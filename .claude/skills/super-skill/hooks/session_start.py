#!/usr/bin/env python3
"""SessionStart hook: inject the run brief (phase, next action, gate, tasks,
playbook, hand-off) so every new/resumed/compacted session continues the run
instead of starting over. Matcher: startup|resume|clear|compact."""
from __future__ import annotations

import _hooklib as H


def handle(payload: dict, root):
    import brief

    source = payload.get("source") or "startup"
    st = H.load_state(root)
    if st.get("stop_blocks"):
        st["stop_blocks"] = 0
        H.save_state(root, st)
    H.log_event(root, H.event_record(payload, root))
    text = brief.build_brief(root, payload.get("transcript_path"), source=source)
    return H.hook_context("SessionStart", text) if text else None


if __name__ == "__main__":
    H.run(handle)
