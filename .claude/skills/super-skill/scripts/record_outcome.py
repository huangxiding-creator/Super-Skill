"""Record an IdeaForge proposal outcome into the GEP evolution log (Super-Skill V4.0).

Closes the learning loop: when a proposal's real-world result is known (built +
monetized / killed / rejected at gate), append an EvolutionEvent so
gene_ideaforge_outcome_learning can turn wins into reusable Capsules and
disconfirmations into tighter ten× calibration.

Appends one JSON line to assets/gep/events.jsonl. Never mutates history.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Mapping

_HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(_HERE)
EVENTS = os.path.join(SKILL_ROOT, "assets", "gep", "events.jsonl")

VALID_OUTCOMES = {"built_monetized", "built_not_monetized", "killed", "rejected_at_gate", "revised"}


def record(outcome: Mapping, events_path: str = EVENTS) -> dict:
    """Append one outcome event. Returns the event dict.

    Required keys: proposal, result (in VALID_OUTCOMES).
    Optional: tenx_axis, tenx_multiplier, scorecard_verdict, revenue, users, notes.
    """
    result = outcome.get("result")
    if result not in VALID_OUTCOMES:
        raise ValueError(f"result must be one of {sorted(VALID_OUTCOMES)}; got {result!r}")
    if not outcome.get("proposal"):
        raise ValueError("proposal (name/title) is required")

    confirmed = result == "built_monetized"
    disconfirmed = result in ("built_not_monetized", "killed")
    signals = []
    if confirmed:
        signals.append("tenx_confirmed")
    if disconfirmed:
        signals.append("tenx_disconfirmed")
    if result == "rejected_at_gate":
        signals.append("idea_rejected_at_gate")
    if outcome.get("revenue"):
        signals.append("revenue_observed")
    signals.append("proposal_outcome")
    signals.append("monetization_result")

    event = {
        "type": "EvolutionEvent",
        "schema_version": "1.5.0",
        "id": f"evt_ideaforge_{int(time.time() * 1000)}",
        "parent": None,
        "intent": "innovate",
        "signals": signals,
        "genes_used": ["gene_ideaforge_outcome_learning"],
        "outcome_meta": {
            "proposal": outcome["proposal"],
            "result": result,
            "tenx_axis": outcome.get("tenx_axis"),
            "tenx_multiplier": outcome.get("tenx_multiplier"),
            "scorecard_verdict": outcome.get("scorecard_verdict"),
            "revenue": outcome.get("revenue"),
            "users": outcome.get("users"),
            "notes": outcome.get("notes", ""),
        },
        "outcome": {"status": "success" if confirmed else "neutral",
                    "score": float(outcome.get("learning_score", 0.5))},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    os.makedirs(os.path.dirname(events_path), exist_ok=True)
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: record_outcome.py <outcome.json>\n")
        return 2
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    ev = record(data)
    print(json.dumps({"recorded": ev["id"], "signals": ev["signals"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
