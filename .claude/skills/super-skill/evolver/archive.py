"""Variant archive for the evolver (DGM-style open-ended archive).

Clean-room implementation from published algorithm descriptions:

* DGM (jennyzzt/dgm, Apache-2.0): keep *every* variant; choose a parent with
  weight ``sigmoid(10 * (score - 0.5)) / (1 + children)`` so strong but
  under-explored variants are favoured.
* GEPA (gepa-ai/gepa, MIT): the Pareto front = candidates that are best (or
  tied best) on at least one task, which preserves specialists.

``archive.jsonl`` holds one JSON record per variant::

    {id, parent, created, workspace, target, score, per_task{task: score},
     tokens, lines_added, lines_removed, children,
     status: "keep"|"discard"|"crash"|"seed", eval_stage: "full"|"smoke"|"none",
     desc, feedback{task: text},
     mutation{gene_id, intent, target_files, expected_signal,
              blast_radius{files, lines}}, stagnant[gene_id]}
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
from ss_common import append_jsonl, read_jsonl  # noqa: E402

PARENT_STATUSES = ("keep", "seed")
EPS = 1e-9


# ------------------------------------------------------------------ io

def load(path: Path) -> List[dict]:
    return read_jsonl(Path(path))


def append(path: Path, record: dict) -> None:
    append_jsonl(Path(path), record)


def save_all(path: Path, records: Iterable[dict]) -> None:
    """Atomically rewrite the whole archive (used for child-count updates)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def by_id(archive: List[dict], vid: Optional[str]) -> Optional[dict]:
    for rec in archive:
        if rec.get("id") == vid:
            return rec
    return None


def update_children(path: Path, parent_id: str, delta: int = 1) -> List[dict]:
    """Increment ``children`` of ``parent_id`` on disk; returns new archive."""
    recs = load(path)
    for rec in recs:
        if rec.get("id") == parent_id:
            rec["children"] = int(rec.get("children") or 0) + delta
    save_all(path, recs)
    return recs


# ------------------------------------------------------------------ selection

def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def dgm_weight(score: float, children: int) -> float:
    """DGM parent weight: sigmoid(10*(score-0.5)) / (1 + children)."""
    return sigmoid(10.0 * (float(score) - 0.5)) / (1.0 + max(0, int(children)))


def candidates(archive: List[dict]) -> List[dict]:
    return [r for r in archive if r.get("status") in PARENT_STATUSES
            and r.get("score") is not None]


def select_parent(archive: List[dict], rng: random.Random,
                  method: str = "dgm") -> Optional[dict]:
    """Pick a parent among keep/seed variants.

    ``method="dgm"``: weighted by :func:`dgm_weight` over all candidates.
    ``method="pareto"``: same weights, restricted to :func:`pareto_front`.
    """
    pool = candidates(archive)
    if method == "pareto":
        front = pareto_front(archive)
        if front:
            pool = front
    if not pool:
        return None
    weights = [dgm_weight(r["score"], r.get("children") or 0) for r in pool]
    total = sum(weights)
    if total <= 0:
        return rng.choice(pool)
    x = rng.random() * total
    acc = 0.0
    for rec, w in zip(pool, weights):
        acc += w
        if x < acc:
            return rec
    return pool[-1]


def pareto_front(archive: List[dict],
                 statuses: Iterable[str] = PARENT_STATUSES) -> List[dict]:
    """Variants that are best or tied-best on at least one task.

    Only fully-evaluated variants (``eval_stage != "smoke"``) take part, so a
    smoke-only score never masquerades as a full-suite result.
    """
    statuses = tuple(statuses)
    pool = [r for r in archive if r.get("status") in statuses
            and r.get("per_task") and r.get("eval_stage", "full") != "smoke"]
    best_by_task: Dict[str, float] = {}
    for r in pool:
        for t, s in r["per_task"].items():
            s = float(s)
            if t not in best_by_task or s > best_by_task[t]:
                best_by_task[t] = s
    return [r for r in pool
            if any(float(s) >= best_by_task[t] - EPS for t, s in r["per_task"].items())]


def second_best_score(archive: List[dict]) -> float:
    """Second-highest score among keep/seed variants (-inf if < 2 exist)."""
    scores = sorted((float(r["score"]) for r in candidates(archive)
                     if r.get("eval_stage", "full") != "smoke"), reverse=True)
    if len(scores) < 2:
        return float("-inf")
    return scores[1]


def best(archive: List[dict], statuses: Iterable[str] = PARENT_STATUSES) -> Optional[dict]:
    statuses = tuple(statuses)
    pool = [r for r in archive if r.get("status") in statuses and r.get("score") is not None]
    if not pool:
        return None
    return max(pool, key=lambda r: float(r["score"]))


def is_improvement(child: Dict[str, Any], parent: Dict[str, Any],
                   leeway: float = 0.0) -> bool:
    """True if ``child`` should be kept relative to ``parent``.

    * ``score_child - score_parent > -leeway`` (strictly greater when
      ``leeway == 0``), or
    * simplicity win: score not worse **and** the file shrank
      (``lines_removed > lines_added``) -- deleting text that keeps the
      score is progress.
    """
    cs = child.get("score")
    ps = parent.get("score")
    if cs is None:
        return False
    if ps is None:
        return True
    delta = float(cs) - float(ps)
    if delta > EPS - leeway:
        return True
    shrank = int(child.get("lines_removed") or 0) > int(child.get("lines_added") or 0)
    return delta >= -EPS and shrank
