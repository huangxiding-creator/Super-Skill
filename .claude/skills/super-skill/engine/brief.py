"""Session brief + context hand-off (W1/W2).

``build_brief`` is injected by the SessionStart hook so a fresh, resumed or
compacted session knows exactly where the run stands. ``write_handoff`` is
called before compaction (Continuous-Claude pattern, MIT) and on demand.
Optional modules (playbook, cost_meter) are used when present and skipped
silently otherwise — the brief must never fail.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    ENGINE_DIR, load_phases, load_state, now_iso, phase_index, read_jsonl, sdir,
)


def ss_cmd() -> str:
    """Portable command line for the engine CLI on *this* machine."""
    return f'"{Path(sys.executable).as_posix()}" "{(ENGINE_DIR / "ss.py").as_posix()}"'


def _tasks_summary(root: Path) -> tuple[str, dict | None]:
    try:
        import taskgraph
        tasks = taskgraph.load(root)["tasks"]
    except Exception:
        return "", None
    if not tasks:
        return "", None
    prog = taskgraph.progress(tasks)
    ready = taskgraph.ready(tasks)
    active = [t for t in tasks if t.get("status") == "in_progress"]
    line = f"tasks {prog['done']}/{prog['total']} done · {prog['ready']} ready · {prog['blocked']} blocked"
    if active:
        line += " · in progress: " + ", ".join(f"{t['id']} {t['title'][:40]}" for t in active[:3])
    return line, (ready[0] if ready else None)


def _playbook_lines(root: Path, k: int = 8) -> list[str]:
    try:
        import playbook
        return [f"- [{b.get('section')}] {b.get('text')}" for b in playbook.top(root, k=k, max_chars=1500)]
    except Exception:
        return []


def _budget_line(root: Path, transcript: str | None) -> str:
    if not transcript:
        return ""
    try:
        import cost_meter
        b = cost_meter.budget_status(root, transcript)
    except Exception:
        return ""
    if b.get("level") in (None, "off"):
        return ""
    return (f"budget: {b['level']} — {b.get('ratio', 0):.0%} used "
            f"(≈${b.get('spent_usd', 0):.2f} estimate)")


def build_brief(root: Path, transcript: str | None = None, source: str = "startup",
                max_chars: int = 3500) -> str:
    root = Path(root)
    st = load_state(root)
    if not st:
        return ""
    phases = load_phases()
    pid = st.get("active_phase")
    ph = phase_index(phases).get(pid, {})
    lines = [f"# Super-Skill run: {st.get('project')} ({source})",
             f"status: **{st.get('status')}** · active phase: **{pid} {ph.get('name', '')}** "
             f"(sub-skill `{ph.get('skill', '?')}`)",
             f"next action: {st.get('next_action') or '—'}"]
    try:
        import gate_check
        gate = gate_check.run(root, pid, static=True, phases=phases) if pid and st.get("status") != "done" else None
    except Exception:
        gate = None
    if gate:
        fails = [c["msg"] for c in gate["checks"] if c["ok"] is False and c["severity"] == "error"]
        lines.append("gate (static): " + ("passes — run `ss.py advance`" if not fails
                                           else "failing → " + "; ".join(fails[:5])))
    tline, nxt = _tasks_summary(root)
    if tline:
        lines.append(tline)
    if nxt:
        lines.append(f"next ready task: {nxt['id']} {nxt['title']} (verify: `{nxt.get('verify') or '—'}`)")
    try:
        import loop_guard
        lg = loop_guard.load(root)
        if lg["state"] != loop_guard.CLOSED:
            lines.append(f"loop guard: {lg['state']} — {lg.get('reason')}")
    except Exception:
        pass
    bl = _budget_line(root, transcript)
    if bl:
        lines.append(bl)
    lines.append(f"engine CLI: {ss_cmd()} status|gate|advance|task …")
    pb = _playbook_lines(root)
    if pb:
        lines += ["", "## Playbook (learned rules — follow them)"] + pb
    handoff = sdir(root) / "handoff.md"
    if source in ("resume", "compact", "clear") and handoff.is_file():
        text = handoff.read_text(encoding="utf-8", errors="replace")
        lines += ["", "## Last hand-off", text[:1500]]
    if st.get("status") in ("executing",) and ph.get("autonomous"):
        lines += ["", "Autonomy rule: this phase runs without user interaction. Do not stop to ask; "
                  "a Stop hook blocks early exits until the gate passes. Use `ss.py wait \"<reason>\"` "
                  "only for human-only steps (credentials, payments, approvals)."]
    text = "\n".join(lines)
    return text[:max_chars]


def _git_status(root: Path) -> str:
    if not (root / ".git").exists():
        return ""
    try:
        out = subprocess.run(["git", "status", "--short", "--branch"], cwd=str(root),
                             capture_output=True, text=True, timeout=5, encoding="utf-8",
                             errors="replace").stdout
        return "\n".join(out.splitlines()[:25])
    except (OSError, subprocess.SubprocessError):
        return ""


def write_handoff(root: Path, reason: str = "manual", include_git: bool = True) -> Path:
    root = Path(root)
    st = load_state(root)
    ledger_tail = read_jsonl(sdir(root) / "ledger.jsonl", tail=12)
    failures = [e for e in read_jsonl(sdir(root) / "events.jsonl", tail=200) if e.get("ok") is False][-5:]
    tline, nxt = _tasks_summary(root)
    lines = [f"# Hand-off — {now_iso()} ({reason})", "",
             f"- project: {st.get('project')} · status: {st.get('status')} · phase: {st.get('active_phase')}",
             f"- next action: {st.get('next_action') or '—'}"]
    if tline:
        lines.append(f"- {tline}")
    if nxt:
        lines.append(f"- next ready task: {nxt['id']} {nxt['title']}")
    lines += ["", "## Recent ledger"] + [
        f"- {e.get('ts')} {e.get('kind')} " + " ".join(f"{k}={v}" for k, v in e.items() if k not in ("ts", "kind"))[:160]
        for e in ledger_tail]
    if failures:
        lines += ["", "## Recent failures"] + [f"- {e.get('tool')}: {e.get('summary', '')[:140]}" for e in failures]
    if include_git:
        gs = _git_status(root)
        if gs:
            lines += ["", "## git status", "```", gs, "```"]
    path = sdir(root) / "handoff.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
