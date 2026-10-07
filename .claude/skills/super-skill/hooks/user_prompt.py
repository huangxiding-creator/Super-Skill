#!/usr/bin/env python3
"""UserPromptSubmit hook: log the turn, reset the Stop-gate counter (a human
spoke, so the autonomy budget restarts) and re-inject a one-line phase
reminder to fight context rot."""
from __future__ import annotations

import _hooklib as H


def handle(payload: dict, root):
    st = H.load_state(root)
    if st.get("stop_blocks"):
        st["stop_blocks"] = 0
        H.save_state(root, st)
    rec = H.event_record(payload, root)
    rec["summary"] = str(payload.get("prompt", ""))[:120]
    H.log_event(root, rec)
    if st.get("status") == "done":
        return None
    line = (f"[super-skill] run '{st.get('project')}' · phase {st.get('active_phase')} · "
            f"status {st.get('status')} · next: {st.get('next_action', '')[:300]}")
    return H.hook_context("UserPromptSubmit", line)


if __name__ == "__main__":
    H.run(handle)
