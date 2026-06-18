"""TenX Delta Index (IdeaForge / Super-Skill V4.0) — proposal-forge Stage 3.

Turns "ten-times-better" from a slogan into a falsifiable gate. For each
differentiator axis, compares our product's value against the best existing
solution; the index is the maximum order-of-magnitude advantage across axes.

    delta_axis = ours / baseline   (higher_better)
               = baseline / ours   (lower_better)
    TenX       = max_axis  log10(delta_axis)        # i.e. "N times" on the best axis

Verdict bands (operationalize the user's "十倍好" definition):
    >= 1.0  → tenx-qualified  (≥10× on some axis)  → may proceed
    0.3–1.0 → incremental                            → must find a new angle
    < 0.3   → red ocean                              → kill or pivot
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Mapping

DEFAULT_AXES = {
    # axis: direction
    "dev_efficiency": "higher_better",   # output per engineer-hour
    "deploy_cost": "lower_better",
    "extensibility": "higher_better",
    "cac": "lower_better",               # customer acquisition cost
    "price": "lower_better",
    "onboarding_time": "lower_better",
    "latency": "lower_better",
}

TENX_QUALIFIED = 1.0     # log10 => 10x
INCREMENTAL_FLOOR = 0.3  # ~2x


@dataclass(frozen=True)
class AxisDelta:
    axis: str
    direction: str
    ours: float
    baseline: float
    delta: float          # ratio (>=1 means we're better)
    log10: float          # log10(delta)
    better: bool


@dataclass(frozen=True)
class TenXResult:
    tenx: float                     # max log10(delta) across axes
    best_axis: str
    verdict: str                    # tenx_qualified | incremental | red_ocean
    axes: List[AxisDelta]
    multiplier: float = 1.0         # 10**tenx on best axis

    def to_dict(self) -> Dict:
        return {**asdict(self), "axes": [asdict(a) for a in self.axes]}


def _delta(direction: str, ours: float, baseline: float) -> float:
    if direction == "lower_better":
        return baseline / ours if ours > 0 else 0.0
    return ours / baseline if baseline > 0 else 0.0


def score(claims: Mapping[str, Mapping[str, float]],
          axes: Mapping[str, str] = DEFAULT_AXES) -> TenXResult:
    """``claims`` maps axis -> {"ours": n, "baseline": n}.

    Unknown axes are ignored. Missing fields are skipped (not penalized) so a
    sparse claim set doesn't silently score red ocean.
    """
    deltas: List[AxisDelta] = []
    for axis, direction in axes.items():
        if axis not in claims:
            continue
        c = claims[axis]
        ours = float(c.get("ours", 0) or 0)
        baseline = float(c.get("baseline", 0) or 0)
        if ours <= 0 or baseline <= 0:
            continue
        d = _delta(direction, ours, baseline)
        lg = math.log10(d) if d > 0 else -9.0
        deltas.append(AxisDelta(axis=axis, direction=direction, ours=ours,
                                baseline=baseline, delta=round(d, 3),
                                log10=round(lg, 3), better=d >= 1.0))
    if not deltas:
        return TenXResult(tenx=-9.0, best_axis="", verdict="red_ocean",
                          axes=[], multiplier=0.0)
    best = max(deltas, key=lambda a: a.log10)
    tenx = best.log10
    verdict = ("tenx_qualified" if tenx >= TENX_QUALIFIED
               else "incremental" if tenx >= INCREMENTAL_FLOOR
               else "red_ocean")
    return TenXResult(tenx=round(tenx, 3), best_axis=best.axis,
                      verdict=verdict, axes=deltas, multiplier=round(10 ** tenx, 2))


def derive_tenx_score(result: TenXResult) -> float:
    """Map the TenX result to a 0..1 scorecard sub-score for the 'tenx' dimension."""
    if not result.axes:
        return 0.0
    # >=1.0 (10x) => ~0.95+; 0.3 => ~0.4; <0.3 => <0.4
    return round(max(0.0, min(0.99, 0.35 + result.tenx * 0.6)), 3)


if __name__ == "__main__":
    raw = sys.stdin.read() if (len(sys.argv) < 2 or sys.argv[1] == "-") else open(sys.argv[1], encoding="utf-8").read()
    claims = json.loads(raw)
    r = score(claims)
    print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
