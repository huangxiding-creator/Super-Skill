"""Shared runtime for Super-Skill Claude Code hooks (W1).

Contract (from the official hooks docs, verified 2026-09-30):
- input is JSON on stdin (``session_id``, ``cwd``, ``hook_event_name``,
  ``transcript_path``, plus event fields such as ``tool_name``/``tool_input``);
- exit 0 + JSON on stdout for decisions / ``additionalContext``;
- every hook here is **fail-open**: any exception is logged to
  ``~/.claude/logs/super-skill-hooks.log`` and the hook exits 0 silently.

Hooks only act inside a Super-Skill project (a directory with
``.super-skill/state.json``); everywhere else they return immediately, so a
global install never interferes with unrelated work.
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from typing import Callable

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))
from ss_common import (  # noqa: E402,F401
    append_jsonl, count_lines, emit, find_root, force_utf8_stdio, hook_context,
    hook_error_log, load_state, now_iso, read_hook_input, read_json, save_state,
    sdir, short_hash, tool_text, write_json_atomic,
)

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def project_root(payload: dict) -> Path | None:
    start = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return find_root(start)


def summarize(tool: str, tool_input) -> str:
    ti = tool_input if isinstance(tool_input, dict) else {}
    if tool in SHELL_TOOLS:
        return str(ti.get("command", ""))[:240]
    for key in ("file_path", "notebook_path", "path", "pattern", "url", "description", "query"):
        if ti.get(key):
            return str(ti[key])[:240]
    return tool_text(tool_input, 240)


def response_failed(resp) -> bool:
    if isinstance(resp, dict):
        if resp.get("is_error") or resp.get("isError") or resp.get("error"):
            return True
        if resp.get("interrupted"):
            return True
        code = resp.get("exit_code", resp.get("exitCode", resp.get("returnCode")))
        if isinstance(code, int) and code != 0:
            return True
    return False


def event_record(payload: dict, root: Path, ok=None) -> dict:
    ev = payload.get("hook_event_name", "")
    tool = payload.get("tool_name")
    resp = payload.get("tool_response", payload.get("tool_result", payload.get("tool_output")))
    rec = {"ts": now_iso(), "sid": (payload.get("session_id") or "")[:12], "ev": ev,
           "tool": tool, "summary": summarize(tool, payload.get("tool_input")) if tool else "",
           "ok": ok, "out_hash": short_hash(tool_text(resp, 2000)) if resp is not None else None,
           "agent": payload.get("agent_type") or payload.get("agent_id"),
           "phase": load_state(root).get("active_phase")}
    if ev == "PostToolUseFailure":
        rec["ok"] = False
        rec["error"] = tool_text(payload.get("error") or resp, 300)
    elif ev == "PostToolUse" and ok is None:
        rec["ok"] = not response_failed(resp)
    return rec


def log_event(root: Path, rec: dict) -> None:
    append_jsonl(sdir(root) / "events.jsonl", rec)


def bump_progress(root: Path, n: int = 1) -> int:
    path = sdir(root) / "progress.json"
    data = read_json(path, default={}) or {}
    data["work"] = int(data.get("work", 0)) + n
    data["ts"] = now_iso()
    write_json_atomic(path, data)
    return data["work"]


def progress_mark(root: Path) -> int:
    work = int((read_json(sdir(root) / "progress.json", default={}) or {}).get("work", 0))
    return work + count_lines(sdir(root) / "ledger.jsonl")


def run(handler: Callable[[dict, Path], dict | None], needs_project: bool = True) -> None:
    """Hook entry point: parse stdin, call handler, emit its JSON, never raise."""
    force_utf8_stdio()
    try:
        payload = read_hook_input()
        root = project_root(payload)
        if root is None and needs_project:
            return
        out = handler(payload, root)
        if out:
            emit(out)
    except Exception:  # fail-open by design
        hook_error_log(f"{Path(sys.argv[0]).name}: {traceback.format_exc()[-1500:]}")
    finally:
        try:
            sys.stdout.flush()
        except Exception:
            pass
