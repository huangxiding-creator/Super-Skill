#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure hook (W1/W5/W9).

1. append the event to ``.super-skill/events.jsonl`` (observability);
2. count real work (edits, shell commands) for the Stop-gate progress check;
3. run the stuck detector and, once per pattern, inject pressure-ladder advice;
4. warn (non-blocking) on playbook do-not-repeat matches in new edits;
5. warn once when spend crosses the budget warn ratio.
"""
from __future__ import annotations

import _hooklib as H
from ss_common import read_jsonl


def _already_warned(root, kind: str, key: str, lookback: int = 60) -> bool:
    return any(e.get("ev") == kind and e.get("key") == key
               for e in read_jsonl(H.sdir(root) / "events.jsonl", tail=lookback))


def handle(payload: dict, root):
    rec = H.event_record(payload, root)
    H.log_event(root, rec)
    tool = payload.get("tool_name") or ""
    if rec.get("ok") and (tool in H.EDIT_TOOLS or tool in H.SHELL_TOOLS):
        H.bump_progress(root)
    notes = []

    import loop_guard
    findings = loop_guard.detect_stuck(read_jsonl(H.sdir(root) / "events.jsonl", tail=60))
    if findings:
        key = "|".join(sorted(f["pattern"] for f in findings))
        if not _already_warned(root, "LoopGuardWarn", key, lookback=12):
            H.log_event(root, {"ts": H.now_iso(), "ev": "LoopGuardWarn", "key": key})
            notes.append(loop_guard.stuck_advice(findings))

    if tool in H.EDIT_TOOLS:
        ti = payload.get("tool_input") or {}
        text = ti.get("content") or ti.get("new_string") or ""
        if text:
            try:
                import playbook
                hits = [h for h in playbook.check_text(root, text) if not h.get("block")]
            except Exception:
                hits = []
            for h in hits[:3]:
                notes.append(f"[super-skill playbook] do-not-repeat {h.get('id')}: {h.get('text')} — "
                             f"revise {ti.get('file_path', 'the edit')} if this applies.")

    st = H.load_state(root)
    budget = st.get("budget") or {}
    if (budget.get("usd_limit") or budget.get("token_limit")) and payload.get("transcript_path"):
        try:
            import cost_meter
            b = cost_meter.budget_status(root, payload["transcript_path"])
        except Exception:
            b = {}
        if b.get("level") in ("warn", "exceeded") and not _already_warned(root, "BudgetWarn", b["level"], 400):
            H.log_event(root, {"ts": H.now_iso(), "ev": "BudgetWarn", "key": b["level"]})
            notes.append(f"[super-skill budget] {b['level']}: {b.get('ratio', 0):.0%} of the limit used "
                         f"(≈${b.get('spent_usd', 0):.2f}, estimate). Prioritise finishing the current task.")
    if notes:
        return H.hook_context(payload.get("hook_event_name") or "PostToolUse", "\n".join(notes))
    return None


if __name__ == "__main__":
    H.run(handle)
