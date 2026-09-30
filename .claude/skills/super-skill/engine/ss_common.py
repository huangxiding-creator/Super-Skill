"""Shared helpers for the Super-Skill V5 engine and hooks.

Stdlib only. Every file under ``engine/`` and ``hooks/`` imports this module,
so it must stay fast to import and must never raise on missing state.

Project layout managed by the engine (all under ``<project>/.super-skill/``)::

    state.json      phase state machine (written only via ss.py)
    ledger.jsonl    append-only progress / transition log
    events.jsonl    hook event stream (one line per hook call)
    tasks.json      task graph (taskgraph.py)
    handoff.md      context hand-off written before compaction
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

ENGINE_DIR = Path(__file__).resolve().parent
SKILL_DIR = ENGINE_DIR.parent
PHASES_FILE = SKILL_DIR / "phases.json"
STATE_DIRNAME = ".super-skill"
SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------- time / io

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def force_utf8_stdio() -> None:
    """Windows consoles default to a legacy codepage; hooks emit UTF-8 JSON."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json_atomic(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_jsonl(path: Path, record: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path, tail: int | None = None) -> list[dict]:
    """Read a JSONL file, skipping corrupt lines. ``tail`` keeps the last N."""
    try:
        with open(path, "rb") as fh:
            if tail:
                # read only the end of large logs
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                fh.seek(max(0, size - max(4096, tail * 2048)))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = raw.splitlines()
    if tail:
        lines = lines[-tail:]
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def count_lines(path: Path) -> int:
    try:
        with open(path, "rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def short_hash(text: str, n: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:n]


# ---------------------------------------------------------------- project

def find_root(start: str | os.PathLike | None = None) -> Path | None:
    """Nearest ancestor of ``start`` holding ``.super-skill/state.json``.

    ``SUPER_SKILL_PROJECT`` overrides discovery. Returns None when the
    directory is not a Super-Skill project, which makes every hook a no-op.
    """
    override = os.environ.get("SUPER_SKILL_PROJECT")
    if override:
        p = Path(override)
        return p if (p / STATE_DIRNAME / "state.json").is_file() else None
    cur = Path(start or os.getcwd()).resolve()
    for cand in (cur, *cur.parents):
        if (cand / STATE_DIRNAME / "state.json").is_file():
            return cand
    return None


def sdir(root: Path) -> Path:
    return Path(root) / STATE_DIRNAME


def state_path(root: Path) -> Path:
    return sdir(root) / "state.json"


def load_state(root: Path) -> dict:
    return read_json(state_path(root), default={}) or {}


def save_state(root: Path, state: dict) -> None:
    state["last_updated"] = now_iso()
    write_json_atomic(state_path(root), state)


def ledger(root: Path, kind: str, **fields: Any) -> dict:
    rec = {"ts": now_iso(), "kind": kind, **fields}
    append_jsonl(sdir(root) / "ledger.jsonl", rec)
    return rec


def load_phases(path: Path | None = None) -> dict:
    data = read_json(path or PHASES_FILE, default=None)
    if not data or "phases" not in data:
        raise RuntimeError(f"phases file missing or invalid: {path or PHASES_FILE}")
    return data


def phase_index(phases: dict) -> dict[str, dict]:
    return {p["id"]: p for p in phases["phases"]}


def phase_order(phases: dict) -> list[str]:
    return [p["id"] for p in phases["phases"]]


# ---------------------------------------------------------------- hook I/O

def read_hook_input() -> dict:
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()


def hook_context(event: str, text: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}


def hook_error_log(msg: str) -> None:
    """Hooks must never break a session: errors go to a log, not the user."""
    try:
        log = Path.home() / ".claude" / "logs" / "super-skill-hooks.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"[{now_iso()}] {msg}\n")
    except OSError:
        pass


def tool_text(value: Any, limit: int = 4000) -> str:
    """Flatten a tool_input / tool_response value into bounded text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:limit]
    try:
        return json.dumps(value, ensure_ascii=False)[:limit]
    except (TypeError, ValueError):
        return str(value)[:limit]


def first(items: Iterable[Any], default: Any = None) -> Any:
    for item in items:
        return item
    return default
