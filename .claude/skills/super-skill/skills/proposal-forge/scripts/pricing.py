"""Data-driven pricing (IdeaForge / Super-Skill V4.0) — proposal-forge Stage 3.

Derives pricing bands from harvested competitor prices instead of guessing.
Operationalizes the user's Insight 3 ("变现就绪前置到设计阶段"): BUSINESS_MODEL.md
gets a price recommendation backed by real market data.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class PriceBands:
    p10: float
    p25: float
    p50: float  # median
    p75: float
    p90: float
    n: int


@dataclass(frozen=True)
class PriceRecommendation:
    positioning: str        # cost_leader | value | premium
    model_hint: str         # subscription | usage | one_time | freemium
    recommended: float
    anchor: float           # median competitor price
    floor: float            # p25
    rationale: str
    bands: PriceBands


def _percentile(sorted_vals: Sequence[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return float(sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f))


def compute_bands(prices: Sequence[float]) -> PriceBands:
    clean = sorted(float(p) for p in prices if p and float(p) > 0)
    return PriceBands(
        p10=_percentile(clean, 0.10), p25=_percentile(clean, 0.25),
        p50=_percentile(clean, 0.50), p75=_percentile(clean, 0.75),
        p90=_percentile(clean, 0.90), n=len(clean),
    )


_MODEL_BY_POSITIONING = {
    "cost_leader": "subscription",   # low price → scale via volume subscription
    "value": "subscription",
    "premium": "usage",              # capture high willingness-to-pay via usage
}


def recommend(prices: Sequence[float], positioning: str = "value") -> PriceRecommendation:
    """Recommend a price from competitor bands + positioning.

    positioning:
      cost_leader → price at p10–p25 (win on price)
      value       → price at p50       (parity, win on differentiation)
      premium     → price at p75–p90   (capture surplus from 10× value)
    """
    bands = compute_bands(prices)
    positioning = positioning if positioning in _MODEL_BY_POSITIONING else "value"
    if bands.n == 0:
        return PriceRecommendation(
            positioning=positioning, model_hint=_MODEL_BY_POSITIONING[positioning],
            recommended=0.0, anchor=0.0, floor=0.0,
            rationale="no competitor price data — LLM must estimate from domain",
            bands=bands,
        )
    if positioning == "cost_leader":
        rec = round((bands.p10 + bands.p25) / 2, 2)
        why = f"cost-leader: average of p10({bands.p10:.2f}) & p25({bands.p25:.2f})"
    elif positioning == "premium":
        rec = round((bands.p75 + bands.p90) / 2, 2)
        why = f"premium: average of p75({bands.p75:.2f}) & p90({bands.p90:.2f})"
    else:
        rec = round(bands.p50, 2)
        why = f"value parity at median p50({bands.p50:.2f})"
    return PriceRecommendation(
        positioning=positioning, model_hint=_MODEL_BY_POSITIONING[positioning],
        recommended=rec, anchor=round(bands.p50, 2), floor=round(bands.p25, 2),
        rationale=why, bands=bands,
    )


def positioning_from_tenx(tenx_verdict: str, best_axis: str) -> str:
    """Derive positioning from the TenX result (called by proposal-forge)."""
    if tenx_verdict == "tenx_qualified" and best_axis in ("price", "deploy_cost", "cac"):
        return "cost_leader"
    if tenx_verdict == "tenx_qualified":
        return "premium"
    return "value"


if __name__ == "__main__":
    import json, sys
    raw = sys.stdin.read() if (len(sys.argv) < 2 or sys.argv[1] == "-") else open(sys.argv[1], encoding="utf-8").read()
    payload = json.loads(raw)
    rec = recommend(payload.get("prices", []), payload.get("positioning", "value"))
    print(json.dumps(asdict(rec), ensure_ascii=False, indent=2))
