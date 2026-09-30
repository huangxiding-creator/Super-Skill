#!/usr/bin/env python3
"""Super-Skill V5 installer / doctor — portable across Windows, macOS, Linux.

    python install.py --global            copy skill + subagents to ~/.claude
    python install.py --global --hooks    ... and register hooks in ~/.claude/settings.json
    python install.py --hooks             (re)register hooks for an already-installed copy
    python install.py --project DIR       register hooks in DIR/.claude/settings.json
    python install.py --uninstall-hooks [--project DIR]
    python install.py --doctor            verify everything on THIS machine

Portability rules this file enforces:
- hook commands are generated on the target machine with the absolute path of
  the Python that ran the installer (no hard-coded paths anywhere in the repo);
  a project whose own tree contains the skill gets ``$CLAUDE_PROJECT_DIR``-
  relative commands instead, so a committed settings file works everywhere;
- only long-standing hook events are registered; newer events are added only
  when the local Claude Code version is known to support them, so an older
  Claude Code never rejects the whole settings file;
- on Windows without Git Bash (hooks then run in PowerShell) the exec form
  (``command`` + ``args``) is used instead of a quoted shell string;
- settings are merged, never replaced, and backed up first.
Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILL_SRC = Path(__file__).resolve().parent
HOME = Path.home()
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HOME / ".claude")
GLOBAL_SKILL = CLAUDE_DIR / "skills" / "super-skill"
BACKUP_DIR = CLAUDE_DIR / "backups"
MARKER = "super-skill/hooks/"
MIN_PY = (3, 9)
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "results",
                                     "*.bak-*", ".DS_Store")

# (event, matcher or None, script, timeout seconds, min Claude Code version or None)
HOOKS = [
    ("SessionStart", "startup|resume|clear|compact", "session_start.py", 30, None),
    ("UserPromptSubmit", None, "user_prompt.py", 10, None),
    ("PreToolUse", "Bash|PowerShell|Read|Edit|Write|MultiEdit|NotebookEdit", "pre_tool.py", 15, None),
    ("PostToolUse", "", "post_tool.py", 15, None),
    ("PostToolUseFailure", "", "post_tool.py", 15, (2, 1, 0)),
    ("PreCompact", "manual|auto", "pre_compact.py", 30, None),
    ("Stop", None, "stop_gate.py", 30, None),
    ("SubagentStop", None, "log_event.py", 10, None),
    ("SessionEnd", None, "log_event.py", 5, None),
]
REQUIRED_FILES = ["SKILL.md", "phases.json", "engine/ss.py", "engine/ss_common.py",
                  "engine/state_machine.py", "engine/gate_check.py", "engine/taskgraph.py",
                  "engine/trace_matrix.py", "engine/loop_guard.py", "engine/brief.py",
                  "hooks/_hooklib.py", "hooks/session_start.py", "hooks/pre_tool.py",
                  "hooks/post_tool.py", "hooks/stop_gate.py"]


def _say(icon: str, msg: str) -> None:
    try:
        print(f"{icon} {msg}")
    except UnicodeEncodeError:
        print(f"{icon.encode('ascii', 'replace').decode()} {msg.encode('ascii', 'replace').decode()}")


# ---------------------------------------------------------------- environment

def claude_version() -> tuple[int, ...] | None:
    exe = shutil.which("claude")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out or "")
    return tuple(int(x) for x in m.groups()) if m else None


def windows_git_bash() -> str | None:
    """Claude Code runs hook commands through Git Bash on Windows when present."""
    env = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if env and Path(env).exists():
        return env
    candidates = [Path(os.environ.get(v, "")) / "Git" / "bin" / "bash.exe"
                  for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA") if os.environ.get(v)]
    git = shutil.which("git")
    if git:
        candidates.append(Path(git).resolve().parent.parent / "bin" / "bash.exe")
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def python_exe() -> str:
    return Path(sys.executable).resolve().as_posix()


# ---------------------------------------------------------------- hook specs

def hook_entries(hooks_dir: Path, version: tuple | None, use_exec: bool,
                 project_rel: str | None = None) -> dict:
    """Build the ``hooks`` mapping. ``project_rel`` → portable $CLAUDE_PROJECT_DIR form."""
    py = python_exe()
    spec: dict[str, list] = {}
    for event, matcher, script, timeout, min_ver in HOOKS:
        if min_ver and (version is None or version < min_ver):
            continue
        if project_rel is not None:
            target = f"${{CLAUDE_PROJECT_DIR}}/{project_rel}/{script}"
            handler = {"type": "command", "timeout": timeout,
                       "command": f'python3 "{target}" 2>/dev/null || python "{target}"'}
        elif use_exec:
            handler = {"type": "command", "command": py,
                       "args": [(hooks_dir / script).as_posix()], "timeout": timeout}
        else:
            handler = {"type": "command", "command": f'"{py}" "{(hooks_dir / script).as_posix()}"',
                       "timeout": timeout}
        group = {"hooks": [handler]}
        if matcher is not None:
            group = {"matcher": matcher, **group}
        spec.setdefault(event, []).append(group)
    return spec


def _is_ours(group: dict) -> bool:
    for h in group.get("hooks", []) if isinstance(group, dict) else []:
        text = " ".join([str(h.get("command", ""))] + [str(a) for a in h.get("args", [])])
        if MARKER in text.replace("\\", "/"):
            return True
    return False


def merge_hooks(settings: dict, spec: dict) -> dict:
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
    for event in list(hooks):
        groups = hooks[event] if isinstance(hooks[event], list) else []
        kept = [g for g in groups if not _is_ours(g)]
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    for event, groups in spec.items():
        hooks.setdefault(event, []).extend(groups)
    if hooks:
        settings["hooks"] = hooks
    else:
        settings.pop("hooks", None)
    return settings


def remove_hooks(settings: dict) -> dict:
    return merge_hooks(settings, {})


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8-sig")
    if not raw.strip():
        return {}
    data = json.loads(raw)  # refuse to touch an unparseable file
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def _write_settings(path: Path, data: dict) -> Path | None:
    backup = None
    if path.exists():
        backup = path.with_name(f"{path.name}.bak-superskill-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-superskill")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return backup


def register_hooks(settings_path: Path, hooks_dir: Path, project_root: Path | None = None) -> dict:
    version = claude_version()
    use_exec = platform.system() == "Windows" and windows_git_bash() is None
    rel = None
    if project_root is not None:
        try:
            rel = hooks_dir.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            rel = None  # skill lives outside the project: absolute form
    spec = hook_entries(hooks_dir, version, use_exec and rel is None, rel)
    data = merge_hooks(_load_settings(settings_path), spec)
    backup = _write_settings(settings_path, data)
    form = "portable" if rel is not None else ("exec" if use_exec else "shell")
    return {"settings": str(settings_path), "backup": str(backup) if backup else None,
            "events": sorted(spec), "form": form,
            "claude_version": ".".join(map(str, version)) if version else None}


# ---------------------------------------------------------------- install

def install_global(src: Path = SKILL_SRC, dest: Path = GLOBAL_SKILL) -> dict:
    src = src.resolve()
    result = {"skill": str(dest), "copied": False, "agents": [], "backup": None}
    if not dest.exists() or src != dest.resolve():
        if dest.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup = BACKUP_DIR / f"super-skill-{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.move(str(dest), str(backup))
            for old in sorted(BACKUP_DIR.glob("super-skill-*"))[:-2]:  # keep 2 newest
                shutil.rmtree(old, ignore_errors=True)
            result["backup"] = str(backup)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, ignore=COPY_IGNORE)
        result["copied"] = True
    agents_src = dest / "agents"
    if agents_src.is_dir():
        agents_dst = CLAUDE_DIR / "agents"
        agents_dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(agents_src.glob("ss-*.md")):
            shutil.copy2(f, agents_dst / f.name)
            result["agents"].append(f.name)
    return result


# ---------------------------------------------------------------- doctor

def _run(args: list, payload: str | None = None, env: dict | None = None):
    return subprocess.run(args, input=payload, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env, timeout=120)


def doctor(skill_dir: Path, settings_path: Path) -> int:
    fails = 0

    def check(ok: bool, msg: str, warn: bool = False):
        nonlocal fails
        if ok:
            _say("✅", msg)
        elif warn:
            _say("⚠️ ", msg)
        else:
            _say("❌", msg)
            fails += 1

    check(sys.version_info >= MIN_PY, f"Python {platform.python_version()} ({python_exe()})")
    missing = [f for f in REQUIRED_FILES if not (skill_dir / f).is_file()]
    check(not missing, f"skill files in {skill_dir}" + (f" — missing: {', '.join(missing)}" if missing else ""))
    sys.path.insert(0, str(skill_dir / "engine"))
    bad = []
    for mod in ("ss_common", "state_machine", "gate_check", "taskgraph", "trace_matrix",
                "loop_guard", "brief", "cost_meter", "playbook", "memindex", "skill_router", "ralph"):
        try:
            __import__(mod)
        except Exception as exc:  # noqa: BLE001 - report any import problem
            bad.append(f"{mod} ({exc.__class__.__name__}: {exc})")
    check(not bad, "engine modules import" + (f" — {'; '.join(bad)}" if bad else ""))
    try:
        import sqlite3
        con = sqlite3.connect(":memory:")
        con.execute("create virtual table t using fts5(x, tokenize='trigram')")
        check(True, f"sqlite {sqlite3.sqlite_version} with FTS5 trigram (Chinese search)")
    except Exception:
        check(False, "SQLite FTS5 trigram unavailable — memindex falls back to slower LIKE search", warn=True)
    ver = claude_version()
    check(ver is not None, f"Claude Code CLI {'.'.join(map(str, ver)) if ver else 'not found on PATH'}", warn=True)
    check(shutil.which("git") is not None, "git on PATH", warn=True)
    if platform.system() == "Windows":
        gb = windows_git_bash()
        check(True, f"Windows hook shell: {'Git Bash ' + gb if gb else 'PowerShell (exec-form hooks)'}")
    try:
        data = _load_settings(settings_path)
    except Exception as exc:  # noqa: BLE001
        check(False, f"{settings_path} unreadable: {exc}")
        data = {}
    ours = {}
    for ev, groups in (data.get("hooks") or {}).items():
        mine = [g for g in groups if _is_ours(g)] if isinstance(groups, list) else []
        if mine:
            ours[ev] = mine
    check(bool(ours), f"hooks registered in {settings_path}: {', '.join(sorted(ours)) or 'none'}", warn=True)
    for ev, groups in ours.items():
        for g in groups:
            for h in g.get("hooks", []):
                cmd = str(h.get("command", ""))
                paths = list(h.get("args", [])) if h.get("args") else re.findall(r'"([^"$]+)"', cmd)
                if h.get("args"):
                    paths.append(cmd)
                for p in paths:
                    if ("/" in p or "\\" in p) and not Path(p).exists():
                        check(False, f"{ev}: hook path does not exist: {p}")
    with tempfile.TemporaryDirectory() as tmp:
        env = {k: v for k, v in os.environ.items() if k != "SUPER_SKILL_PROJECT"}
        py = sys.executable
        r = _run([py, str(skill_dir / "engine" / "ss.py"), "--root", tmp, "init", "--project", "doctor"], env=env)
        check(r.returncode == 0, "engine: ss.py init in a temp project" + ("" if r.returncode == 0 else f" — {r.stderr[-200:]}"))
        r = _run([py, str(skill_dir / "hooks" / "stop_gate.py")],
                 json.dumps({"hook_event_name": "Stop", "stop_hook_active": False, "cwd": tmp}), env)
        check('"decision": "block"' in r.stdout, "hooks: Stop gate blocks an unfinished autonomous phase")
        r = _run([py, str(skill_dir / "hooks" / "pre_tool.py")],
                 json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                             "tool_input": {"command": "rm -rf ~"}, "cwd": tmp}), env)
        check('"deny"' in r.stdout, "hooks: PreToolUse guard denies a destructive command")
        r = _run([py, str(skill_dir / "hooks" / "session_start.py")],
                 json.dumps({"hook_event_name": "SessionStart", "source": "startup", "cwd": tmp}), env)
        check('"additionalContext"' in r.stdout, "hooks: SessionStart injects the run brief")
    outside = tempfile.mkdtemp()
    try:
        r = _run([py, str(skill_dir / "hooks" / "stop_gate.py")],
                 json.dumps({"hook_event_name": "Stop", "cwd": outside}), env)
        check(r.returncode == 0 and not r.stdout.strip(), "hooks: no-op outside Super-Skill projects")
    finally:
        shutil.rmtree(outside, ignore_errors=True)
    _say("🩺", "doctor: all good" if not fails else f"doctor: {fails} problem(s)")
    return 1 if fails else 0


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Install / verify Super-Skill V5")
    ap.add_argument("--global", dest="global_", action="store_true", help="copy to ~/.claude/skills/super-skill")
    ap.add_argument("--hooks", action="store_true", help="register hooks (global unless --project)")
    ap.add_argument("--project", help="register hooks in PROJECT/.claude/settings.json instead")
    ap.add_argument("--uninstall-hooks", action="store_true")
    ap.add_argument("--doctor", action="store_true")
    args = ap.parse_args(argv)
    if sys.version_info < MIN_PY:
        _say("❌", f"Python {MIN_PY[0]}.{MIN_PY[1]}+ required, found {platform.python_version()}")
        return 2
    if not any((args.global_, args.hooks, args.project, args.uninstall_hooks, args.doctor)):
        ap.print_help()
        return 0
    project = Path(args.project).resolve() if args.project else None
    settings_path = (project / ".claude" / "settings.json") if project else CLAUDE_DIR / "settings.json"
    skill_dir = SKILL_SRC if project or not (args.global_ or GLOBAL_SKILL.exists()) else GLOBAL_SKILL
    if args.global_:
        res = install_global()
        skill_dir = GLOBAL_SKILL
        _say("📦", f"skill → {res['skill']}" + (" (copied)" if res["copied"] else " (already in place)"))
        if res.get("backup"):
            _say("🗂", f"previous version kept at {res['backup']}")
        if res["agents"]:
            _say("🤖", f"subagents → {CLAUDE_DIR / 'agents'}: {', '.join(res['agents'])}")
    if args.uninstall_hooks:
        data = remove_hooks(_load_settings(settings_path))
        backup = _write_settings(settings_path, data)
        _say("🧹", f"removed Super-Skill hooks from {settings_path} (backup {backup})")
        return 0
    if args.hooks or project:
        res = register_hooks(settings_path, skill_dir / "hooks", project)
        _say("🪝", f"hooks ({res['form']} form) → {res['settings']}: {', '.join(res['events'])}")
        if res["backup"]:
            _say("🗂", f"settings backup: {res['backup']}")
        if not res["claude_version"]:
            _say("⚠️ ", "Claude Code CLI not found; registered only long-standing hook events")
    if args.doctor or args.global_ or args.hooks:
        return doctor(skill_dir, settings_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
