#!/usr/bin/env python3
"""ss.py — the Super-Skill V5 engine CLI (single entry point).

    ss.py init [--project NAME] [--from P0|IF1] [--test-cmd CMD] [--budget-usd N]
    ss.py status [--json]         ss.py next           ss.py brief
    ss.py gate [PHASE] [--static] ss.py advance        ss.py goto PHASE
    ss.py approve NAME [--note]   ss.py reject NAME --note TEXT
    ss.py wait "REASON"           ss.py resume         ss.py pause
    ss.py config KEY VALUE        ss.py log "MESSAGE"  ss.py handoff
    ss.py task|trace|loop|cost|mem|playbook|route|ralph|evolve  ...   (sub-tools)

``approve``/``reject`` are human decisions: the PreToolUse guard asks the
user to confirm whenever the model tries to run them.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE))
from ss_common import (  # noqa: E402
    SKILL_DIR, find_root, force_utf8_stdio, ledger, load_phases, load_state, phase_order,
    state_path,
)
import state_machine as sm  # noqa: E402

PASSTHROUGH = {
    "task": "taskgraph", "trace": "trace_matrix", "loop": "loop_guard",
    "cost": "cost_meter", "mem": "memindex", "playbook": "playbook",
    "route": "skill_router", "ralph": "ralph",
}


def _root(arg: str | None) -> Path:
    if arg:
        return Path(arg).resolve()
    return find_root() or Path.cwd().resolve()


def _require_state(root: Path) -> dict:
    st = load_state(root)
    if not st:
        print(f"not a Super-Skill project: {root} (run `ss.py init`)", file=sys.stderr)
        raise SystemExit(2)
    return st


def _parse_value(raw: str):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def cmd_status(root: Path, as_json: bool) -> int:
    st = _require_state(root)
    if as_json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0
    phases = load_phases()
    marks = {"done": "✅", "in_progress": "▶", "pending": "·", "skipped": "–", "stale": "⚠"}
    print(f"{st['project']} · status {st['status']} · active {st['active_phase']}")
    for p in phases["phases"]:
        s = st["phases"].get(p["id"], {}).get("status", "?")
        print(f"  {marks.get(s, '?')} {p['id']:<4} {p['name']:<28} {s}")
    print(f"next: {st.get('next_action')}")
    return 0


def main(argv=None) -> int:
    force_utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in PASSTHROUGH:
        mod = importlib.import_module(PASSTHROUGH[argv[0]])
        return int(mod.main(argv[1:]) or 0)
    if argv and argv[0] == "evolve":
        sys.path.insert(0, str(SKILL_DIR / "evolver"))
        mod = importlib.import_module("evolve")
        return int(mod.main(argv[1:]) or 0)

    ap = argparse.ArgumentParser(prog="ss.py", description="Super-Skill V5 engine")
    ap.add_argument("--root", help="project root (default: nearest .super-skill/ or cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="start a Super-Skill run in this project")
    i.add_argument("--project")
    i.add_argument("--from", dest="start", default="P0", help="first phase (IF1 for raw ideas)")
    i.add_argument("--test-cmd", default="")
    i.add_argument("--budget-usd", type=float)
    i.add_argument("--force", action="store_true")
    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    sub.add_parser("next")
    sub.add_parser("brief")
    g = sub.add_parser("gate")
    g.add_argument("phase", nargs="?")
    g.add_argument("--static", action="store_true")
    g.add_argument("--json", action="store_true")
    sub.add_parser("advance")
    go = sub.add_parser("goto")
    go.add_argument("phase")
    a = sub.add_parser("approve")
    a.add_argument("name")
    a.add_argument("--note", default="")
    r = sub.add_parser("reject")
    r.add_argument("name")
    r.add_argument("--note", required=True)
    w = sub.add_parser("wait")
    w.add_argument("reason")
    sub.add_parser("resume")
    sub.add_parser("pause")
    c = sub.add_parser("config")
    c.add_argument("key")
    c.add_argument("value")
    lg = sub.add_parser("log")
    lg.add_argument("message")
    sub.add_parser("handoff")
    sub.add_parser("phases")
    args = ap.parse_args(argv)
    root = _root(args.root)

    if args.cmd == "init":
        st = sm.init(root, args.project, args.start, args.test_cmd, args.budget_usd, args.force)
        print(f"initialized {state_path(root)} — active phase {st['active_phase']}")
        print(f"next: {st['next_action']}")
        return 0
    if args.cmd == "phases":
        for p in load_phases()["phases"]:
            flags = " ".join(f for f in ("autonomous" if p.get("autonomous") else "",
                                         f"approval={p['approval']}" if p.get("approval") else "") if f)
            print(f"{p['id']:<4} {p['name']:<28} skill={p.get('skill')} {flags}")
        return 0
    if args.cmd == "status":
        return cmd_status(root, args.json)
    st = _require_state(root)
    if args.cmd == "next":
        print(st.get("next_action") or sm.next_action(st))
    elif args.cmd == "brief":
        import brief
        print(brief.build_brief(root, source="manual"))
    elif args.cmd == "gate":
        import gate_check
        pid = args.phase or st.get("active_phase")
        res = gate_check.run(root, pid, static=args.static, record=not args.static)
        print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else gate_check.render(res))
        return 0 if res["passed"] else 1
    elif args.cmd == "advance":
        import gate_check
        res = sm.advance(root)
        if res.get("gate"):
            print(gate_check.render(res["gate"]))
        if res["ok"]:
            print(f"advanced {res.get('from')} -> {res.get('to') or 'DONE'} (status {res.get('status')})")
            print(f"next: {load_state(root).get('next_action')}")
            return 0
        print(f"cannot advance: status {res.get('status')}")
        print(f"next: {load_state(root).get('next_action')}")
        return 1
    elif args.cmd == "goto":
        if args.phase not in phase_order(load_phases()):
            print(f"unknown phase {args.phase}", file=sys.stderr)
            return 2
        sm.goto(root, args.phase)
        print(f"active phase -> {args.phase}; later completed phases marked stale")
    elif args.cmd == "approve":
        sm.approve(root, args.name, args.note, True)
        print(f"approval '{args.name}' recorded")
    elif args.cmd == "reject":
        sm.approve(root, args.name, args.note, False)
        print(f"rejection of '{args.name}' recorded: {args.note}")
    elif args.cmd == "wait":
        sm.wait(root, args.reason)
        print(f"waiting for user: {args.reason}")
    elif args.cmd == "resume":
        st = sm.resume(root)
        print(f"resumed — next: {st['next_action']}")
    elif args.cmd == "pause":
        sm.pause(root)
        print("paused (Stop gate released)")
    elif args.cmd == "config":
        sm.set_config(root, args.key, _parse_value(args.value))
        print(f"{args.key} = {args.value}")
    elif args.cmd == "log":
        ledger(root, "note", msg=args.message)
        print("logged")
    elif args.cmd == "handoff":
        import brief
        print(f"wrote {brief.write_handoff(root, 'manual')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
