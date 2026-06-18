"""Gap analyzer (IdeaForge / Super-Skill V4.0) — proposal-dimension × evidence coverage.

Ports the ResearchFactory-Eng gap-analysis idea: after the first research pass, build
a coverage matrix of *proposal dimensions* × *harvested evidence*; weak dimensions
trigger a targeted re-research (specific channel + query) instead of a blunt re-run.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Sequence

from channels.base import Doc

# The dimensions a complete proposal needs evidence for.
PROPOSAL_DIMENSIONS = ("problem", "competitors", "pricing", "maturity", "demand", "differentiation")

# Which doc types/channels satisfy which dimension.
_DIM_SOURCES = {
    "problem": {"article", "post"},          # sogou/reddit/hn pain stories
    "competitors": {"repo", "app", "product", "package"},
    "pricing": {"pricing", "page"},
    "maturity": {"repo", "package"},          # stars/forks/release_count
    "demand": {"post", "product", "trend"},
    "differentiation": set(),                 # derived: needs both problem + competitors
}

MIN_PER_DIM = 2  # need >=2 evidence docs for a dimension to count as "covered"


@dataclass(frozen=True)
class DimensionCoverage:
    dimension: str
    covered: bool
    count: int
    contributing_channels: List[str]


@dataclass(frozen=True)
class GapReport:
    coverage: List[DimensionCoverage]
    gaps: List[str]                  # uncovered dimensions
    re_research: List[Dict]          # recommended targeted actions
    differentiation_possible: bool

    def to_dict(self) -> Dict:
        return asdict(self)


def analyze(docs: Sequence[Doc]) -> GapReport:
    by_type: Dict[str, List[Doc]] = {}
    for d in docs:
        if d.doc_type == "degraded":
            continue
        by_type.setdefault(d.doc_type, []).append(d)

    coverage: List[DimensionCoverage] = []
    gaps: List[str] = []
    for dim in PROPOSAL_DIMENSIONS:
        sources = _DIM_SOURCES[dim]
        if dim == "differentiation":
            continue  # handled after the loop
        hits = []
        for t in sources:
            hits.extend(by_type.get(t, []))
        count = len(hits)
        chans = sorted({d.channel for d in hits})
        covered = count >= MIN_PER_DIM
        coverage.append(DimensionCoverage(dim, covered, count, chans))
        if not covered:
            gaps.append(dim)

    # differentiation = problem + competitors both have evidence
    prob = next((c for c in coverage if c.dimension == "problem"), None)
    comp = next((c for c in coverage if c.dimension == "competitors"), None)
    diff_possible = bool(prob and comp and prob.count >= 1 and comp.count >= 1)
    coverage.append(DimensionCoverage("differentiation", diff_possible,
                                      int(diff_possible),
                                      (prob.contributing_channels if prob else []) +
                                      (comp.contributing_channels if comp else [])))
    if not diff_possible:
        gaps.append("differentiation")

    re_research = _recommend(gaps, by_type)
    return GapReport(coverage=coverage, gaps=gaps,
                     re_research=re_research, differentiation_possible=diff_possible)


_DIM_RECOMMENDATIONS = {
    "problem": {"channels": ["sogou_wechat", "reddit", "hackernews"],
                "note": "broaden pain query; add domain subreddits"},
    "competitors": {"channels": ["github", "appstore"],
                    "note": "try alternate keywords; lower star threshold"},
    "pricing": {"channels": ["competitor_site"],
                "note": "add competitor_urls (homepages) to seed; fetch /pricing"},
    "maturity": {"channels": ["github", "npm_pypi"],
                 "note": "inspect top repos' commit/release cadence"},
    "demand": {"channels": ["googletrends", "reddit", "producthunt"],
               "note": "check mention volume; set PRODUCTHUNT_TOKEN"},
    "differentiation": {"channels": ["github", "sogou_wechat"],
                        "note": "need both pain + competitor evidence to argue a delta"},
}


def _recommend(gaps: List[str], by_type: Dict[str, List[Doc]]) -> List[Dict]:
    out: List[Dict] = []
    for g in gaps:
        rec = _DIM_RECOMMENDATIONS.get(g)
        if rec:
            out.append({"dimension": g, **rec})
    return out
