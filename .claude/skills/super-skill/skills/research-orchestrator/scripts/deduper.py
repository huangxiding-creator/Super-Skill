"""Dedup for research-orchestrator (IdeaForge / Super-Skill V4.0).

Two-layer dedup, porting the ResearchFactory-Eng idea:
1. Title normalization (see base.normalize_title) — catches re-posts / mirrors.
2. Content hash (SHA1 of normalized text) — catches same-content, different-title.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from channels.base import Doc, normalize_title


def content_hash(text: str) -> str:
    if not text:
        return ""
    # collapse whitespace + lowercase so cosmetic diffs don't dodge dedup
    t = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class DedupResult:
    unique: List[Doc]
    duplicates: int
    by_title: int
    by_hash: int


def dedupe(docs: List[Doc]) -> DedupResult:
    """Return unique docs + counts of how many were dropped. Stable (keeps first)."""
    seen_titles: Dict[str, int] = {}
    seen_hash: Dict[str, int] = {}
    unique: List[Doc] = []
    by_title = by_hash = 0
    for d in docs:
        tkey = normalize_title(d.title)
        hkey = content_hash(d.content)
        if tkey and tkey in seen_titles:
            by_title += 1
            continue
        if hkey and hkey in seen_hash:
            by_hash += 1
            continue
        if tkey:
            seen_titles[tkey] = 1
        if hkey:
            seen_hash[hkey] = 1
        unique.append(d)
    return DedupResult(unique=unique, duplicates=by_title + by_hash,
                       by_title=by_title, by_hash=by_hash)
