#!/usr/bin/env python3
"""Loop safety for autonomous runs (W5): circuit breaker, stuck detection,
pressure ladder and the dual-condition exit gate.

Borrowed patterns:
- frankbria/ralph-claude-code ``lib/circuit_breaker.sh`` (MIT): CLOSED /
  OPEN / HALF_OPEN with no-progress, same-error and permission-denial trips
  plus a cooldown; exit only on completion AND an explicit ``EXIT_SIGNAL``.
- OpenHands stuck detector (MIT): repeated action/observation, repeated
  error, monologue and A-B-A-B alternation over a recent window.
- tanweai/pua (pattern only, no license): escalating pressure levels that
  force a fundamentally different approach instead of retrying.

State: ``<project>/.super-skill/loop_guard.json``.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    force_utf8_stdio, ledger, now_iso, read_json, read_jsonl, sdir, short_hash,
    write_json_atomic,
)

CLOSED, OPEN, HALF_OPEN = "CLOSED", "OPEN", "HALF_OPEN"
DEFAULTS = {"no_progress": 3, "same_error": 5, "perm_denials": 2}
COOLDOWN_S = 1800
EXIT_SIGNAL = re.compile(r"^\s*EXIT_SIGNAL:\s*true\s*$", re.IGNORECASE | re.MULTILINE)

PRESSURE = {
    0: "",
    1: "L1 — second consecutive failure: do NOT retry the same approach. Switch to a "
       "fundamentally different strategy and state why the previous one failed.",
    2: "L2 — third failure: stop guessing. Read the actual source/docs/error output, list 3 "
       "competing hypotheses, and design one experiment that falsifies at least two.",
    3: "L3 — fourth failure: run the 7-point checklist: (1) reproduce minimally (2) read the "
       "full error (3) check assumptions/versions (4) search the codebase for the pattern "
       "(5) search upstream issues/docs (6) simplify or bisect (7) write the finding down.",
    4: "L4 — repeated failure: escalate. Write a BLOCKER note (what was tried, evidence, "
       "what is needed), mark the task blocked, and move to the next ready task.",
}


# ---------------------------------------------------------------- breaker

def _path(root: Path) -> Path:
    return sdir(root) / "loop_guard.json"


def load(root: Path) -> dict:
    st = read_json(_path(root), default=None) or {}
    st.setdefault("state", CLOSED)
    st.setdefault("thresholds", dict(DEFAULTS))
    st.setdefault("cooldown_s", COOLDOWN_S)
    for key in ("no_progress", "same_error", "perm_denials", "consecutive_failures", "iterations"):
        st.setdefault(key, 0)
    st.setdefault("last_error_sig", "")
    st.setdefault("opened_at", None)
    st.setdefault("opened_epoch", None)
    st.setdefault("reason", "")
    return st


def save(root: Path, st: dict) -> None:
    st["updated_at"] = now_iso()
    write_json_atomic(_path(root), st)


def _trip(root: Path, st: dict, reason: str) -> None:
    st.update(state=OPEN, opened_at=now_iso(), opened_epoch=time.time(), reason=reason)
    ledger(root, "breaker", state=OPEN, reason=reason)


def record(root: Path, progress: bool, error: str | None = None,
           permission_denied: bool = False) -> dict:
    """Record one loop iteration and update the breaker."""
    st = load(root)
    th = st["thresholds"]
    st["iterations"] += 1
    was_half_open = st["state"] == HALF_OPEN
    if progress and not error:
        st.update(no_progress=0, same_error=0, consecutive_failures=0, last_error_sig="")
        if was_half_open:
            st.update(state=CLOSED, reason="", opened_at=None, opened_epoch=None)
            ledger(root, "breaker", state=CLOSED, reason="half-open probe succeeded")
        save(root, st)
        return st
    st["consecutive_failures"] += 1
    if not progress:
        st["no_progress"] += 1
    if error:
        sig = short_hash(_normalize_error(error))
        st["same_error"] = st["same_error"] + 1 if sig == st["last_error_sig"] else 1
        st["last_error_sig"] = sig
    if permission_denied:
        st["perm_denials"] += 1
    reason = ""
    if was_half_open:
        reason = "half-open probe failed"
    elif st["no_progress"] >= th["no_progress"]:
        reason = f"{st['no_progress']} iterations without progress"
    elif st["same_error"] >= th["same_error"]:
        reason = f"same error {st['same_error']} times"
    elif st["perm_denials"] >= th["perm_denials"]:
        reason = f"{st['perm_denials']} permission denials"
    if reason and st["state"] != OPEN:
        _trip(root, st, reason)
    save(root, st)
    return st


def _normalize_error(text: str) -> str:
    """Strip volatile bits (numbers, hex, paths) so the same error hashes equal."""
    text = re.sub(r"0x[0-9a-fA-F]+|\b\d+(\.\d+)?\b", "#", text)
    text = re.sub(r"[A-Za-z]:\\[^\s:]+|/[\w./-]+", "<path>", text)
    return " ".join(text.split())[-600:]


def can_proceed(root: Path) -> tuple[bool, str]:
    st = load(root)
    if st["state"] == CLOSED:
        return True, "closed"
    if st["state"] == HALF_OPEN:
        return True, "half-open probe"
    opened = st.get("opened_epoch") or 0
    if time.time() - opened >= st.get("cooldown_s", COOLDOWN_S):
        st["state"] = HALF_OPEN
        save(root, st)
        ledger(root, "breaker", state=HALF_OPEN, reason="cooldown elapsed")
        return True, "cooldown elapsed, half-open probe"
    left = int(st.get("cooldown_s", COOLDOWN_S) - (time.time() - opened))
    return False, f"breaker OPEN ({st['reason']}); cooldown {left}s left"


def reset(root: Path) -> dict:
    st = load(root)
    st.update(state=CLOSED, no_progress=0, same_error=0, perm_denials=0,
              consecutive_failures=0, last_error_sig="", reason="", opened_at=None,
              opened_epoch=None)
    save(root, st)
    ledger(root, "breaker", state=CLOSED, reason="manual reset")
    return st


def pressure(consecutive_failures: int) -> tuple[int, str]:
    level = 0 if consecutive_failures < 2 else min(4, consecutive_failures - 1)
    return level, PRESSURE[level]


def exit_ok(agent_output: str, all_done: bool) -> bool:
    """Dual-condition exit: work verifiably done AND agent explicitly signalled."""
    return bool(all_done and EXIT_SIGNAL.search(agent_output or ""))


# ---------------------------------------------------------------- stuck

def _tool_sig(e: dict) -> str:
    return f"{e.get('tool')}|{e.get('summary', '')[:160]}"


def detect_stuck(events: list[dict], window: int = 20) -> list[dict]:
    """Return stuck patterns found in the most recent ``window`` hook events."""
    recent = events[-window:]
    tools = [e for e in recent if e.get("ev") in ("PostToolUse", "PostToolUseFailure")]
    findings = []
    counts = Counter((_tool_sig(e), e.get("out_hash")) for e in tools)
    for (sig, _), n in counts.items():
        if n >= 4:
            findings.append({"pattern": "repeat_action", "count": n, "detail": sig})
            break
    errors = Counter(e.get("out_hash") for e in tools if e.get("ok") is False and e.get("out_hash"))
    for h, n in errors.items():
        if n >= 3:
            sample = next(_tool_sig(e) for e in tools if e.get("out_hash") == h)
            findings.append({"pattern": "repeat_error", "count": n, "detail": sample})
            break
    sigs = [_tool_sig(e) for e in tools[-6:]]
    if len(sigs) == 6 and len(set(sigs)) == 2 and all(sigs[i] != sigs[i + 1] for i in range(5)):
        findings.append({"pattern": "alternation", "count": 6, "detail": " <-> ".join(sorted(set(sigs)))})
    streak = 0
    for e in reversed(recent):
        if e.get("ev") == "Stop":
            streak += 1
        elif e.get("ev") in ("PostToolUse", "PostToolUseFailure", "UserPromptSubmit"):
            break
    if streak >= 3:
        findings.append({"pattern": "monologue", "count": streak,
                         "detail": "several stops with no tool activity in between"})
    return findings


def stuck_advice(findings: list[dict]) -> str:
    if not findings:
        return ""
    names = ", ".join(f"{f['pattern']}×{f['count']}" for f in findings)
    return (f"[super-skill loop-guard] Stuck pattern detected ({names}). Stop repeating. "
            + PRESSURE[2] + " If still blocked: " + PRESSURE[4])


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="loop_guard", description="circuit breaker + stuck detector")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    r = sub.add_parser("record")
    r.add_argument("--progress", action="store_true")
    r.add_argument("--error", default=None)
    r.add_argument("--permission-denied", action="store_true")
    sub.add_parser("reset")
    sub.add_parser("check")
    sub.add_parser("stuck")
    e = sub.add_parser("exit-check")
    e.add_argument("output_file")
    e.add_argument("--all-done", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if args.cmd == "status":
        st = load(root)
        st["pressure"] = pressure(st["consecutive_failures"])[1]
        print(json.dumps(st, ensure_ascii=False, indent=2))
    elif args.cmd == "record":
        print(json.dumps(record(root, args.progress, args.error, args.permission_denied), indent=2))
    elif args.cmd == "reset":
        print(json.dumps(reset(root), indent=2))
    elif args.cmd == "check":
        ok, why = can_proceed(root)
        print(why)
        return 0 if ok else 2
    elif args.cmd == "stuck":
        found = detect_stuck(read_jsonl(sdir(root) / "events.jsonl", tail=200))
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return 1 if found else 0
    elif args.cmd == "exit-check":
        text = Path(args.output_file).read_text(encoding="utf-8", errors="replace")
        ok = exit_ok(text, args.all_done)
        print("exit" if ok else "continue")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
