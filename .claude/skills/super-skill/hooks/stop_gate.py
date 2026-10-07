#!/usr/bin/env python3
"""Stop hook — the phase gate that keeps an autonomous run going (W1/W2).

Blocks Claude from ending its turn while an *autonomous* phase is still open,
feeding back the next action and failing gate checks. Anti-loop safeguards
(planning-with-files ``check-complete --gate`` pattern, MIT):

- only when ``gate_mode`` is on and status is ``executing``;
- never for phases that need a human (``autonomous: false``) or while
  ``awaiting_user`` / ``awaiting_approval`` / ``paused`` / ``done``;
- if Claude is already continuing because of this hook (``stop_hook_active``)
  and no work was recorded since the last block, the run is stalled → allow;
- at most ``STOP_CAP`` blocks between two user prompts;
- an exhausted budget always allows the stop.
"""
from __future__ import annotations

import os

import _hooklib as H

STOP_CAP = int(os.environ.get("SUPER_SKILL_STOP_CAP", "20"))


def handle(payload: dict, root):
    H.log_event(root, H.event_record(payload, root))
    st = H.load_state(root)
    if not st.get("gate_mode", True) or st.get("status") != "executing":
        return None
    from ss_common import load_phases, phase_index
    phases = load_phases()
    pid = st.get("active_phase")
    phase = phase_index(phases).get(pid) or {}
    if not phase.get("autonomous"):
        return None
    mark = H.progress_mark(root)
    if payload.get("stop_hook_active") and mark <= int(st.get("stop_progress_mark", -1)):
        H.log_event(root, {"ts": H.now_iso(), "ev": "StopGateRelease", "key": "stalled", "phase": pid})
        return {"systemMessage": f"Super-Skill: phase {pid} stalled (no progress since last nudge) — "
                                 "stopping. Run `ss.py next` to see what is missing."}
    if int(st.get("stop_blocks", 0)) >= STOP_CAP:
        return {"systemMessage": f"Super-Skill: Stop gate released after {STOP_CAP} nudges this turn."}
    budget = st.get("budget") or {}
    if (budget.get("usd_limit") or budget.get("token_limit")) and payload.get("transcript_path"):
        try:
            import cost_meter
            if cost_meter.budget_status(root, payload["transcript_path"]).get("level") == "exceeded":
                return {"systemMessage": "Super-Skill: budget exhausted — stopping."}
        except Exception:
            pass

    import gate_check
    gate = gate_check.run(root, pid, static=True, phases=phases)
    fails = [c["msg"] for c in gate["checks"] if c["ok"] is False and c["severity"] == "error"]
    if fails:
        reason = (f"Super-Skill phase {pid} ({phase.get('name')}) is not complete — keep working. "
                  f"Failing gate checks: {'; '.join(dict.fromkeys(fails))}. Next: {st.get('next_action', '')}")
    else:
        reason = (f"Super-Skill: the static gate for {pid} passes. Run `ss.py advance` now "
                  f"(it also runs command checks) and continue with the next phase.")
    reason += (" If a human-only step blocks you (credentials, payment, approval), run "
               "`ss.py wait \"<reason>\"` and then stop.")
    st["stop_blocks"] = int(st.get("stop_blocks", 0)) + 1
    st["stop_progress_mark"] = mark
    H.save_state(root, st)
    return {"decision": "block", "reason": reason}


if __name__ == "__main__":
    H.run(handle)
