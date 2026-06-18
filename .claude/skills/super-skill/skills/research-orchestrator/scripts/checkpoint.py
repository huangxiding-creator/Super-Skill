"""Checkpoint / resume for research-orchestrator (IdeaForge / Super-Skill V4.0).

Persists per-stage state as JSON so a crashed/halted research run resumes from the
last completed stage instead of re-harvesting. Ports the ResearchFactory idea.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List

STAGES = ("intake", "research", "gap_analysis", "digest", "proposal")


@dataclass
class Checkpoint:
    topic: str
    completed_stages: List[str] = field(default_factory=list)
    channel_counts: Dict[str, int] = field(default_factory=dict)
    notes: str = ""

    def mark(self, stage: str, **extra) -> None:
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        for k, v in extra.items():
            if k == "channel_counts":
                self.channel_counts.update(v)

    def is_done(self, stage: str) -> bool:
        return stage in self.completed_stages

    def next_stage(self) -> "str | None":
        for s in STAGES:
            if not self.is_done(s):
                return s
        return None


def path_for(docket_dir: str) -> str:
    return os.path.join(docket_dir, "_checkpoint.json")


def save(docket_dir: str, cp: Checkpoint) -> str:
    os.makedirs(docket_dir, exist_ok=True)
    p = path_for(docket_dir)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(asdict(cp), f, ensure_ascii=False, indent=2)
    return p


def load(docket_dir: str, topic: str = "") -> Checkpoint:
    p = path_for(docket_dir)
    if not os.path.exists(p):
        return Checkpoint(topic=topic)
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Checkpoint(
            topic=data.get("topic", topic),
            completed_stages=list(data.get("completed_stages", [])),
            channel_counts=dict(data.get("channel_counts", {})),
            notes=data.get("notes", ""),
        )
    except (OSError, ValueError):
        return Checkpoint(topic=topic)
