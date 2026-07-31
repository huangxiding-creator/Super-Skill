"""Rationale miner (ai-mastery-7, Discipline 3).

Surfaces the **why** behind the current state of a file or path. A bare technique
is mechanical; understanding "what problem this solved, when it was introduced,
and what's been drifting lately" is real understanding. Boris Cherny: "理解历史，
才能理解为什么".

Given a path it walks git history to produce a rationale timeline:
- **Origin**            — when + why the path first appeared (first commit subject)
- **Formative changes**  — highest-impact commits (top N by churn), each with its stated rationale
- **Recent drift**      — last few commits, so you see what's changing now
- **Segment map**       — (single file only) `git blame` grouped into runs, linking each
                          region of the CURRENT file to the commit + message that last shaped it

Pure stdlib, offline, deterministic. The agent's job is to interpret the timeline
into "conditions where this still holds / breaks"; this script only produces the
honest source material.

Usage:
    python rationale_mining.py src/auth.py
    python rationale_mining.py src/auth.py --max 5
    python rationale_mining.py src/auth.py --json
    python rationale_mining.py --repo /path path/to/dir
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import List

SENTINEL = "__COMMIT__"
NUMSTAT_RE = re.compile(r"^(\d+|-)\t(\d+|-)\t(.+)$")
_BLAME_KEYS = {
    "author", "author-mail", "author-time", "author-tz",
    "committer", "committer-mail", "committer-time", "committer-tz",
    "summary", "filename", "boundary",
}


@dataclass
class Change:
    hash: str
    date: str
    author: str
    subject: str
    insertions: int = 0
    deletions: int = 0

    @property
    def churn(self) -> int:
        return self.insertions + self.deletions


def _run_git(args: List[str], repo: str) -> str:
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


def _parse_log(raw: str) -> List[Change]:
    """Parse SENTINEL-delimited log + --numstat (single path scope)."""
    changes: List[Change] = []
    cur: Change | None = None
    for line in raw.splitlines():
        if line.startswith(SENTINEL):
            if cur is not None:
                changes.append(cur)
            h, date, author, subject = line[len(SENTINEL):].split("|", 3)
            cur = Change(hash=h, date=date, author=author, subject=subject)
        elif cur is not None:
            m = NUMSTAT_RE.match(line)
            if m:
                ins = 0 if m.group(1) == "-" else int(m.group(1))
                dele = 0 if m.group(2) == "-" else int(m.group(2))
                cur.insertions += ins
                cur.deletions += dele
    if cur is not None:
        changes.append(cur)
    return changes


def history(repo: str, path: str) -> List[Change]:
    """All commits touching `path`, oldest→newest. Uses --follow for single files."""
    follow = [] if os.path.isdir(os.path.join(repo, path)) else ["--follow"]
    fmt = f"{SENTINEL}%H|%aI|%an|%s"
    raw = _run_git(
        ["log", *follow, f"--pretty=tformat:{fmt}", "--numstat", "--", path], repo,
    )
    return list(reversed(_parse_log(raw)))  # oldest first


def blame_segments(repo: str, path: str) -> List[dict]:
    """Group `git blame --line-porcelain` into runs by the commit that last touched each line.

    Returns [{hash, subject, author, start, end}], ordered by position. Single-file only.
    """
    raw = _run_git(["blame", "--line-porcelain", "--", path], repo)
    summaries: dict[str, str] = {}
    authors: dict[str, str] = {}
    line_hashes: List[str] = []
    cur_hash: str | None = None
    for line in raw.splitlines():
        if not line:
            continue
        if line.startswith("\t"):  # the source line itself
            line_hashes.append(cur_hash or "")
            continue
        head = line.split(" ", 1)[0]
        if head not in _BLAME_KEYS:
            cur_hash = head  # header line: "<hash> <orig-line> <final-line>"
        elif head == "summary" and cur_hash:
            summaries.setdefault(cur_hash, line[len("summary "):])
        elif head == "author" and cur_hash:
            authors.setdefault(cur_hash, line[len("author "):])

    runs: List[dict] = []
    idx = 0
    while idx < len(line_hashes):
        h = line_hashes[idx]
        start = idx + 1
        j = idx
        while j < len(line_hashes) and line_hashes[j] == h:
            j += 1
        runs.append({
            "hash": (h or "")[:8],
            "subject": summaries.get(h, "(no summary)"),
            "author": authors.get(h, "?"),
            "start": start,
            "end": j,  # 1-based inclusive
        })
        idx = j
    return runs


def build_report(repo: str, path: str, max_formative: int) -> dict:
    try:
        changes = history(repo, path)
    except RuntimeError as e:
        # No commits at all, unreadable path, etc. — report gracefully, don't crash.
        return {"path": path, "error": f"no git history for this path ({e})"}
    if not changes:
        return {"path": path, "error": "no git history for this path"}

    origin = changes[0]
    recent = list(reversed(changes[-5:]))  # most recent first, up to 5
    formative = sorted(changes, key=lambda c: c.churn, reverse=True)[:max_formative]

    report: dict = {
        "path": path,
        "total_commits": len(changes),
        "origin": {"hash": origin.hash[:8], "date": origin.date[:10],
                   "author": origin.author, "subject": origin.subject},
        "formative": [
            {"hash": c.hash[:8], "date": c.date[:10], "author": c.author,
             "subject": c.subject, "insertions": c.insertions, "deletions": c.deletions}
            for c in formative
        ],
        "recent_drift": [
            {"hash": c.hash[:8], "date": c.date[:10], "subject": c.subject}
            for c in recent
        ],
    }

    if os.path.isfile(os.path.join(repo, path)):
        try:
            report["segments"] = blame_segments(repo, path)
        except RuntimeError:
            report["segments"] = []  # blame can fail on binary / empty files
    return report


def render_markdown(report: dict) -> str:
    if report.get("error"):
        return f"# Rationale: {report['path']}\n\n_{report['error']}_\n"
    out: List[str] = [f"# Rationale timeline — `{report['path']}`", ""]
    o = report["origin"]
    out.append("## Origin (why it first appeared)")
    out.append(f"- `{o['hash']}` {o['date']} — **{o['subject']}**  ·  _{o['author']}_")
    out.append("")
    out.append(f"## Formative changes (top {len(report['formative'])} by impact)")
    for c in report["formative"]:
        out.append(f"- `{c['hash']}` {c['date']} — **{c['subject']}**"
                   f"  ·  +{c['insertions']}/-{c['deletions']}")
    out.append("")
    out.append("## Recent drift")
    for c in report["recent_drift"]:
        out.append(f"- `{c['hash']}` {c['date']} — {c['subject']}")
    if report.get("segments"):
        out.append("")
        out.append("## Current-file segment map (who last shaped each region)")
        for s in report["segments"]:
            out.append(f"- L{s['start']}–L{s['end']}  `{s['hash']}` {s['subject']}  ·  _{s['author']}_")
    out.append("")
    out.append("> Interpret: for each formative change, ask — what problem did this "
               "solve? Under what conditions does it still hold? When does it break?")
    return "\n".join(out) + "\n"


def _force_utf8_stdout() -> None:
    """Force UTF-8 stdout/stderr so non-ASCII output isn't GBK-mangled on Windows pipes."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: List[str] | None = None) -> int:
    _force_utf8_stdout()
    p = argparse.ArgumentParser(description="Mine the rationale behind a path's current state.")
    p.add_argument("path", help="file or directory to explain")
    p.add_argument("--repo", default=".", help="repository path (default: CWD)")
    p.add_argument("--max", type=int, default=5, help="top-N formative commits (default: 5)")
    p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = p.parse_args(argv)

    try:
        report = build_report(args.repo, args.path, args.max)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
