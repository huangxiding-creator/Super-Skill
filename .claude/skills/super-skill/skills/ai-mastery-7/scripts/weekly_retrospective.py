"""Weekly retrospective generator (ai-mastery-7, Discipline 4).

Turns `git log` for a date range into a clear weekly report:
- Delivered      — completed-looking commits (feat/fix/perf/refactor/release)
- In progress    — WIP / draft / partial work
- Scope signals  — oversized commits (many files or huge diff) that may indicate
                   a task ran larger than expected, plus high-churn paths.

Pure stdlib, offline, deterministic. The agent's job is to *interpret* the report;
this script only turns git into a structured, honest list — "把模糊的感觉变成清晰的清单".

Usage:
    python weekly_retrospective.py                      # this week (7 days), CWD repo
    python weekly_retrospective.py --since 14           # last 14 days
    python weekly_retrospective.py --area src --area tests
    python weekly_retrospective.py --json               # machine-readable
    python weekly_retrospective.py --repo /path/to/repo
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Tuple

SENTINEL = "__COMMIT__"
DELIVERED_RE = re.compile(r"^\s*(feat|fix|perf|refactor|release|test|docs|chore)(\([^)]*\))?!?:", re.I)
WIP_RE = re.compile(r"\b(wip|draft|todo|fixme|in-?progress|part(ial)?)\b", re.I)
NUMSTAT_RE = re.compile(r"^(\d+|-)\t(\d+|-)\t(.+)$")

# A commit is a "scope signal" if it touches more than this many files OR net churn exceeds this.
SCOPE_FILE_THRESHOLD = 10
SCOPE_CHURN_THRESHOLD = 300


@dataclass
class Commit:
    hash: str
    date: str          # ISO 8601 from git (%aI)
    author: str
    subject: str
    files: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0

    @property
    def churn(self) -> int:
        return self.insertions + self.deletions

    @property
    def category(self) -> str:
        if WIP_RE.search(self.subject):
            return "in_progress"
        if DELIVERED_RE.match(self.subject):
            return "delivered"
        # Subject with no conventional prefix: treat as delivered-ish work unless clearly partial
        return "delivered"

    @property
    def is_scope_signal(self) -> bool:
        if len(self.files) > SCOPE_FILE_THRESHOLD:
            return True
        if self.churn > SCOPE_CHURN_THRESHOLD:
            return True
        return False


def _run_git(args: List[str], repo: str) -> str:
    """Run git, return stdout. Raise with a friendly message on failure."""
    try:
        r = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60, check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("git executable not found on PATH")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git failed: {(e.stderr or '').strip() or e}")
    return r.stdout


def _parse_commits(raw: str) -> List[Commit]:
    """Parse `git log` output produced with our SENTINEL format + --numstat."""
    commits: List[Commit] = []
    cur: Commit | None = None
    for line in raw.splitlines():
        if line.startswith(SENTINEL):
            if cur is not None:
                commits.append(cur)
            h, date, author, subject = line[len(SENTINEL):].split("|", 3)
            cur = Commit(hash=h, date=date, author=author, subject=subject)
        elif cur is not None:
            m = NUMSTAT_RE.match(line)
            if m:
                ins = 0 if m.group(1) == "-" else int(m.group(1))
                dele = 0 if m.group(2) == "-" else int(m.group(2))
                path = m.group(3)
                cur.insertions += ins
                cur.deletions += dele
                cur.files.append(path)
    if cur is not None:
        commits.append(cur)
    return commits


def collect(repo: str, since_days: int, areas: Tuple[str, ...]) -> List[Commit]:
    """Return commits in the last `since_days` days, optionally limited to `areas`."""
    fmt = f"{SENTINEL}%H|%aI|%an|%s"
    args = ["log", f"--since={since_days}.days", f"--pretty=tformat:{fmt}", "--numstat"]
    if areas:
        args.append("--")
        args.extend(areas)
    raw = _run_git(args, repo)
    return _parse_commits(raw)


def summarize(commits: List[Commit]) -> dict:
    """Group commits into the retrospective sections."""
    delivered = [c for c in commits if c.category == "delivered"]
    in_progress = [c for c in commits if c.category == "in_progress"]
    scope_signals = [c for c in commits if c.is_scope_signal]

    # High-churn paths: files touched by >=3 commits this week.
    file_counts: dict[str, int] = defaultdict(int)
    for c in commits:
        for f in c.files:
            file_counts[f] += 1
    hotspots = sorted(
        ({"path": p, "commits": n} for p, n in file_counts.items() if n >= 3),
        key=lambda x: x["commits"], reverse=True,
    )[:10]

    by_day: dict[str, int] = defaultdict(int)
    for c in commits:
        day = c.date[:10]  # YYYY-MM-DD
        by_day[day] += 1

    return {
        "range_days": None,  # filled by caller
        "totals": {
            "commits": len(commits),
            "delivered": len(delivered),
            "in_progress": len(in_progress),
            "authors": len({c.author for c in commits}),
        },
        "by_day": dict(sorted(by_day.items())),
        "delivered": [{"hash": c.hash[:8], "subject": c.subject, "date": c.date[:10]} for c in delivered],
        "in_progress": [{"hash": c.hash[:8], "subject": c.subject, "date": c.date[:10]} for c in in_progress],
        "scope_signals": [
            {"hash": c.hash[:8], "subject": c.subject, "files": len(c.files), "churn": c.churn}
            for c in scope_signals
        ],
        "hotspots": hotspots,
    }


def render_markdown(report: dict) -> str:
    lines: List[str] = []
    t = report["totals"]
    lines.append(f"# Weekly Retrospective — {report['range_days']} days")
    lines.append("")
    lines.append(
        f"_{t['commits']} commits · {t['delivered']} delivered · "
        f"{t['in_progress']} in-progress · {t['authors']} author(s)_"
    )
    lines.append("")
    lines.append("## Delivered")
    for c in report["delivered"]:
        lines.append(f"- `{c['hash']}` {c['subject']}")
    if not report["delivered"]:
        lines.append("_Nothing landed as delivered this week._")
    lines.append("")
    lines.append("## In progress")
    for c in report["in_progress"]:
        lines.append(f"- `{c['hash']}` {c['subject']}")
    if not report["in_progress"]:
        lines.append("_No explicit WIP/draft markers found._")
    lines.append("")
    lines.append("## Scope signals (larger-than-expected?)")
    for c in report["scope_signals"]:
        lines.append(f"- `{c['hash']}` {c['subject']} — {c['files']} files, {c['churn']} churn")
    if not report["scope_signals"]:
        lines.append("_No oversized commits._")
    if report["hotspots"]:
        lines.append("")
        lines.append("## Hotspots (touched ≥3× this week)")
        for h in report["hotspots"]:
            lines.append(f"- `{h['path']}` — {h['commits']} commits")
    return "\n".join(lines) + "\n"


def _force_utf8_stdout() -> None:
    """Force UTF-8 stdout/stderr so non-ASCII output isn't GBK-mangled on Windows pipes."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: List[str] | None = None) -> int:
    _force_utf8_stdout()
    p = argparse.ArgumentParser(description="Weekly retrospective from git log.")
    p.add_argument("--repo", default=".", help="repository path (default: CWD)")
    p.add_argument("--since", type=int, default=7, help="days to look back (default: 7)")
    p.add_argument("--area", action="append", default=[], help="limit to path(s); repeatable")
    p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = p.parse_args(argv)

    try:
        commits = collect(args.repo, args.since, tuple(args.area))
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    report = summarize(commits)
    report["range_days"] = args.since
    report["generated_at"] = dt.datetime.now().astimezone().isoformat()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
