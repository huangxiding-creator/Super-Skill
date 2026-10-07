#!/usr/bin/env python3
"""Run every Super-Skill check and exit non-zero on any failure (CI gate).

1. engine + hooks + installer tests      (engine/tests)
2. evolver tests                         (evolver/tests)
3. every sub-skill script test suite     (skills/*/scripts/test_*.py, run in its own dir)
4. offline benchmark                     (evals/bench_offline.py, must score 100 %)
5. structural validation                 (frontmatter of every SKILL.md + agent, hooks.json,
                                          phases.json check types, SKILL.md < 500 lines + footnote)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PY = sys.executable
KNOWN_CHECKS = {"file_exists", "min_bytes", "glob_count", "no_marker", "json_field", "regex_count",
                "regex_number", "approval", "state_field", "git_repo", "command", "req_ids", "ears",
                "trace", "taskgraph_valid", "tasks_done", "loop_guard_closed"}
HOOK_EVENTS = {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
               "PreCompact", "PostCompact", "Stop", "SubagentStop", "SubagentStart", "SessionEnd",
               "Notification", "PermissionRequest"}


def _pytest(args: list[str], cwd: Path) -> bool:
    return subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=str(cwd)).returncode == 0


def _frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    try:
        import yaml  # optional: stricter check when PyYAML is installed
        data = yaml.safe_load(m.group(1))
        return data if isinstance(data, dict) else None
    except ImportError:
        out = {}
        for line in m.group(1).splitlines():
            key, sep, val = line.partition(":")
            if sep and not line.startswith(" "):
                val = val.strip()
                if ": " in val and not val.startswith(('"', "'")):
                    return None  # unquoted ": " breaks real YAML parsers
                out[key.strip()] = val.strip("\"'")
        return out
    except Exception:
        return None


def validate() -> list[str]:
    errors = []
    for md in sorted(SKILL.rglob("SKILL.md")):
        if "results" in md.parts:
            continue
        fm = _frontmatter(md)
        rel = md.relative_to(SKILL)
        if fm is None:
            errors.append(f"{rel}: frontmatter missing or not valid YAML")
            continue
        if not fm.get("name") or not fm.get("description"):
            errors.append(f"{rel}: name/description required")
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", str(fm["name"])):
            errors.append(f"{rel}: bad name {fm['name']!r}")
        elif len(str(fm["description"])) > 1024:
            errors.append(f"{rel}: description > 1024 chars")
        if md.read_text(encoding="utf-8").count("\n") + 1 >= 500:
            errors.append(f"{rel}: >= 500 lines")
    main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"Super-Skill (V\d+(?:\.\d+)*):", main):
        errors.append("SKILL.md: version footnote 'Super-Skill Vx.y.z:' missing (weekly automation needs it)")
    for agent in sorted((SKILL / "agents").glob("*.md")):
        fm = _frontmatter(agent)
        if not fm or not fm.get("name") or not fm.get("description"):
            errors.append(f"agents/{agent.name}: invalid frontmatter")
    phases = json.loads((SKILL / "phases.json").read_text(encoding="utf-8"))
    for p in phases["phases"]:
        for c in p.get("gate", []):
            if c.get("type") not in KNOWN_CHECKS:
                errors.append(f"phases.json {p['id']}: unknown check {c.get('type')}")
    hooks = json.loads((SKILL / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    for event, groups in hooks.items():
        if event not in HOOK_EVENTS:
            errors.append(f"hooks.json: unknown event {event}")
        for g in groups:
            if not isinstance(g.get("hooks"), list) or ("matcher" in g and not isinstance(g["matcher"], str)):
                errors.append(f"hooks.json {event}: malformed group")
            for h in g.get("hooks", []):
                script = re.search(r"hooks/(\w+\.py)", h.get("command", ""))
                if not script or not (SKILL / "hooks" / script.group(1)).is_file():
                    errors.append(f"hooks.json {event}: missing script in {h.get('command')}")
    return errors


def main() -> int:
    results = {}
    results["engine+hooks+installer"] = _pytest(["engine/tests"], SKILL)
    results["evolver"] = _pytest(["tests"], SKILL / "evolver")
    for test in sorted(SKILL.glob("skills/*/scripts/test_*.py")):
        results[f"sub-skill {test.parent.parent.name}/{test.name}"] = _pytest([test.name], test.parent)
    bench = subprocess.run([PY, str(SKILL / "evals" / "bench_offline.py"), "--min-score", "1.0", "--pretty"],
                           cwd=str(SKILL))
    results["offline bench (100%)"] = bench.returncode == 0
    errs = validate()
    for e in errs:
        print(f"  ✗ {e}")
    results["structure validation"] = not errs
    print("\n=== summary ===")
    for name, ok in results.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failed = [n for n, ok in results.items() if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} groups passed")
    return 1 if failed else 0


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
