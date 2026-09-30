"""Phase state machine for Super-Skill (W2).

Patterns: GSD ``STATE.md`` resume pointer and cc-sdd ``spec.json`` approvals
(both MIT), LangGraph-style checkpoints (pattern). ``state.json`` is the one
source of truth; it is only changed through these functions (the PreToolUse
guard denies direct edits), and every transition is appended to the ledger.

Statuses: ``executing`` · ``awaiting_approval`` (a human gate is pending) ·
``awaiting_user`` (``wait`` was called with a reason) · ``paused`` · ``done``.
Phase statuses: ``pending`` · ``in_progress`` · ``done`` · ``skipped`` · ``stale``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    SCHEMA_VERSION, ledger, load_phases, load_state, now_iso, phase_index,
    phase_order, save_state, sdir, state_path,
)

GITIGNORE = """# Super-Skill runtime files (machine-local)
events.jsonl
cost_cache.json
memindex.sqlite*
*.lock
evolve/variants/
ralph/
"""


def default_state(project: str, phases: dict, start: str, config: dict | None = None) -> dict:
    order = phase_order(phases)
    if start not in order:
        raise KeyError(f"unknown start phase {start}")
    start_idx = order.index(start)
    ts = now_iso()
    ph = {}
    for i, pid in enumerate(order):
        status = "skipped" if i < start_idx else ("in_progress" if i == start_idx else "pending")
        ph[pid] = {"status": status, "started_at": ts if i == start_idx else None, "done_at": None}
    return {
        "schema_version": SCHEMA_VERSION, "project": project, "status": "executing",
        "active_phase": start, "gate_mode": True, "phases": ph, "approvals": {},
        "config": {"test_cmd": "", "tag_phases": True, "requirements_file": "REQUIREMENTS.md",
                   **(config or {})},
        "budget": {"usd_limit": None, "token_limit": None, "warn_ratio": 0.7},
        "stop_blocks": 0, "stop_progress_mark": 0, "wait_reason": "",
        "created_at": ts, "last_updated": ts, "next_action": "",
    }


def init(root: Path, project: str | None = None, start: str = "P0", test_cmd: str = "",
         budget_usd: float | None = None, force: bool = False) -> dict:
    root = Path(root)
    if state_path(root).exists() and not force:
        raise FileExistsError(f"{state_path(root)} exists (use --force to re-init)")
    phases = load_phases()
    st = default_state(project or root.name, phases, start, {"test_cmd": test_cmd})
    if budget_usd is not None:
        st["budget"]["usd_limit"] = float(budget_usd)
    st["next_action"] = next_action(st, phases)
    sdir(root).mkdir(parents=True, exist_ok=True)
    gi = sdir(root) / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE, encoding="utf-8")
    save_state(root, st)
    ledger(root, "init", project=st["project"], start=start)
    ledger(root, "phase_start", phase=start)
    return st


def next_action(state: dict, phases: dict | None = None, gate: dict | None = None) -> str:
    phases = phases or load_phases()
    if state.get("status") == "done":
        return "All phases complete. Run the post-run retrospective and stop."
    pid = state.get("active_phase")
    ph = phase_index(phases).get(pid, {})
    if state.get("status") == "awaiting_user":
        return f"Waiting for the user: {state.get('wait_reason') or 'input needed'}."
    if state.get("status") == "awaiting_approval":
        return (f"Phase {pid} needs human approval '{ph.get('approval')}'. Present the artifacts "
                f"and ask the user; the user approves via `ss.py approve {ph.get('approval')}`.")
    outputs = ", ".join(ph.get("outputs", [])) or "the phase artifacts"
    text = (f"Phase {pid} {ph.get('name', '')}: run sub-skill `{ph.get('skill', '?')}`, "
            f"produce {outputs}, then `ss.py advance`.")
    if gate and not gate.get("passed"):
        fails = [c["msg"] for c in gate["checks"] if c["ok"] is False and c["severity"] == "error"]
        if fails:
            text += " Gate still failing: " + "; ".join(fails[:4])
    return text


def _next_phase(state: dict, phases: dict, after: str) -> str | None:
    order = phase_order(phases)
    for pid in order[order.index(after) + 1:]:
        if state["phases"].get(pid, {}).get("status") != "skipped":
            return pid
    return None


def _git_tag(root: Path, tag: str) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        subprocess.run(["git", "tag", "-f", tag], cwd=str(root), capture_output=True, timeout=15, check=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def advance(root: Path) -> dict:
    """Run the full gate of the active phase; on pass, move to the next phase."""
    import gate_check

    root = Path(root)
    phases = load_phases()
    st = load_state(root)
    pid = st.get("active_phase")
    if st.get("status") == "done" or not pid:
        return {"ok": True, "done": True, "msg": "already done"}
    gate = gate_check.run(root, pid, static=False, record=True, phases=phases)
    ph = phase_index(phases)[pid]
    if not gate["passed"]:
        only_approval = all(c["type"] == "approval" for c in gate["checks"]
                            if c["ok"] is False and c["severity"] == "error")
        if only_approval and ph.get("approval"):
            st["status"] = "awaiting_approval"
        st["next_action"] = next_action(st, phases, gate)
        save_state(root, st)
        return {"ok": False, "phase": pid, "gate": gate, "status": st["status"]}
    ts = now_iso()
    st["phases"][pid].update(status="done", done_at=ts)
    ledger(root, "phase_done", phase=pid)
    if st.get("config", {}).get("tag_phases", True):
        _git_tag(root, f"ss/{pid}-done")
    nxt = _next_phase(st, phases, pid)
    if nxt:
        st["active_phase"] = nxt
        st["phases"][nxt].update(status="in_progress", started_at=ts, done_at=None)
        st["status"] = "executing"
        ledger(root, "phase_start", phase=nxt)
    else:
        st["status"] = "done"
    st["stop_blocks"] = 0
    st["next_action"] = next_action(st, phases)
    save_state(root, st)
    return {"ok": True, "from": pid, "to": nxt, "gate": gate, "status": st["status"]}


def goto(root: Path, phase: str) -> dict:
    """Jump to ``phase``; every later phase that was done becomes ``stale``."""
    phases = load_phases()
    order = phase_order(phases)
    if phase not in order:
        raise KeyError(f"unknown phase {phase}")
    st = load_state(root)
    idx = order.index(phase)
    for pid in order[idx + 1:]:
        if st["phases"][pid]["status"] in ("done", "in_progress"):
            st["phases"][pid]["status"] = "stale"
    st["phases"][phase].update(status="in_progress", started_at=now_iso(), done_at=None)
    st["active_phase"] = phase
    st["status"] = "executing"
    st["next_action"] = next_action(st, phases)
    save_state(root, st)
    ledger(root, "goto", phase=phase)
    ledger(root, "phase_start", phase=phase)
    return st


def approve(root: Path, name: str, note: str = "", approved: bool = True) -> dict:
    st = load_state(root)
    st.setdefault("approvals", {})[name] = {"approved": approved, "at": now_iso(),
                                            "note": note, "by": "user"}
    if st.get("status") == "awaiting_approval" and approved:
        st["status"] = "executing"
    st["next_action"] = next_action(st)
    save_state(root, st)
    ledger(root, "approve" if approved else "reject", name=name, note=note)
    return st


def wait(root: Path, reason: str) -> dict:
    st = load_state(root)
    st.update(status="awaiting_user", wait_reason=reason)
    st["next_action"] = next_action(st)
    save_state(root, st)
    ledger(root, "wait", reason=reason)
    return st


def resume(root: Path) -> dict:
    st = load_state(root)
    if st.get("status") in ("awaiting_user", "paused"):
        st["status"] = "executing"
    st["wait_reason"] = ""
    st["stop_blocks"] = 0
    st["next_action"] = next_action(st)
    save_state(root, st)
    ledger(root, "resume")
    return st


def pause(root: Path) -> dict:
    st = load_state(root)
    st["status"] = "paused"
    save_state(root, st)
    ledger(root, "pause")
    return st


def set_config(root: Path, key: str, value) -> dict:
    st = load_state(root)
    section, _, leaf = key.partition(".")
    if section in ("budget", "config") and leaf:
        st.setdefault(section, {})[leaf] = value
    elif key == "gate_mode":
        st["gate_mode"] = bool(value)
    else:
        st.setdefault("config", {})[key] = value
    save_state(root, st)
    ledger(root, "config", key=key, value=value)
    return st
