"""Strategy presets, gene selection and stagnation detection.

A strategy is a weight vector over the three GEP gene categories
(repair / optimize / innovate). Each iteration: draw a category by weight,
then a gene of that category from ``assets/gep/genes.json``, preferring genes
whose ``signals_match`` overlap the current failure signals.

Stagnation: if the most recent run of variants used the same gene_id >= 3
times in a row without an improvement, that gene is excluded for the next
round and reported as ``stagnant``.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
from ss_common import SKILL_DIR, read_json  # noqa: E402

GENES_FILE = SKILL_DIR / "assets" / "gep" / "genes.json"
CATEGORIES = ("repair", "optimize", "innovate")
STAGNATION_RUN = 3

PRESETS: Dict[str, Dict[str, float]] = {
    "balanced": {"repair": 0.34, "optimize": 0.33, "innovate": 0.33},
    "innovate": {"repair": 0.2, "optimize": 0.2, "innovate": 0.6},
    "harden": {"repair": 0.5, "optimize": 0.4, "innovate": 0.1},
    "repair-only": {"repair": 1.0, "optimize": 0.0, "innovate": 0.0},
}

# Minimal fallback so the loop still works if genes.json is missing.
FALLBACK_GENES = [
    {"type": "Gene", "id": "gene_fallback_repair", "category": "repair",
     "signals_match": ["failed", "error"],
     "strategy": ["Fix the most frequent failure with the smallest edit"]},
    {"type": "Gene", "id": "gene_fallback_optimize", "category": "optimize",
     "signals_match": ["prompt", "verbose"],
     "strategy": ["Tighten wording; delete text that does not change behaviour"]},
    {"type": "Gene", "id": "gene_fallback_innovate", "category": "innovate",
     "signals_match": ["capability_gap"],
     "strategy": ["Add one missing capability the failing tasks need"]},
]


def load_genes(path: Optional[Path] = None) -> List[dict]:
    data = read_json(Path(path) if path else GENES_FILE, default=None)
    genes = data.get("genes") if isinstance(data, dict) else None
    genes = [g for g in (genes or []) if isinstance(g, dict) and g.get("id")]
    return genes or list(FALLBACK_GENES)


def get_weights(strategy: str) -> Dict[str, float]:
    if strategy not in PRESETS:
        raise ValueError(f"unknown strategy {strategy!r}; choose from {sorted(PRESETS)}")
    return dict(PRESETS[strategy])


def pick_category(weights: Mapping[str, float], rng: random.Random,
                  allowed: Optional[Iterable[str]] = None) -> str:
    allowed_set = set(allowed) if allowed is not None else set(weights)
    items = [(c, float(w)) for c, w in weights.items() if c in allowed_set and w > 0]
    if not items:
        items = [(c, 1.0) for c in weights if c in allowed_set] or [(c, 1.0) for c in weights]
    total = sum(w for _, w in items)
    x = rng.random() * total
    acc = 0.0
    for c, w in items:
        acc += w
        if x < acc:
            return c
    return items[-1][0]


def _norm(s: str) -> str:
    return s.lower().replace("_", " ").strip()


def extract_signals(per_task: Optional[Mapping[str, float]],
                    feedback: Optional[Mapping[str, str]],
                    genes: Sequence[dict] = ()) -> List[str]:
    """Derive GEP-style signals from an evaluation result."""
    sig: Set[str] = set()
    per_task = per_task or {}
    failed = [t for t, s in per_task.items() if float(s) < 1.0]
    if failed:
        sig.add("failed")
    elif per_task:
        sig.add("stable_success_plateau")
    text = " ".join(str(v) for v in (feedback or {}).values()).lower()
    for word in ("error", "exception", "timeout", "unstable"):
        if word in text:
            sig.add(word)
    known = {s for g in genes for s in (g.get("signals_match") or [])}
    for s in known:
        if _norm(s) and (_norm(s) in text or s.lower() in text):
            sig.add(s)
    return sorted(sig)


def gene_hits(gene: Mapping, signals: Iterable[str]) -> int:
    match = {_norm(s) for s in (gene.get("signals_match") or [])}
    return sum(1 for s in signals if _norm(s) in match)


def detect_stagnation(history: Sequence[Tuple[Optional[str], bool]],
                      run: int = STAGNATION_RUN) -> Set[str]:
    """``history``: chronological (gene_id, improved) of mutated variants.

    Returns the gene_id whose trailing consecutive run of non-improving uses
    has length >= ``run`` (empty set otherwise).
    """
    if not history:
        return set()
    last_gene = history[-1][0]
    if not last_gene:
        return set()
    count = 0
    for gene_id, improved in reversed(history):
        if gene_id != last_gene or improved:
            break
        count += 1
    return {last_gene} if count >= run else set()


def history_from_archive(archive: Sequence[dict]) -> List[Tuple[Optional[str], bool]]:
    out = []
    for rec in archive:
        if rec.get("status") == "seed":
            continue
        gene_id = (rec.get("mutation") or {}).get("gene_id")
        out.append((gene_id, rec.get("status") == "keep"))
    return out


def pick_gene(strategy: str, genes: Sequence[dict], signals: Iterable[str],
              rng: random.Random, exclude: Iterable[str] = ()) -> Tuple[dict, str]:
    """Return (gene, category). Category drawn by preset weight; within the
    category, genes with the most signal hits win (ties broken by rng)."""
    signals = list(signals)
    excluded = set(exclude)
    usable = [g for g in genes if g.get("id") not in excluded] or list(genes)
    by_cat: Dict[str, List[dict]] = {}
    for g in usable:
        by_cat.setdefault(g.get("category") or "optimize", []).append(g)
    weights = get_weights(strategy)
    available = [c for c in weights if by_cat.get(c)]
    if not available:
        g = rng.choice(usable)
        return g, g.get("category") or "optimize"
    cat = pick_category(weights, rng, allowed=available)
    pool = by_cat[cat]
    scored = [(gene_hits(g, signals), g) for g in pool]
    top = max(h for h, _ in scored)
    return rng.choice([g for h, g in scored if h == top]), cat
