#!/usr/bin/env python3
"""Offline benchmark for the Super-Skill V5 engine (W6).

Deterministic, model-free, seconds to run. Each scenario builds a synthetic
project in a temp dir and checks that the engine makes the *right* decision
(gate pass/fail, guard allow/deny, breaker trip, stuck detection, Ralph
keep/discard). Output is evolver-compatible JSON::

    {"tasks": {"S01_...": 1.0, ...}, "tokens": 0, "feedback": {...}, "score": 0.97}

Usage: ``python bench_offline.py [--only S03,S07] [--skill-dir DIR] [--pretty]``.
``--skill-dir`` lets the evolver score a mutated copy of the skill.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REQS_OK = """# Requirements
- REQ-001 [MUST]: When a user adds a todo, the system shall persist it.
  - REQ-001.AC1: the todo is listed after reload
- REQ-002 [MUST]: 当用户离线时，系统应缓存草稿
"""
DANGEROUS = ["rm -rf ~", "rm -rf /", "rm -fr *", "git push --force origin x", "git push -f",
             "cat .env", "mkfs.ext4 /dev/sda1", "echo {} > .super-skill/state.json",
             "type config.secret.ini", "sudo rm -r -f $HOME"]
BENIGN = ["rm -rf build/", "rm -rf node_modules", "git push origin feat/x", "pytest -q",
          "cat README.md", "cat .env.example", "npm test", "git status", "ls -la",
          "git push --force-with-lease origin feat/x"]


def _load(skill: Path):
    sys.path.insert(0, str(skill / "engine"))
    import importlib
    mods = {}
    for name in ("state_machine", "gate_check", "taskgraph", "trace_matrix", "loop_guard", "ralph"):
        mods[name] = importlib.import_module(name)
    return mods


def _hook(skill: Path, name: str, payload: dict) -> dict | None:
    p = subprocess.run([sys.executable, str(skill / "hooks" / name)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return json.loads(p.stdout) if p.stdout.strip() else None


def _write(root: Path, name: str, text: str) -> None:
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text, encoding="utf-8")


def scenarios(m: dict, skill: Path):
    sm, gc, tg, tm, lg = m["state_machine"], m["gate_check"], m["taskgraph"], m["trace_matrix"], m["loop_guard"]

    def s01(d):
        sm.init(d, "b", "P0")
        return not gc.run(d, "P0")["passed"], "fresh P0 must fail its gate"

    def s02(d):
        sm.init(d, "b", "P0")
        _write(d, "VISION.md", "# Vision\n" + "v" * 400)
        _write(d, "AI_NATIVE_OPTIONS.md", "options")
        ok0 = gc.run(d, "P0")["passed"]
        r = sm.advance(d)
        return ok0 and r["ok"] and r["to"] == "P1", "complete P0 artifacts must pass and advance"

    def s03(d):
        sm.init(d, "b", "P4")
        _write(d, "REQUIREMENTS.md", REQS_OK)
        r = gc.run(d, "P4")
        fails = [c["type"] for c in r["checks"] if c["ok"] is False]
        return fails == ["approval"], f"P4 must fail only on approval, got {fails}"

    def s04(d):
        sm.init(d, "b", "P4")
        _write(d, "REQUIREMENTS.md", "- REQ-001: fast and pretty UI\n")
        r = gc.run(d, "P4")
        return any(c["type"] == "ears" and c["ok"] is False for c in r["checks"]), "non-EARS requirement must fail"

    def s05(d):
        sm.init(d, "b", "P6")
        _write(d, "WBS.md", "# WBS")
        _write(d, "REQUIREMENTS.md", REQS_OK)
        tg.add(d, "a", task_id="T-001", after="T-002", covers="REQ-001")
        tg.add(d, "b", task_id="T-002", after="T-001", covers="REQ-002")
        r = gc.run(d, "P6")
        return any(c["type"] == "taskgraph_valid" and c["ok"] is False for c in r["checks"]), "cycle must fail"

    def s06(d):
        sm.init(d, "b", "P6")
        _write(d, "WBS.md", "# WBS")
        _write(d, "REQUIREMENTS.md", REQS_OK)
        tg.add(d, "a", covers="REQ-001")
        tg.add(d, "orphan", covers="REQ-777")
        r = gc.run(d, "P6")
        return not r["passed"], "orphan task / uncovered REQ-002 must fail"

    def s07(d):
        sm.init(d, "b", "P6")
        _write(d, "WBS.md", "# WBS")
        _write(d, "REQUIREMENTS.md", REQS_OK)
        tg.add(d, "a", covers="REQ-001.AC1", verify="pytest")
        tg.add(d, "b", covers="REQ-002", after="T-001", verify="pytest")
        return gc.run(d, "P6")["passed"], "complete, acyclic, covering task graph must pass"

    def s08(d):
        sm.init(d, "b", "P6")
        _write(d, "REQUIREMENTS.md", REQS_OK)
        tg.add(d, "a", covers="REQ-001")
        tg.add(d, "b", covers="REQ-002")
        miss = not tm.build(d, require="tests")["ok"]
        _write(d, "tests/test_x.py", "def test_req_001_ac1(): pass\ndef test_req_002(): pass\n")
        return miss and tm.build(d, require="tests")["ok"], "test coverage must flip fail -> pass"

    def s09(d):
        sm.init(d, "b", "P5")
        a = _hook(skill, "stop_gate.py", {"hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(d)})
        b = _hook(skill, "stop_gate.py", {"hook_event_name": "Stop", "stop_hook_active": True, "cwd": str(d)})
        sm.goto(d, "P4")
        c = _hook(skill, "stop_gate.py", {"hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(d)})
        ok = bool(a and a.get("decision") == "block") and bool(b and "decision" not in b) and c is None
        return ok, "stop gate: block unfinished autonomous phase, release when stalled, never block human phase"

    def s10(d):
        sm.init(d, "b", "P8")
        wrong = []
        for cmd in DANGEROUS:
            out = _hook(skill, "pre_tool.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                               "tool_input": {"command": cmd}, "cwd": str(d)})
            if not out or out["hookSpecificOutput"]["permissionDecision"] != "deny":
                wrong.append(f"missed: {cmd}")
        for cmd in BENIGN:
            out = _hook(skill, "pre_tool.py", {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                               "tool_input": {"command": cmd}, "cwd": str(d)})
            if out:
                wrong.append(f"false positive: {cmd}")
        return not wrong, "; ".join(wrong) or "guard precision/recall 100%"

    def s11(d):
        sm.init(d, "b", "P8")
        states = [lg.record(d, progress=False)["state"] for _ in range(3)]
        return states == ["CLOSED", "CLOSED", "OPEN"], f"breaker must trip on 3rd no-progress, got {states}"

    def s12(d):
        rep = [{"ev": "PostToolUse", "tool": "Bash", "summary": "pytest", "out_hash": "h", "ok": False}] * 4
        healthy = [{"ev": "PostToolUse", "tool": "Edit", "summary": f"f{i}", "out_hash": str(i), "ok": True}
                   for i in range(12)]
        return bool(lg.detect_stuck(rep)) and not lg.detect_stuck(healthy), "stuck detector recall and precision"

    def s13(d):
        sm.init(d, "b", "P8")
        py = sys.executable
        _write(d, "agent.py", "import pathlib,sys\np=sys.stdin.read()\n"
               "print('EXIT_SIGNAL: true') if 'EXIT_SIGNAL' in p else pathlib.Path('done.txt').write_text('1')\n")
        tg.add(d, "make file", verify=f'"{py}" -c "import os,sys; sys.exit(0 if os.path.exists(\'done.txt\') else 1)"')
        res = m["ralph"].run(d, agent_cmd=f'"{py}" agent.py', max_iterations=4, commit=False)
        return res["exit"] == "all_done+exit_signal" and res["kept"] == 1, f"ralph end-to-end: {res}"

    return {"S01_fresh_p0_fails": s01, "S02_complete_p0_advances": s02, "S03_approval_gate": s03,
            "S04_ears_lint": s04, "S05_task_cycle": s05, "S06_orphan_and_uncovered": s06,
            "S07_valid_task_graph": s07, "S08_test_traceability": s08, "S09_stop_gate": s09,
            "S10_guard_precision_recall": s10, "S11_breaker_trip": s11, "S12_stuck_detector": s12,
            "S13_ralph_end_to_end": s13}


def run(skill: Path = SKILL, only: list[str] | None = None) -> dict:
    mods = _load(skill)
    tasks, feedback = {}, {}
    t0 = time.time()
    for name, fn in scenarios(mods, skill).items():
        if only and not any(name.startswith(o) for o in only):
            continue
        with tempfile.TemporaryDirectory() as tmp:
            try:
                ok, msg = fn(Path(tmp))
            except Exception as exc:  # a crash is a failed scenario, not a crashed bench
                ok, msg = False, f"crash: {exc.__class__.__name__}: {exc}"
        tasks[name] = 1.0 if ok else 0.0
        if not ok:
            feedback[name] = msg
    score = sum(tasks.values()) / len(tasks) if tasks else 0.0
    return {"tasks": tasks, "tokens": 0, "feedback": feedback, "score": round(score, 4),
            "seconds": round(time.time() - t0, 2)}


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Super-Skill offline benchmark")
    ap.add_argument("--only", default="", help="comma-separated scenario prefixes")
    ap.add_argument("--skill-dir", default=str(SKILL))
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--min-score", type=float, default=None, help="exit 1 below this score")
    args = ap.parse_args(argv)
    res = run(Path(args.skill_dir).resolve(), [o for o in args.only.split(",") if o])
    if args.pretty:
        for name, val in res["tasks"].items():
            print(f"{'✅' if val else '❌'} {name}" + (f" — {res['feedback'][name]}" if name in res["feedback"] else ""))
        print(f"score {res['score']:.2%} in {res['seconds']}s")
    else:
        print(json.dumps(res, ensure_ascii=False))
    if args.min_score is not None and res["score"] < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
