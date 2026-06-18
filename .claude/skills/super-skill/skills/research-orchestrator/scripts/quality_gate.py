"""Quality gate (IdeaForge / Super-Skill V4.0) — validates a harvested docket.

Ports the ResearchFactory-Eng quality-gate idea (摘要质检 / 打包质检): before the
docket is handed to proposal-forge, run cheap structural checks so we don't propose
on empty, all-degraded, or low-credibility evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Sequence

from channels.base import Doc

MIN_TOTAL_DOCS = 5
MAX_DEGRADED_RATIO = 0.5
MIN_AVG_CREDIBILITY = 0.35
MIN_CONTENT_LEN = 20  # chars; shorter than this is not substantive


@dataclass
class QualityResult:
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


def evaluate(docs: Sequence[Doc]) -> QualityResult:
    total = len(docs)
    real = [d for d in docs if d.doc_type != "degraded"]
    degraded = total - len(real)
    degraded_ratio = (degraded / total) if total else 1.0
    substantive = [d for d in real if len(d.content) >= MIN_CONTENT_LEN or d.signals]
    avg_cred = (sum(d.credibility for d in real) / len(real)) if real else 0.0

    checks = {
        "enough_total_docs": total >= MIN_TOTAL_DOCS,
        "not_mostly_degraded": degraded_ratio <= MAX_DEGRADED_RATIO,
        "avg_credibility_ok": avg_cred >= MIN_AVG_CREDIBILITY,
        "has_substantive_docs": len(substantive) >= 3,
    }
    warnings: List[str] = []
    if not checks["enough_total_docs"]:
        warnings.append(f"only {total} docs (need >= {MIN_TOTAL_DOCS}); widen research")
    if not checks["not_mostly_degraded"]:
        warnings.append(f"{int(degraded_ratio*100)}% channels degraded; check keys/anti-bot")
    if not checks["avg_credibility_ok"]:
        warnings.append(f"avg credibility {avg_cred:.2f} below {MIN_AVG_CREDIBILITY}")
    if not checks["has_substantive_docs"]:
        warnings.append("few substantive docs; content too thin to propose on")

    return QualityResult(
        passed=all(checks.values()),
        checks=checks,
        warnings=warnings,
        stats={"total": total, "real": len(real), "degraded": degraded,
               "degraded_ratio": round(degraded_ratio, 3), "avg_credibility": round(avg_cred, 3)},
    )
