"""Working-tree safety shared by the unattended pipelines (daily + weekly).

Rules (each one exists because a review reproduced the failure without it):

* A run that is about to dirty the tree writes a marker (``MARKER``). Whichever
  pipeline next takes the pipeline lock checks it before touching anything.
* Leftovers of an interrupted run are **stashed, never discarded**, and only
  when it is provable they are the run's own: every dirty path lies in
  ``RECOVERABLE``, HEAD has not moved since the run started, and every dirty
  file was modified inside the run's time window. Otherwise: refuse, keep the
  marker, let a human look.
* ``revert`` never runs ``git checkout -- .`` / ``git clean``. It restores only
  files whose content is still exactly what the pipeline wrote, and stashes
  everything else it would have to undo — so a human edit made while the run
  was going is never lost.
* A failing ``git status`` means "unknown", never "clean".

``git`` is the caller's runner: ``git(*args) -> (returncode, output)``.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path

RECOVERABLE = (".claude/skills/super-skill/", ".claude-plugin/plugin.json")
MARKER = "pipeline_inprogress.json"
WINDOW_S = 8 * 3600     # ≥ any pipeline's Task Scheduler time limit (daily 7 h, weekly 6 h)
SLACK_S = 5             # filesystem timestamp granularity


def _stdout(out: str) -> str:
    return (out or "").split("\n[stderr] ", 1)[0]


def porcelain_paths(git, *args) -> list[str] | None:
    """Paths from ``git status --porcelain -z`` (both sides of renames); None if git failed."""
    rc, out = git("status", "--porcelain", "-z", *args)
    if rc != 0:
        return None
    fields = _stdout(out).split("\0")
    paths, i = [], 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":   # rename/copy: the next field is the source path
            if i < len(fields) and fields[i]:
                paths.append(fields[i])
            i += 1
    return paths


def in_scope(path: str, scope=RECOVERABLE) -> bool:
    return path.startswith(tuple(scope))


def dirty_paths(git) -> list[str] | None:
    """Tracked changes anywhere + untracked files inside RECOVERABLE (None = unknown)."""
    tracked = porcelain_paths(git, "--untracked-files=no")
    untracked = porcelain_paths(git, "--untracked-files=all", "--", *RECOVERABLE)
    if tracked is None or untracked is None:
        return None
    return sorted(set(tracked) | set(untracked))


def scoped_dirty(git, scope=RECOVERABLE) -> list[str] | None:
    """Tracked + untracked changes inside ``scope`` (None = unknown)."""
    paths = porcelain_paths(git, "--untracked-files=all", "--", *scope)
    return None if paths is None else sorted(set(paths))


def snapshot(git) -> set[str] | None:
    """Every changed or untracked (non-ignored) path in the repository."""
    paths = porcelain_paths(git, "--untracked-files=all")
    return None if paths is None else set(paths)


def head(git) -> str:
    rc, out = git("rev-parse", "HEAD")
    lines = _stdout(out).strip().splitlines()
    return lines[0].strip() if rc == 0 and lines else ""


def file_hash(path: Path) -> str | None:
    try:
        return hashlib.sha1(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def fingerprint(repo: Path, paths) -> dict[str, str | None]:
    return {p: file_hash(Path(repo) / p) for p in paths}


# ---------------------------------------------------------------- marker

def mark(logs: Path, git, owner: str, date: str) -> None:
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    data = {"owner": owner, "date": date, "pid": os.getpid(), "head": head(git),
            "since": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    tmp = logs / f"{MARKER}.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, logs / MARKER)


def read_marker(logs: Path) -> dict | None:
    path = Path(logs) / MARKER
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def clear_if_clean(logs: Path, git, ignore=frozenset()) -> bool:
    """Drop the marker once nothing a run may write is dirty; keep it when unsure."""
    path = Path(logs) / MARKER
    if not path.exists():
        return True
    dirty = scoped_dirty(git)
    if dirty is None or [p for p in dirty if p not in ignore]:
        return False
    path.unlink(missing_ok=True)
    return True


def _epoch(stamp) -> float | None:
    try:
        return dt.datetime.fromisoformat(str(stamp)).timestamp()
    except (TypeError, ValueError):
        return None


def recover(repo: Path, logs: Path, git, window_s: float = WINDOW_S) -> tuple[bool, str]:
    """Deal with an interrupted run's marker. Returns (may proceed, message)."""
    info = read_marker(logs)
    if info is None:
        return True, ""
    who = f"{info.get('owner', '?')} run of {info.get('date', '?')}"
    keep = f"inspect `git status` / `git diff`, then delete automation/logs/{MARKER}"
    dirty = dirty_paths(git)
    if dirty is None:
        return False, f"interrupted {who}: git status failed, cannot check its leftovers"
    if not dirty:
        (Path(logs) / MARKER).unlink(missing_ok=True)
        return True, f"interrupted {who} left nothing behind"
    outside = [p for p in dirty if not in_scope(p)]
    if outside:
        return False, f"interrupted {who} left changes mixed with other edits {outside[:3]} — {keep}"
    if not info.get("head") or info["head"] != head(git):
        return False, f"interrupted {who}: commits were made since, the changes may be yours — {keep}"
    since = _epoch(info.get("since"))
    if since is None:
        return False, f"interrupted {who}: marker has no start time — {keep}"
    foreign = []
    for p in dirty:
        try:
            mt = (Path(repo) / p).stat().st_mtime
        except OSError:
            continue  # deleted file: its content is still in HEAD
        if mt < since - SLACK_S or mt > since + window_s:
            foreign.append(p)
    if foreign:
        return False, (f"interrupted {who}: {foreign[:3]} changed outside the run's time window "
                       f"(probably by hand) — {keep}")
    msg = f"super-skill interrupted {who} (pid {info.get('pid', '?')})"
    rc, out = git("stash", "push", "--include-untracked", "-m", msg, "--", *RECOVERABLE)
    left = scoped_dirty(git)
    if rc != 0 or left is None or left:
        return False, f"interrupted {who}: could not stash its leftovers: {out.strip()[-160:]}"
    (Path(logs) / MARKER).unlink(missing_ok=True)
    return True, f"stashed {len(dirty)} leftover path(s) as '{msg}' (see `git stash list`)"


# ---------------------------------------------------------------- revert

def revert(repo: Path, git, log, label: str, ours: dict | None = None,
           baseline=frozenset(), scope=RECOVERABLE, created_dirs=()) -> list[str]:
    """Undo a run's changes inside ``scope`` without destroying anything.

    Files whose content is still exactly what the pipeline wrote (``ours``:
    path → sha1) are restored/removed; every other changed path is stashed as
    ``label``. Paths dirty before the run (``baseline``) are never touched;
    only directories the run created (``created_dirs``) are removed once empty.
    The caller's ``git`` must use literal pathspecs. Returns the stashed paths.
    """
    repo = Path(repo)
    dirty = scoped_dirty(git, scope)
    if dirty is None:
        log(f"[revert] git status failed — tree left as is ({label})")
        return []
    dirty = [p for p in dirty if p not in baseline]
    ours = ours or {}
    pure = [p for p in dirty if ours.get(p) is not None and file_hash(repo / p) == ours[p]]
    rest = [p for p in dirty if p not in pure]
    tracked = [p for p in pure if git("cat-file", "-e", f"HEAD:{p}")[0] == 0]
    if tracked:
        git("checkout", "HEAD", "--", *tracked)
    for p in pure:
        if p not in tracked:
            (repo / p).unlink(missing_ok=True)
    for d in sorted(created_dirs, key=lambda d: len(Path(d).parts), reverse=True):
        try:
            Path(d).rmdir()
        except OSError:
            pass
    if rest:
        rc, out = git("stash", "push", "--include-untracked", "-m", f"super-skill {label}", "--", *rest)
        left = scoped_dirty(git, rest)
        if rc != 0 or "No local changes" in out or left is None or left:
            log(f"[revert] could not stash {rest[:3]} (rc {rc}: {out.strip()[-120:]}) — left in place")
            return []
        log(f"[revert] {len(rest)} path(s) not (or no longer) the pipeline's own output kept in "
            f"stash 'super-skill {label}': {rest[:3]}")
    return rest
