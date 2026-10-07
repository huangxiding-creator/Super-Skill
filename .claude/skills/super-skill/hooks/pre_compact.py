#!/usr/bin/env python3
"""PreCompact hook: write ``.super-skill/handoff.md`` before the context is
compacted; the SessionStart hook (matcher ``compact``) re-injects it.
Pattern: parcadei/Continuous-Claude hand-offs (MIT)."""
from __future__ import annotations

import _hooklib as H


def handle(payload: dict, root):
    import brief

    H.log_event(root, H.event_record(payload, root))
    brief.write_handoff(root, reason=f"pre-compact ({payload.get('trigger') or 'auto'})")
    return None


if __name__ == "__main__":
    H.run(handle)
