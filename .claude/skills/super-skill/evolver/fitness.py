"""Fitness function for the Super-Skill V5 evolver.

    fitness = pass_rate - lambda * (tokens / 1e5) - mu * (lines_added / 100)

``pass_rate`` is the mean of per-task scores (each clamped to [0, 1]).
The two penalty terms implement a simplicity pressure: a variant that costs
more tokens or grows the target file must buy that growth with a real gain
in pass rate. Stdlib only.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

DEFAULT_CFG: Dict[str, float] = {"lambda": 0.05, "mu": 0.02}


def clamp01(x: Any) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    if v != v:  # NaN
        return 0.0
    return max(0.0, min(1.0, v))


def pass_rate(per_task: Optional[Mapping[str, Any]]) -> float:
    """Mean of per-task scores in [0, 1]; 0.0 for an empty result."""
    if not per_task:
        return 0.0
    vals = [clamp01(v) for v in per_task.values()]
    return sum(vals) / len(vals)


def fitness(result: Mapping[str, Any], cfg: Optional[Mapping[str, Any]] = None) -> float:
    """Score an evaluation result.

    ``result`` keys: ``tasks`` (or ``per_task``) -> {task: score},
    ``tokens`` (int), ``lines_added`` (int). Missing keys count as 0.
    ``cfg`` may override ``lambda`` / ``mu``.
    """
    c = dict(DEFAULT_CFG)
    if cfg:
        for k in ("lambda", "mu"):
            if cfg.get(k) is not None:
                c[k] = float(cfg[k])
    per_task = result.get("tasks")
    if per_task is None:
        per_task = result.get("per_task")
    tokens = max(0.0, float(result.get("tokens") or 0))
    lines = max(0.0, float(result.get("lines_added") or 0))
    return pass_rate(per_task) - c["lambda"] * (tokens / 1e5) - c["mu"] * (lines / 100.0)
