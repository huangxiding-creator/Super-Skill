"""Research orchestrator (IdeaForge / Super-Skill V4.0) — Stage 2 of the Idea Factory.

Runs enabled channels against an IDEA_SEED, normalizes to :class:`Doc`, persists a
per-channel docket, dedups across channels, and writes RESEARCH_DIGEST.md. Ports the
ResearchFactory-Eng orchestration shape (channel dispatch → normalize → dedup → quality
note → checkpoint) but with software-product channels instead of EPC ones.

Pure-Python, stdlib-only, network-injectable for tests. Never aborts the whole run on a
single channel failure: it records the failure and continues.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional

# allow running both as `python orchestrator.py` (cwd=scripts) and as a module
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from channels.base import Channel, Doc, HttpFunc, real_http  # noqa: E402
from channels import REGISTRY  # noqa: E402
from channels.github import ChannelGitHub  # noqa: E402
from channels.sogou_wechat import ChannelSogouWechat  # noqa: E402
import checkpoint as ckpt  # noqa: E402
from deduper import dedupe  # noqa: E402

# Channels enabled by default in M1. M3 adds the rest.
DEFAULT_CHANNELS = ("github", "sogou_wechat")


@dataclass
class ChannelRun:
    name: str
    ok: bool
    count: int
    error: str = ""


@dataclass
class OrchestratorReport:
    topic: str
    docket_dir: str
    per_channel: List[ChannelRun] = field(default_factory=list)
    total_raw: int = 0
    unique: int = 0
    duplicates: int = 0
    degraded: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


def _build_channels(names: List[str], http: Optional[HttpFunc]) -> List[Channel]:
    channels: List[Channel] = []
    for n in names:
        cls = REGISTRY.get(n)
        if cls is None:
            continue
        channels.append(cls(http=http) if http is not None else cls())
    return channels


def _persist_channel(docket_dir: str, name: str, docs: List[Doc]) -> None:
    ch_dir = os.path.join(docket_dir, name)
    os.makedirs(ch_dir, exist_ok=True)
    # write one combined markdown per channel for LLM consumption
    lines = [f"# Channel: {name} ({len(docs)} docs)\n"]
    for i, d in enumerate(docs, 1):
        lines.append(f"## {i}. {d.title}\n")
        lines.append(f"- type: `{d.doc_type}` | url: {d.url} | credibility: {d.credibility}\n")
        if d.signals:
            lines.append(f"- signals: `{json.dumps(d.signals, ensure_ascii=False)}`\n")
        if d.content:
            lines.append(f"\n{d.content[:2000]}\n")
        lines.append("")
    with open(os.path.join(ch_dir, "_all.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # also raw json for downstream scorers
    with open(os.path.join(ch_dir, "_all.json"), "w", encoding="utf-8") as f:
        json.dump([d.to_dict() for d in docs], f, ensure_ascii=False, indent=2)


def _write_digest(docket_dir: str, report: OrchestratorReport, unique: List[Doc]) -> str:
    path = os.path.join(docket_dir, "RESEARCH_DIGEST.md")
    by_ch: Dict[str, int] = {}
    for d in unique:
        by_ch[d.channel] = by_ch.get(d.channel, 0) + 1
    lines = [
        f"# RESEARCH DIGEST — {report.topic}\n",
        f"- raw docs: {report.total_raw} | unique: {report.unique} | dupes dropped: {report.duplicates}",
        f"- degraded channels: {', '.join(report.degraded) or 'none'}\n",
        "## Per-channel unique counts\n",
    ]
    for cr in report.per_channel:
        flag = " (DEGRADED)" if cr.name in report.degraded else ""
        lines.append(f"- **{cr.name}**: {by_ch.get(cr.name, 0)} unique{flag} — {cr.error or 'ok'}")
    lines.append("\n## Top repos / solutions (by credibility × stars)\n")
    repos = [d for d in unique if d.doc_type == "repo"]
    repos.sort(key=lambda d: (d.credibility, d.signals.get("stars", 0)), reverse=True)
    for d in repos[:15]:
        s = d.signals
        lines.append(f"- [{d.title}]({d.url}) — ⭐{s.get('stars',0)} 🍴{s.get('forks',0)} "
                     f"issues:{s.get('open_issues',0)} lang:{s.get('language','?')} "
                     f"license:{s.get('license','?')} updated:{s.get('updated_at','?')[:10]}")
    if not repos:
        lines.append("- (no repo docs harvested)")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def orchestrate(
    seed: Dict,
    docket_dir: str,
    channels: Optional[List[str]] = None,
    http: Optional[HttpFunc] = None,
    resume: bool = True,
) -> OrchestratorReport:
    """Run the research stage end-to-end. Idempotent-ish: re-runs overwrite docket."""
    topic = seed.get("summary") or seed.get("topic") or "untitled"
    names = list(channels or DEFAULT_CHANNELS)
    report = OrchestratorReport(topic=topic, docket_dir=docket_dir)
    os.makedirs(docket_dir, exist_ok=True)

    cp = ckpt.load(docket_dir, topic=topic) if resume else ckpt.Checkpoint(topic=topic)
    cp.topic = topic

    ch_objs = _build_channels(names, http)
    all_docs: List[Doc] = []
    for ch in ch_objs:
        try:
            docs = ch.harvest(seed)
            ok = True
            err = ""
        except Exception as e:  # never let one channel kill the run
            docs, ok, err = [], False, f"{type(e).__name__}: {e}"
        degraded = any(d.doc_type == "degraded" for d in docs)
        if degraded:
            report.degraded.append(ch.name)
            err = err or "degraded"
        _persist_channel(docket_dir, ch.name, docs)
        all_docs.extend(docs)
        report.per_channel.append(ChannelRun(name=ch.name, ok=ok, count=len(docs), error=err))

    report.total_raw = len(all_docs)
    # drop degraded notes before dedup so they don't pollute uniqueness
    real_docs = [d for d in all_docs if d.doc_type != "degraded"]
    res = dedupe(real_docs)
    report.unique = len(res.unique)
    report.duplicates = res.duplicates

    _write_digest(docket_dir, report, res.unique)
    cp.mark("research", channel_counts={cr.name: cr.count for cr in report.per_channel})
    ckpt.save(docket_dir, cp)
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _read_seed(path: str) -> Dict:
    if path == "-":
        return json.loads(sys.stdin.read())
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    return json.loads(txt) if txt.strip().startswith("{") else {"summary": txt.strip()}


def main(argv: List[str]) -> int:
    if len(argv) < 3:
        sys.stderr.write("usage: orchestrator.py <seed.json|-> <docket_dir> [ch1,ch2,...]\n")
        return 2
    seed = _read_seed(argv[1])
    docket = argv[2]
    chans = argv[3].split(",") if len(argv) > 3 else None
    rep = orchestrate(seed, docket, channels=chans)
    print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
