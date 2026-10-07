#!/usr/bin/env python3
"""Requirement -> task -> test traceability matrix + EARS lint (W3).

Borrowed patterns: spec-kit stable ``FR-###`` IDs + coverage table (MIT),
cc-sdd EARS format + ``_Requirements:`` annotations (MIT), Kiro EARS
acceptance criteria (pattern only).

Requirement lines in ``REQUIREMENTS.md`` look like::

    - REQ-001 [MUST]: When a user submits the form, the system shall persist it.
      - REQ-001.AC1: Given a valid form, the record appears in the list.
    ### REQ-002 (SHOULD) 当用户离线时，系统应缓存草稿

Priority defaults to MUST. Tasks cover requirements via ``covers`` in
``.super-skill/tasks.json``; tests cover them by mentioning the ID (``REQ-001``
or ``req_001``) anywhere in a test file.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import force_utf8_stdio, load_state, now_iso, sdir, write_json_atomic  # noqa: E402
import taskgraph  # noqa: E402

REQ_ID = re.compile(r"\bREQ-(\d{3,})(?:\.AC(\d+))?\b")
_REQ_DEF = re.compile(
    r"^\s*(?:#{1,6}\s*|[-*+]\s*|\|\s*|\d+[.)]\s*)?\**\s*(REQ-\d{3,}(?:\.AC\d+)?)\s*\**"
    r"\s*(?:[\[(（【]\s*(MUST|SHOULD|COULD|WON'?T|MAY)\s*[\])）】])?\s*[:：\-—|]?\s*(.*)$",
    re.IGNORECASE)
# no \b: in test names like ``test_req_001_ac1`` the "_" before REQ is a word char
_TEST_ID = re.compile(r"(?i)(?<![A-Za-z0-9])REQ[-_](\d{3,})(?:[._]AC(\d+))?")
_EARS = [
    re.compile(r"(?i)\b(when|while|if|where)\b.*\bshall\b"),
    re.compile(r"(?i)^\s*the\b.*\bshall\b"),
    re.compile(r"(?i)\bshall\b"),
    re.compile(r"(当|在|如果|若|假如).*(应|应当|必须|须)"),
    re.compile(r"(系统|服务|应用|平台|模块|用户界面|接口).{0,20}(应|应当|必须|须)"),
]
DEFAULT_TEST_GLOBS = ["tests/**/*", "test/**/*", "**/test_*.*", "**/*_test.*",
                      "**/*.test.*", "**/*.spec.*"]
_SKIP_DIRS = {".git", "node_modules", ".super-skill", ".venv", "venv", "__pycache__",
              "dist", "build", ".next"}


def parse_requirements(path: Path) -> list[dict]:
    """Return requirement and acceptance-criterion records in document order."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    reqs: dict[str, dict] = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        m = _REQ_DEF.match(line)
        if not m:
            continue
        rid = m.group(1).upper()
        if rid in reqs:
            continue
        prio = (m.group(2) or "").upper().replace("'", "")
        body = m.group(3).strip()
        if not prio:
            pm = re.search(r"(?i)\b(MUST|SHOULD|COULD|WONT|WON'T)\b|可选|建议", body)
            prio = {"可选": "COULD", "建议": "SHOULD"}.get(pm.group(0), pm.group(0).upper().replace("'", "")) if pm else "MUST"
        is_ac = ".AC" in rid
        parent = rid.split(".")[0] if is_ac else None
        if is_ac and parent in reqs:
            prio = reqs[parent]["priority"]
        reqs[rid] = {"id": rid, "priority": prio, "text": body, "line": lineno,
                     "is_ac": is_ac, "parent": parent}
    return list(reqs.values())


def ears_ok(text: str) -> bool:
    return any(p.search(text) for p in _EARS)


def ears_lint(path: Path) -> dict:
    reqs = [r for r in parse_requirements(path) if not r["is_ac"]]
    bad = [r for r in reqs if not ears_ok(r["text"])]
    return {"ok": bool(reqs) and not bad, "checked": len(reqs),
            "violations": [{"id": r["id"], "line": r["line"], "text": r["text"][:120]} for r in bad]}


def _glob_match(rel: str, pattern: str) -> bool:
    """fnmatch where ``**/`` may also match zero directories."""
    return fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, pattern.replace("**/", ""))


def _iter_files(root: Path, globs: list[str], max_bytes: int = 512_000):
    seen = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            full = Path(dirpath) / name
            rel = full.relative_to(root).as_posix()
            if rel in seen:
                continue
            if any(_glob_match(rel, g) for g in globs):
                seen.add(rel)
                try:
                    if full.stat().st_size <= max_bytes:
                        yield rel, full
                except OSError:
                    continue


def scan_tests(root: Path, globs: list[str] | None = None) -> dict[str, list[str]]:
    """Map REQ id (and REQ.ACn) -> test files mentioning it."""
    hits: dict[str, set] = {}
    for rel, full in _iter_files(root, globs or DEFAULT_TEST_GLOBS):
        try:
            text = full.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in _TEST_ID.finditer(text):
            rid = f"REQ-{m.group(1)}"
            hits.setdefault(rid, set()).add(rel)
            if m.group(2):
                hits.setdefault(f"{rid}.AC{m.group(2)}", set()).add(rel)
    return {k: sorted(v) for k, v in hits.items()}


def build(root: Path, req_path: Path | None = None, require: str = "tasks",
          test_globs: list[str] | None = None, write: bool = True) -> dict:
    """Build the matrix. ``require``: ``tasks`` (P6 gate) or ``tests`` (P9 gate)."""
    root = Path(root)
    state = load_state(root)
    cfg = state.get("config", {}) if state else {}
    req_path = req_path or root / cfg.get("requirements_file", "REQUIREMENTS.md")
    reqs = parse_requirements(req_path)
    known = {r["id"] for r in reqs}
    tasks = taskgraph.load(root)["tasks"]
    tests = scan_tests(root, test_globs or cfg.get("test_globs"))

    by_req: dict[str, list[str]] = {}
    orphans = []
    for t in tasks:
        if t.get("status") == "dropped":
            continue
        covers = [c.upper() for c in t.get("covers", [])]
        valid = [c for c in covers if c in known or c.split(".")[0] in known]
        if not valid:
            orphans.append({"id": t["id"], "covers": covers,
                            "reason": "no covers" if not covers else "unknown requirement id"})
        for c in valid:
            by_req.setdefault(c, []).append(t["id"])
            if "." in c:
                by_req.setdefault(c.split(".")[0], []).append(t["id"])

    rows = []
    for r in reqs:
        rid = r["id"]
        row_tasks = sorted(set(by_req.get(rid, [])))
        row_tests = tests.get(rid, [])
        if not r["is_ac"]:
            # a requirement is test-covered if any of its ACs is
            row_tests = sorted(set(row_tests) | {f for k, v in tests.items()
                                                 if k.startswith(rid + ".") for f in v})
        rows.append({**r, "tasks": row_tasks, "tests": row_tests,
                     "ears_ok": True if r["is_ac"] else ears_ok(r["text"])})

    top = [r for r in rows if not r["is_ac"] and r["priority"] == "MUST"]
    cov_tasks = sum(1 for r in top if r["tasks"]) / len(top) if top else 0.0
    cov_tests = sum(1 for r in top if r["tests"]) / len(top) if top else 0.0
    problems = []
    if not reqs:
        problems.append(f"no REQ-### ids found in {Path(req_path).name}")
    for r in top:
        if not r["tasks"]:
            problems.append(f"{r['id']} has no task")
        if require == "tests" and not r["tests"]:
            problems.append(f"{r['id']} has no test")
    for o in orphans:
        problems.append(f"orphan task {o['id']} ({o['reason']})")
    result = {"ts": now_iso(), "require": require, "requirements_file": str(req_path),
              "reqs": rows, "orphans": orphans,
              "coverage": {"tasks": round(cov_tasks, 3), "tests": round(cov_tests, 3),
                           "must_count": len(top)},
              "problems": problems, "ok": not problems}
    if write and sdir(root).is_dir():
        write_json_atomic(sdir(root) / "trace.json", result)
        (sdir(root) / "trace.md").write_text(render_md(result), encoding="utf-8")
    return result


def render_md(result: dict) -> str:
    cov = result["coverage"]
    lines = ["# Traceability Matrix", "",
             f"- generated: {result['ts']} · require: `{result['require']}`",
             f"- MUST coverage — tasks: {cov['tasks']:.0%} · tests: {cov['tests']:.0%} "
             f"({cov['must_count']} MUST requirements)",
             f"- verdict: {'✅ PASS' if result['ok'] else '❌ FAIL'}", "",
             "| REQ | Priority | EARS | Tasks | Tests |", "|---|---|---|---|---|"]
    for r in result["reqs"]:
        indent = "↳ " if r["is_ac"] else ""
        lines.append(f"| {indent}{r['id']} | {r['priority']} | {'✓' if r['ears_ok'] else '✗'} | "
                     f"{', '.join(r['tasks']) or '—'} | {', '.join(r['tests'][:3]) or '—'} |")
    if result["problems"]:
        lines += ["", "## Problems", ""] + [f"- {p}" for p in result["problems"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="trace_matrix", description="REQ -> task -> test matrix")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--require", choices=("tasks", "tests"), default="tasks")
    b.add_argument("--requirements")
    b.add_argument("--json", action="store_true")
    e = sub.add_parser("ears")
    e.add_argument("path", nargs="?", default="REQUIREMENTS.md")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if args.cmd == "ears":
        res = ears_lint(root / args.path)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1
    res = build(root, Path(args.requirements) if args.requirements else None, args.require)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render_md(res), end="")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
