"""Maturity Index (IdeaForge / Super-Skill V4.0) — proposal-forge Stage 3.

Scores how production-ready & sustainable a candidate technical solution (typically
a GitHub repo) is, on a deterministic 0–100 scale. Operationalizes the user's
Insight 2 ("GitHub signals → 方案成熟度指数"). Weighted blend of 5 components:

    recency 0.25 | adoptability 0.25 | health 0.20 | ecosystem 0.15 | license 0.15

Without paid GitHub time-series we approximate momentum with star/fork magnitude +
update recency; the LLM (or a richer fetcher) can supply real growth history later —
the component weights stay stable.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List, Mapping, Optional, Sequence

# Weight vector (sums to 1.0). Tunable in one place.
WEIGHTS = {"recency": 0.25, "adoptability": 0.25, "health": 0.20,
           "ecosystem": 0.15, "license": 0.15}

# Verdict bands.
MATURE, VIABLE = 70.0, 40.0

_LICENSE_SCORE = {
    "MIT": 1.0, "Apache-2.0": 1.0, "BSD-2-Clause": 1.0, "BSD-3-Clause": 1.0,
    "ISC": 1.0, "MPL-2.0": 0.85, "LGPL-3.0": 0.6, "GPL-3.0": 0.5, "GPL-2.0": 0.5,
    "AGPL-3.0": 0.4, "Unlicense": 0.9, "CC0-1.0": 0.9, "NOASSERTION": 0.4,
    "NONE": 0.3,
}


@dataclass(frozen=True)
class MaturityScore:
    score: float                      # 0..100
    components: Dict[str, float]      # each component 0..1
    verdict: str                      # mature | viable | immature
    source: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def _days_since(iso_ts: str) -> Optional[float]:
    if not iso_ts:
        return None
    try:
        # GitHub uses "...Z"; fromisoformat wants +00:00
        ts = iso_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0


def _recency(updated_at: str) -> float:
    d = _days_since(updated_at)
    if d is None:
        return 0.0
    return max(0.0, 1.0 - d / 365.0)  # full marks if updated today, 0 if >1yr stale


def _adoptability(stars: int, forks: int) -> float:
    # log-scaled: 100k stars ~ 1.0; 100 stars ~ 0.4
    s = math.log10(max(stars, 1) + 1) / 5.0
    f = math.log10(max(forks, 1) + 1) / 4.0
    return max(0.0, min(1.0, 0.7 * s + 0.3 * f))


def _health(stars: int, forks: int, open_issues: int) -> float:
    # lower issues/star ratio is healthier; forks indicate contributor base
    ratio = open_issues / max(stars, 1)
    issue_health = max(0.0, 1.0 - ratio)            # 0 issues/star => 1
    fork_signal = min(1.0, math.log10(max(forks, 1) + 1) / 3.0)
    return max(0.0, min(1.0, 0.6 * issue_health + 0.4 * fork_signal))


def _ecosystem(language: str, topics: Sequence[str]) -> float:
    lang = 1.0 if language else 0.0
    topic_signal = min(1.0, len(topics) / 5.0)      # 5+ topics => full
    return max(0.0, min(1.0, 0.4 * lang + 0.6 * topic_signal))


def _license(license_id: str) -> float:
    return _LICENSE_SCORE.get((license_id or "NONE").strip(), 0.4)


def score_repo(signals: Mapping, source: str = "") -> MaturityScore:
    """Score one repo's signals dict (the 'signals' field of a research Doc)."""
    stars = int(signals.get("stars", 0) or 0)
    forks = int(signals.get("forks", 0) or 0)
    issues = int(signals.get("open_issues", 0) or 0)
    components = {
        "recency": _recency(str(signals.get("updated_at", ""))),
        "adoptability": _adoptability(stars, forks),
        "health": _health(stars, forks, issues),
        "ecosystem": _ecosystem(str(signals.get("language", "")),
                                signals.get("topics", []) or []),
        "license": _license(str(signals.get("license", "NONE"))),
    }
    score = 100.0 * sum(WEIGHTS[k] * components[k] for k in WEIGHTS)
    verdict = "mature" if score >= MATURE else "viable" if score >= VIABLE else "immature"
    return MaturityScore(score=round(score, 1), components=components, verdict=verdict, source=source)


@dataclass(frozen=True)
class LandscapeReport:
    best: Optional[MaturityScore]
    median: float
    mean: float
    n: int
    mature_count: int


def score_landscape(repos: Sequence[Mapping]) -> LandscapeReport:
    """Summarize the competitor/solution landscape from a list of repo signal dicts."""
    if not repos:
        return LandscapeReport(best=None, median=0.0, mean=0.0, n=0, mature_count=0)
    scores = [score_repo(r) for r in repos]
    vals = sorted(s.score for s in scores)
    n = len(vals)
    median = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    mean = sum(vals) / n
    best = max(scores, key=lambda s: s.score)
    mature_count = sum(1 for s in scores if s.verdict == "mature")
    return LandscapeReport(best=best, median=round(median, 1),
                           mean=round(mean, 1), n=n, mature_count=mature_count)


def derive_feasibility(landscape: LandscapeReport) -> float:
    """Map landscape maturity to a 0..1 feasibility estimate for the scorecard.

    If existing mature solutions exist, building is lower-risk (high feasibility)
    but differentiation must come from elsewhere. If nothing is mature, feasibility
    is bounded by whether the approach is proven elsewhere; we map median maturity.
    """
    if landscape.n == 0:
        return 0.5  # unknown — neutral
    # proven space => technically feasible; median maturity drives it
    return round(max(0.3, min(0.95, 0.35 + landscape.median / 150.0)), 3)


if __name__ == "__main__":
    # CLI: read a JSON list of repo signal dicts from file/stdin -> landscape report
    raw = sys.stdin.read() if (len(sys.argv) < 2 or sys.argv[1] == "-") else open(sys.argv[1], encoding="utf-8").read()
    data = json.loads(raw)
    repos = data if isinstance(data, list) else [data]
    land = score_landscape(repos)
    print(json.dumps({
        "best": land.best.to_dict() if land.best else None,
        "median": land.median, "mean": land.mean, "n": land.n,
        "mature_count": land.mature_count,
        "derived_feasibility": derive_feasibility(land),
    }, ensure_ascii=False, indent=2))
