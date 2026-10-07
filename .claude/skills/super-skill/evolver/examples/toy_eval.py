"""Deterministic toy evaluator for the evolver demo and tests.

Each task passes (1.0) iff its required keyword appears in the target text
(case-insensitive); otherwise 0.0 with feedback ``missing keyword '<kw>'``.

    python toy_eval.py <target> [--tasks a,b]

Prints ``{"tasks": {...}, "tokens": int, "feedback": {...}}``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

TASKS = {
    "t_install": "install",
    "t_usage": "usage",
    "t_test": "pytest",
    "t_license": "license",
    "t_verify": "verify",
}


def score(text: str, tasks: Optional[Sequence[str]] = None) -> dict:
    low = text.lower()
    ids = [t for t in (tasks or TASKS) if t in TASKS]
    out, fb = {}, {}
    for t in ids:
        kw = TASKS[t]
        ok = kw in low
        out[t] = 1.0 if ok else 0.0
        if not ok:
            fb[t] = f"missing keyword '{kw}'"
    return {"tasks": out, "tokens": len(text) // 4, "feedback": fb}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--tasks", default="")
    args = ap.parse_args(argv)
    text = Path(args.target).read_text(encoding="utf-8", errors="replace")
    tasks = [t for t in args.tasks.split(",") if t.strip()] or None
    sys.stdout.write(json.dumps(score(text, tasks)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
