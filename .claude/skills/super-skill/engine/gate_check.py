#!/usr/bin/env python3
"""Deterministic phase-gate checker (W2).

Runs the ``gate`` list of a phase from ``phases.json`` against a project.
``--static`` skips checks that execute commands, so hooks can call it cheaply.
Results are written to ``.super-skill/gates/<PHASE>.json``.

Check types::

    file_exists  {path}                 min_bytes   {path, min}
    glob_count   {pattern, min}         no_marker   {paths, marker}
    json_field   {path, field, op, value}  (op: eq | in | nonempty | gte)
    regex_count  {path, pattern, min}   regex_number {path, pattern, min}
    approval     {name}                 state_field {field, op, value}
    git_repo     {}                     command     {cmd | cmd_from, timeout}
    req_ids      {path, min}            ears        {path}
    trace        {require: tasks|tests} taskgraph_valid {}
    tasks_done   {min_ratio}            loop_guard_closed {}
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import (  # noqa: E402
    force_utf8_stdio, ledger, load_phases, load_state, now_iso, phase_index,
    read_json, sdir, write_json_atomic,
)

COMMAND_TYPES = {"command"}


def _dotted(obj, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _compare(actual, op: str, expected) -> bool:
    if op == "nonempty":
        return actual not in (None, "", [], {})
    if op == "eq":
        return actual == expected
    if op == "in":
        return actual in (expected or [])
    if op == "gte":
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False
    raise ValueError(f"unknown op {op}")


def _read(root: Path, rel: str) -> str | None:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def run_check(root: Path, check: dict, state: dict, static: bool = False) -> dict:
    """Evaluate one check. Returns ``{ok: True|False|None, msg}`` (None = skipped)."""
    ctype = check.get("type")
    path = check.get("path", "")
    if ctype == "file_exists":
        p = root / path
        ok = p.is_dir() if path.endswith("/") else p.is_file()
        return {"ok": ok, "msg": f"{path} {'exists' if ok else 'missing'}"}
    if ctype == "min_bytes":
        try:
            size = (root / path).stat().st_size
        except OSError:
            return {"ok": False, "msg": f"{path} missing"}
        return {"ok": size >= check["min"], "msg": f"{path} is {size} bytes (min {check['min']})"}
    if ctype == "glob_count":
        n = len(glob.glob(str(root / check["pattern"]), recursive=True))
        return {"ok": n >= check.get("min", 1), "msg": f"{check['pattern']}: {n} match(es)"}
    if ctype == "no_marker":
        marker = check.get("marker", "[NEEDS CLARIFICATION]")
        hits = [p for p in check.get("paths", []) if marker in (_read(root, p) or "")]
        return {"ok": not hits, "msg": f"{marker} left in {', '.join(hits)}" if hits else f"no {marker}"}
    if ctype == "json_field":
        data = read_json(root / path, default=None)
        if data is None:
            return {"ok": False, "msg": f"{path} missing or invalid JSON"}
        actual = _dotted(data, check["field"])
        ok = _compare(actual, check.get("op", "eq"), check.get("value"))
        return {"ok": ok, "msg": f"{path}:{check['field']} = {actual!r}"}
    if ctype in ("regex_count", "regex_number"):
        text = _read(root, path)
        if text is None:
            return {"ok": False, "msg": f"{path} missing"}
        matches = re.findall(check["pattern"], text)
        if ctype == "regex_count":
            return {"ok": len(matches) >= check.get("min", 1), "msg": f"{len(matches)} match(es)"}
        nums = []
        for m in matches:
            try:
                nums.append(float(m if isinstance(m, str) else m[0]))
            except (TypeError, ValueError):
                continue
        if not nums:
            return {"ok": False, "msg": "number not found"}
        return {"ok": max(nums) >= check["min"], "msg": f"value {max(nums)} (min {check['min']})"}
    if ctype == "approval":
        name = check["name"]
        rec = (state.get("approvals") or {}).get(name) or {}
        ok = rec.get("approved") is True
        return {"ok": ok, "msg": f"approval '{name}' {'granted' if ok else 'pending — needs the user'}"}
    if ctype == "state_field":
        actual = _dotted(state, check["field"])
        ok = _compare(actual, check.get("op", "nonempty"), check.get("value"))
        return {"ok": ok, "msg": f"state.{check['field']} = {actual!r}"}
    if ctype == "git_repo":
        ok = (root / ".git").exists()
        return {"ok": ok, "msg": "git repository present" if ok else "not a git repository"}
    if ctype == "command":
        cmd = check.get("cmd") or _dotted(state, check.get("cmd_from", "")) or ""
        if not cmd:
            return {"ok": False, "msg": f"no command configured ({check.get('cmd_from')})"}
        if static:
            return {"ok": None, "msg": f"skipped in static mode: {cmd}"}
        try:
            proc = subprocess.run(cmd, shell=True, cwd=str(root), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=check.get("timeout", 600))
        except subprocess.TimeoutExpired:
            return {"ok": False, "msg": f"timeout: {cmd}"}
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
        return {"ok": proc.returncode == 0,
                "msg": f"`{cmd}` exit {proc.returncode}" + (f": {' | '.join(tail)}" if tail else "")}
    if ctype in ("req_ids", "ears", "trace"):
        import trace_matrix
        req_file = root / (path or (state.get("config") or {}).get("requirements_file", "REQUIREMENTS.md"))
        if ctype == "req_ids":
            reqs = [r for r in trace_matrix.parse_requirements(req_file) if not r["is_ac"]]
            return {"ok": len(reqs) >= check.get("min", 1), "msg": f"{len(reqs)} REQ id(s)"}
        if ctype == "ears":
            res = trace_matrix.ears_lint(req_file)
            bad = ", ".join(v["id"] for v in res["violations"][:5])
            return {"ok": res["ok"], "msg": f"EARS: {res['checked']} checked" + (f", not EARS: {bad}" if bad else "")}
        res = trace_matrix.build(root, req_file, check.get("require", "tasks"), write=not static)
        return {"ok": res["ok"], "msg": "; ".join(res["problems"][:5]) or
                f"MUST coverage tasks {res['coverage']['tasks']:.0%} tests {res['coverage']['tests']:.0%}"}
    if ctype in ("taskgraph_valid", "tasks_done"):
        import taskgraph
        tasks = taskgraph.load(root)["tasks"]
        if ctype == "taskgraph_valid":
            if not tasks:
                return {"ok": False, "msg": "tasks.json has no tasks"}
            res = taskgraph.validate(tasks)
            return {"ok": res["ok"], "msg": "; ".join(res["errors"][:5]) or f"{res['count']} tasks valid"}
        prog = taskgraph.progress(tasks)
        ok = prog["total"] > 0 and prog["ratio"] >= check.get("min_ratio", 1.0)
        return {"ok": ok, "msg": f"{prog['done']}/{prog['total']} tasks done"}
    if ctype == "loop_guard_closed":
        import loop_guard
        st = loop_guard.load(root)
        return {"ok": st["state"] != loop_guard.OPEN, "msg": f"breaker {st['state']}"}
    return {"ok": False, "msg": f"unknown check type {ctype!r}"}


def run(root: Path, phase_id: str, static: bool = False, record: bool = False,
        phases: dict | None = None) -> dict:
    root = Path(root)
    phases = phases or load_phases()
    phase = phase_index(phases).get(phase_id)
    if not phase:
        raise KeyError(f"unknown phase {phase_id}")
    state = load_state(root)
    results = []
    for check in phase.get("gate", []):
        try:
            res = run_check(root, check, state, static)
        except Exception as exc:  # a broken check must fail loudly, not crash the gate
            res = {"ok": False, "msg": f"check error: {exc}"}
        results.append({"type": check.get("type"), "severity": check.get("severity", "error"), **res})
    errors = [r for r in results if r["ok"] is False and r["severity"] == "error"]
    warnings = [r for r in results if r["ok"] is False and r["severity"] != "error"]
    out = {"phase": phase_id, "name": phase.get("name"), "passed": not errors,
           "static": static, "ts": now_iso(), "checks": results,
           "errors": len(errors), "warnings": len(warnings),
           "skipped": sum(1 for r in results if r["ok"] is None)}
    if sdir(root).is_dir() and not static:
        write_json_atomic(sdir(root) / "gates" / f"{phase_id}.json", out)
    if record:
        ledger(root, "gate", phase=phase_id, passed=out["passed"],
               failures=[r["msg"] for r in errors])
    return out


def render(res: dict) -> str:
    icon = {True: "✅", False: "❌", None: "⏭"}
    lines = [f"Gate {res['phase']} {res.get('name', '')}: {'PASS' if res['passed'] else 'FAIL'}"
             + (" (static)" if res["static"] else "")]
    for c in res["checks"]:
        sev = "" if c["severity"] == "error" else f" [{c['severity']}]"
        lines.append(f"  {icon[c['ok']]} {c['type']}{sev}: {c['msg']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="gate_check", description="run a phase gate")
    ap.add_argument("phase", nargs="?")
    ap.add_argument("--root", default=".")
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    phase_id = args.phase or load_state(root).get("active_phase")
    if not phase_id:
        print("no phase given and no active phase in state", file=sys.stderr)
        return 2
    res = run(root, phase_id, static=args.static, record=not args.static)
    print(json.dumps(res, ensure_ascii=False, indent=2) if args.json else render(res))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
