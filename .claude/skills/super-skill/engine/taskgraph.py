#!/usr/bin/env python3
"""Dependency-aware task graph for Super-Skill (W3).

Patterns borrowed from steveyegge/beads (``ready`` queue, atomic claim, MIT)
and Task Master (complexity analysis, pattern only). Storage is
``<project>/.super-skill/tasks.json``::

    {"schema_version": "1.0", "tasks": [
      {"id": "T-001", "title": "...", "covers": ["REQ-001.AC1"],
       "after": ["T-000"], "files": ["src/a.py"], "verify": "pytest -q",
       "status": "pending", "complexity": 3, "attempts": 0,
       "claimed_by": null, "claimed_at": null, "done_at": null, "notes": ""}]}

A task is *ready* when it is ``pending`` and every task in ``after`` is
``done`` or ``dropped``.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    force_utf8_stdio, ledger, now_iso, read_json, sdir, write_json_atomic,
)

STATUSES = ("pending", "in_progress", "review", "done", "blocked", "dropped")
FINISHED = ("done", "dropped")
MAX_ATTEMPTS = 3
SPLIT_THRESHOLD = 5
_RISKY = re.compile(
    r"(?i)refactor|migrat|auth|security|concurren|distributed|payment|schema|"
    r"重构|迁移|鉴权|安全|并发|分布式|支付")


# ---------------------------------------------------------------- storage

def tasks_path(root: Path) -> Path:
    return sdir(root) / "tasks.json"


def load(root: Path) -> dict:
    data = read_json(tasks_path(root), default=None)
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        data = {"schema_version": "1.0", "tasks": []}
    return data


def save(root: Path, data: dict) -> None:
    write_json_atomic(tasks_path(root), data)


class _Lock:
    """Cross-process lock via O_EXCL lockfile; stale after ``stale_s``."""

    def __init__(self, root: Path, timeout: float = 10.0, stale_s: float = 60.0):
        self.path = sdir(root) / "tasks.lock"
        self.timeout, self.stale_s = timeout, stale_s

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale_s:
                        self.path.unlink()
                        continue
                except OSError:
                    continue
                if time.monotonic() > deadline:
                    raise TimeoutError(f"task graph locked: {self.path}")
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            self.path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- model

def _by_id(tasks: list[dict]) -> dict[str, dict]:
    return {t["id"]: t for t in tasks}


def _next_id(tasks: list[dict]) -> str:
    nums = [int(m.group(1)) for t in tasks if (m := re.match(r"T-(\d+)$", t.get("id", "")))]
    return f"T-{(max(nums) + 1) if nums else 1:03d}"


def normalize(task: dict) -> dict:
    task.setdefault("title", "")
    for key in ("covers", "after", "files"):
        val = task.get(key) or []
        task[key] = [v.strip() for v in (val.split(",") if isinstance(val, str) else val) if str(v).strip()]
    task.setdefault("verify", "")
    task["status"] = task.get("status") if task.get("status") in STATUSES else "pending"
    task.setdefault("attempts", 0)
    task.setdefault("notes", "")
    for key in ("claimed_by", "claimed_at", "done_at"):
        task.setdefault(key, None)
    if not task.get("complexity"):
        task["complexity"] = estimate_complexity(task)
    return task


def estimate_complexity(task: dict) -> int:
    """Heuristic 1-10 score; >5 means "split before implementing"."""
    score = 1.0
    score += 0.8 * len(task.get("files") or [])
    score += 0.5 * len(task.get("covers") or [])
    text = f"{task.get('title', '')} {task.get('notes', '')}"
    if _RISKY.search(text):
        score += 2
    score += min(2.0, len(text) / 200)
    if not task.get("verify"):
        score += 1  # unverifiable work is riskier
    return max(1, min(10, round(score)))


def ready(tasks: list[dict]) -> list[dict]:
    idx = _by_id(tasks)
    out = []
    for t in tasks:
        if t.get("status") != "pending":
            continue
        if all(idx.get(d, {}).get("status") in FINISHED for d in t.get("after", [])):
            out.append(t)
    return out


def waves(tasks: list[dict]) -> list[list[str]]:
    """Kahn layering of unfinished tasks into parallelizable waves."""
    idx = _by_id(tasks)
    remaining = {t["id"] for t in tasks if t.get("status") not in FINISHED}
    done = {t["id"] for t in tasks if t.get("status") in FINISHED}
    result = []
    while remaining:
        layer = sorted(
            tid for tid in remaining
            if all(d in done or d not in idx for d in idx[tid].get("after", []))
        )
        if not layer:  # cycle — report the rest as one unresolved wave
            result.append(sorted(remaining))
            break
        result.append(layer)
        remaining -= set(layer)
        done |= set(layer)
    return result


def validate(tasks: list[dict]) -> dict:
    errors, warnings = [], []
    seen = set()
    for t in tasks:
        tid = t.get("id")
        if not tid:
            errors.append("task without id")
            continue
        if tid in seen:
            errors.append(f"duplicate id {tid}")
        seen.add(tid)
    idx = _by_id(tasks)
    for t in tasks:
        for dep in t.get("after", []):
            if dep not in idx:
                errors.append(f"{t['id']}: unknown dependency {dep}")
        if not t.get("covers"):
            warnings.append(f"{t['id']}: covers no requirement")
        if not t.get("verify"):
            warnings.append(f"{t['id']}: no verify command")
        if (t.get("complexity") or 0) > SPLIT_THRESHOLD and t.get("status") not in FINISHED:
            warnings.append(f"{t['id']}: complexity {t['complexity']} > {SPLIT_THRESHOLD}, split it")
    cycle = _find_cycle(tasks)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))
    return {"ok": not errors, "errors": errors, "warnings": warnings, "count": len(tasks)}


def _find_cycle(tasks: list[dict]) -> list[str] | None:
    graph = {t["id"]: [d for d in t.get("after", [])] for t in tasks if t.get("id")}
    color: dict[str, int] = {}
    stack: list[str] = []

    def dfs(node: str) -> list[str] | None:
        color[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in graph:
                continue
            if color.get(nxt) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if color.get(nxt) is None:
                found = dfs(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = 2
        return None

    for node in graph:
        if color.get(node) is None:
            found = dfs(node)
            if found:
                return found
    return None


def progress(tasks: list[dict]) -> dict:
    live = [t for t in tasks if t.get("status") != "dropped"]
    done = sum(1 for t in live if t.get("status") == "done")
    return {"total": len(live), "done": done,
            "ratio": (done / len(live)) if live else 0.0,
            "ready": len(ready(tasks)),
            "blocked": sum(1 for t in live if t.get("status") == "blocked")}


# ---------------------------------------------------------------- mutations

def add(root: Path, title: str, covers=None, after=None, verify: str = "",
        files=None, complexity: int | None = None, task_id: str | None = None,
        notes: str = "") -> dict:
    with _Lock(root):
        data = load(root)
        tid = task_id or _next_id(data["tasks"])
        if any(t["id"] == tid for t in data["tasks"]):
            raise ValueError(f"task {tid} already exists")
        task = normalize({"id": tid, "title": title, "covers": covers or [],
                          "after": after or [], "verify": verify, "files": files or [],
                          "complexity": complexity, "notes": notes})
        data["tasks"].append(task)
        save(root, data)
    return task


def claim(root: Path, owner: str, task_id: str | None = None) -> dict | None:
    """Atomically move a ready task to in_progress. None when nothing is ready."""
    with _Lock(root):
        data = load(root)
        candidates = ready(data["tasks"])
        if task_id:
            candidates = [t for t in candidates if t["id"] == task_id]
        if not candidates:
            return None
        task = candidates[0]
        task.update(status="in_progress", claimed_by=owner, claimed_at=now_iso())
        save(root, data)
    return task


def set_status(root: Path, task_id: str, status: str, note: str = "") -> dict:
    if status not in STATUSES:
        raise ValueError(f"bad status {status}")
    with _Lock(root):
        data = load(root)
        task = _by_id(data["tasks"]).get(task_id)
        if not task:
            raise KeyError(task_id)
        task["status"] = status
        if note:
            task["notes"] = (task.get("notes", "") + f"\n[{now_iso()}] {note}").strip()
        if status == "done":
            task["done_at"] = now_iso()
        if status in ("pending", "done", "dropped", "blocked"):
            task["claimed_by"] = None if status != "done" else task.get("claimed_by")
        save(root, data)
    if status == "done":
        ledger(root, "task_done", id=task_id)
    return task


def fail(root: Path, task_id: str, note: str = "") -> dict:
    """Record a failed attempt; after MAX_ATTEMPTS the task is blocked."""
    with _Lock(root):
        data = load(root)
        task = _by_id(data["tasks"]).get(task_id)
        if not task:
            raise KeyError(task_id)
        task["attempts"] = int(task.get("attempts", 0)) + 1
        task["status"] = "blocked" if task["attempts"] >= MAX_ATTEMPTS else "pending"
        task["claimed_by"] = None
        if note:
            task["notes"] = (task.get("notes", "") + f"\n[{now_iso()}] FAIL: {note}").strip()
        save(root, data)
    return task


# ---------------------------------------------------------------- markdown io

_MD_LINE = re.compile(r"^\s*[-*]\s*\[(?P<done>[ xX])\]\s*(?P<id>T-[\w-]+)\s*[:：]\s*(?P<rest>.+)$")


def import_md(root: Path, md_path: Path, replace: bool = False) -> int:
    """Import ``- [ ] T-001: Title | covers: REQ-1 | after: T-0 | verify: cmd``."""
    parsed = []
    for line in Path(md_path).read_text(encoding="utf-8").splitlines():
        m = _MD_LINE.match(line)
        if not m:
            continue
        parts = [p.strip() for p in m.group("rest").split("|")]
        task = {"id": m.group("id"), "title": parts[0],
                "status": "done" if m.group("done").lower() == "x" else "pending"}
        for part in parts[1:]:
            key, _, val = part.partition(":")
            key = key.strip().lower()
            if key in ("covers", "after", "files"):
                task[key] = val
            elif key in ("verify", "notes"):
                task[key] = val.strip()
            elif key == "complexity" and val.strip().isdigit():
                task["complexity"] = int(val.strip())
        parsed.append(normalize(task))
    with _Lock(root):
        data = load(root)
        if replace:
            data["tasks"] = []
        known = {t["id"] for t in data["tasks"]}
        added = [t for t in parsed if t["id"] not in known]
        data["tasks"].extend(added)
        save(root, data)
    return len(added)


def export_md(tasks: list[dict]) -> str:
    lines = ["# Task Backlog", ""]
    for t in tasks:
        box = "x" if t.get("status") == "done" else " "
        extra = []
        for key in ("covers", "after", "files"):
            if t.get(key):
                extra.append(f"{key}: {', '.join(t[key])}")
        if t.get("verify"):
            extra.append(f"verify: {t['verify']}")
        extra.append(f"complexity: {t.get('complexity')}")
        tail = (" | " + " | ".join(extra)) if extra else ""
        status = "" if t.get("status") in ("pending", "done") else f" _({t['status']})_"
        lines.append(f"- [{box}] {t['id']}: {t.get('title', '')}{tail}{status}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI

def _print(obj, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    elif isinstance(obj, list):
        for t in obj:
            if isinstance(t, dict):
                print(f"{t['id']:<8} {t.get('status', ''):<12} c={t.get('complexity')} {t.get('title', '')}")
            else:
                print(t)
    else:
        print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="taskgraph", description="Super-Skill task graph")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--covers", default="")
    a.add_argument("--after", default="")
    a.add_argument("--files", default="")
    a.add_argument("--verify", default="")
    a.add_argument("--complexity", type=int)
    a.add_argument("--id")
    a.add_argument("--notes", default="")
    ls = sub.add_parser("list")
    ls.add_argument("--status")
    sub.add_parser("ready")
    sub.add_parser("next")
    c = sub.add_parser("claim")
    c.add_argument("id", nargs="?")
    c.add_argument("--owner", default="agent")
    for name in ("start", "done", "review", "block", "drop", "reopen"):
        p = sub.add_parser(name)
        p.add_argument("id")
        p.add_argument("--note", default="")
    f = sub.add_parser("fail")
    f.add_argument("id")
    f.add_argument("--note", default="")
    sub.add_parser("waves")
    sub.add_parser("validate")
    sub.add_parser("progress")
    sub.add_parser("complexity")
    im = sub.add_parser("import-md")
    im.add_argument("path")
    im.add_argument("--replace", action="store_true")
    sub.add_parser("export-md")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    tasks = load(root)["tasks"]

    if args.cmd == "add":
        _print(add(root, args.title, args.covers, args.after, args.verify, args.files,
                   args.complexity, args.id, args.notes), True)
    elif args.cmd == "list":
        _print([t for t in tasks if not args.status or t.get("status") == args.status], args.json)
    elif args.cmd == "ready":
        _print(ready(tasks), args.json)
    elif args.cmd == "next":
        r = ready(tasks)
        if not r:
            print("no ready task")
            return 1
        _print(r[0], True)
    elif args.cmd == "claim":
        t = claim(root, args.owner, args.id)
        if not t:
            print("no ready task to claim")
            return 1
        _print(t, True)
    elif args.cmd in ("start", "done", "review", "block", "drop", "reopen"):
        status = {"start": "in_progress", "done": "done", "review": "review",
                  "block": "blocked", "drop": "dropped", "reopen": "pending"}[args.cmd]
        _print(set_status(root, args.id, status, args.note), True)
    elif args.cmd == "fail":
        _print(fail(root, args.id, args.note), True)
    elif args.cmd == "waves":
        w = waves(tasks)
        if args.json:
            _print(w, True)
        else:
            for i, layer in enumerate(w, 1):
                print(f"wave {i}: {', '.join(layer)}")
    elif args.cmd == "validate":
        res = validate(tasks)
        _print(res, True)
        return 0 if res["ok"] else 1
    elif args.cmd == "progress":
        _print(progress(tasks), True)
    elif args.cmd == "complexity":
        rows = [{"id": t["id"], "complexity": t.get("complexity") or estimate_complexity(t),
                 "estimated": estimate_complexity(t),
                 "split": (t.get("complexity") or estimate_complexity(t)) > SPLIT_THRESHOLD}
                for t in tasks]
        _print(rows, True)
    elif args.cmd == "import-md":
        print(f"imported {import_md(root, Path(args.path), args.replace)} task(s)")
    elif args.cmd == "export-md":
        print(export_md(tasks), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
