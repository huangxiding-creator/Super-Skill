"""Proposal Scorecard (IdeaForge / Super-Skill V4.0) — proposal-forge Stage 3.

The human-facing gate. Four weighted dimensions, each 0..1:

    feasibility 0.25 | user-value 0.30 | monetization 0.20 | tenx 0.25

Gate bands:
    >= GATE_PROCEED (0.72)  → proceed to human Proposal Approval Gate
    >= GATE_REVISE  (0.55)  → revise (send back to research/clarify weak dim)
    else                    → reject, loop idea-intake
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict, field
from typing import Dict, Mapping

WEIGHTS = {"feasibility": 0.25, "user_value": 0.30, "monetization": 0.20, "tenx": 0.25}
GATE_PROCEED = 0.72
GATE_REVISE = 0.55


@dataclass(frozen=True)
class Scorecard:
    feasibility: float
    user_value: float
    monetization: float
    tenx: float
    weighted: float
    verdict: str            # proceed | revise | reject
    rationale: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def compute(feasibility: float, user_value: float, monetization: float,
            tenx: float, rationale: "Mapping[str, str] | None" = None) -> Scorecard:
    dims = {"feasibility": _clamp(feasibility), "user_value": _clamp(user_value),
            "monetization": _clamp(monetization), "tenx": _clamp(tenx)}
    weighted = sum(WEIGHTS[k] * dims[k] for k in WEIGHTS)
    verdict = ("proceed" if weighted >= GATE_PROCEED
               else "revise" if weighted >= GATE_REVISE
               else "reject")
    return Scorecard(
        feasibility=round(dims["feasibility"], 3),
        user_value=round(dims["user_value"], 3),
        monetization=round(dims["monetization"], 3),
        tenx=round(dims["tenx"], 3),
        weighted=round(weighted, 3),
        verdict=verdict,
        rationale=dict(rationale or {}),
    )


def weakest_dim(card: Scorecard) -> str:
    """Return the dimension name most worth re-researching when verdict != proceed."""
    return min(("feasibility", "user_value", "monetization", "tenx"),
               key=lambda k: getattr(card, k))


if __name__ == "__main__":
    # CLI: JSON {feasibility, user_value, monetization, tenx, rationale?}
    raw = sys.stdin.read() if (len(sys.argv) < 2 or sys.argv[1] == "-") else open(sys.argv[1], encoding="utf-8").read()
    data = json.loads(raw)
    card = compute(data.get("feasibility", 0), data.get("user_value", 0),
                   data.get("monetization", 0), data.get("tenx", 0),
                   data.get("rationate") or data.get("rationale"))
    print(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))
