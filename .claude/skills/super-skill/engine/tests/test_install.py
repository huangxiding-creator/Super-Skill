"""Installer tests, including a full "fresh machine" simulation: HOME and
CLAUDE_CONFIG_DIR point at an empty temp dir, the installer copies the skill,
merges hooks into a pre-existing settings file, and ``--doctor`` must pass."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL))
import install  # noqa: E402

USER_SETTINGS = {
    "language": "简体中文",
    "permissions": {"allow": ["Bash(git *)"]},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}]},
}


def test_hook_entries_forms():
    hd = Path("/opt/x/super-skill/hooks")
    shell = install.hook_entries(hd, (2, 1, 285), use_exec=False)
    assert set(shell) >= {"SessionStart", "PreToolUse", "PostToolUse", "Stop", "PreCompact", "PostToolUseFailure"}
    cmd = shell["Stop"][0]["hooks"][0]["command"]
    assert cmd.startswith('"') and "super-skill/hooks/stop_gate.py" in cmd
    assert "matcher" not in shell["Stop"][0] and shell["SessionStart"][0]["matcher"].startswith("startup")
    execf = install.hook_entries(hd, (2, 1, 285), use_exec=True)
    h = execf["Stop"][0]["hooks"][0]
    assert h["args"][0].endswith("super-skill/hooks/stop_gate.py") and '"' not in h["command"]
    old = install.hook_entries(hd, None, use_exec=False)
    assert "PostToolUseFailure" not in old, "newer events need a known-new Claude Code"
    port = install.hook_entries(hd, (2, 1, 285), False, project_rel=".claude/skills/super-skill/hooks")
    assert "${CLAUDE_PROJECT_DIR}/.claude/skills/super-skill/hooks/stop_gate.py" in port["Stop"][0]["hooks"][0]["command"]


def test_merge_preserves_user_hooks_and_is_idempotent():
    spec = install.hook_entries(Path("/h/super-skill/hooks"), (2, 1, 285), False)
    once = install.merge_hooks(json.loads(json.dumps(USER_SETTINGS)), spec)
    twice = install.merge_hooks(json.loads(json.dumps(once)), spec)
    assert once == twice
    pre = twice["hooks"]["PreToolUse"]
    assert pre[0]["hooks"][0]["command"] == "echo mine" and len(pre) == 2
    assert twice["language"] == "简体中文" and twice["permissions"] == USER_SETTINGS["permissions"]
    removed = install.remove_hooks(twice)
    assert removed["hooks"] == USER_SETTINGS["hooks"]


def _env(home: Path, cfg: Path) -> dict:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), CLAUDE_CONFIG_DIR=str(cfg),
               PYTHONDONTWRITEBYTECODE="1")  # so doctor's own imports leave no __pycache__
    env.pop("SUPER_SKILL_PROJECT", None)
    return env


def _py(args, env):
    return subprocess.run([sys.executable, *args], env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)


def test_fresh_machine_global_install(tmp_path):
    home = tmp_path / "home"
    cfg = home / ".claude"
    cfg.mkdir(parents=True)
    (cfg / "settings.json").write_text(json.dumps(USER_SETTINGS, ensure_ascii=False), encoding="utf-8")
    env = _env(home, cfg)
    p = _py([str(SKILL / "install.py"), "--global", "--hooks"], env)
    assert p.returncode == 0, p.stdout + p.stderr
    dest = cfg / "skills" / "super-skill"
    assert (dest / "SKILL.md").is_file() and (dest / "engine" / "ss.py").is_file()
    assert not list(dest.rglob("__pycache__"))
    settings = json.loads((cfg / "settings.json").read_text(encoding="utf-8"))
    assert settings["language"] == "简体中文"
    assert settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "echo mine"
    ours = [g for g in settings["hooks"]["Stop"] if install._is_ours(g)]
    assert ours, settings["hooks"]
    assert dest.as_posix() in json.dumps(ours), "hooks must point at the installed copy, not the repo"
    assert list(cfg.glob("settings.json.bak-superskill-*")), "settings must be backed up"
    assert "doctor: all good" in p.stdout, p.stdout
    # re-running is safe (idempotent) and keeps a backup of the previous copy outside skills/
    p2 = _py([str(SKILL / "install.py"), "--global", "--hooks"], env)
    assert p2.returncode == 0, p2.stdout + p2.stderr
    s2 = json.loads((cfg / "settings.json").read_text(encoding="utf-8"))
    assert len([g for g in s2["hooks"]["Stop"] if install._is_ours(g)]) == 1
    assert list((cfg / "backups").glob("super-skill-*"))
    assert not list((cfg / "skills").glob(".super-skill*")), "backups must not live in skills/"
    # the installed copy can run its own doctor, then uninstall removes only our hooks
    p3 = _py([str(dest / "install.py"), "--doctor"], env)
    assert p3.returncode == 0 and "doctor: all good" in p3.stdout, p3.stdout
    _py([str(dest / "install.py"), "--uninstall-hooks"], env)
    s3 = json.loads((cfg / "settings.json").read_text(encoding="utf-8"))
    assert s3["hooks"] == USER_SETTINGS["hooks"]


def test_repo_contains_no_machine_specific_paths():
    """Executable files must not depend on this machine (docs may cite provenance paths)."""
    bad = []
    for path in SKILL.rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".json", ".sh", ".yaml", ".yml", ".js"}:
            continue
        if any(part in {"__pycache__", "results", ".pytest_cache"} for part in path.parts):
            continue
        if path.name == "test_install.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in ("C:\\Users\\Lenovo", "C:/Users/Lenovo", "E:\\00-", "E:/00-", "E:\\AI-Station"):
            if needle in text:
                bad.append(f"{path.relative_to(SKILL)}: {needle}")
    assert not bad, bad
