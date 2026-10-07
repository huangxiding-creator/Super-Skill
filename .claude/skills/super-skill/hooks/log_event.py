#!/usr/bin/env python3
"""Generic observability hook for SubagentStart/SubagentStop, Notification and
SessionEnd: one line per event in ``.super-skill/events.jsonl``. Kept tiny —
SessionEnd hooks share a 1.5 s budget."""
from __future__ import annotations

import _hooklib as H


def handle(payload: dict, root):
    rec = H.event_record(payload, root)
    if payload.get("hook_event_name") == "Notification":
        rec["summary"] = str(payload.get("message", ""))[:160]
    elif payload.get("hook_event_name") == "SessionEnd":
        rec["summary"] = str(payload.get("reason", ""))
    H.log_event(root, rec)
    return None


if __name__ == "__main__":
    H.run(handle)
