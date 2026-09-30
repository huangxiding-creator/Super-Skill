"""Tests for the V5 core engine: state machine, gates, task graph, trace
matrix, loop guard, brief/hand-off and the Ralph driver (fake agent)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

import brief  # noqa: E402
import gate_check  # noqa: E402
import loop_guard  # noqa: E402
import ralph  # noqa: E402
import ss  # noqa: E402
import state_machine as sm  # noqa: E402
import taskgraph  # noqa: E402
import trace_matrix  # noqa: E402
from ss_common import find_root, load_phases, load_state, read_jsonl, sdir  # noqa: E402

REQS = """# Requirements
- REQ-001 [MUST]: When a user adds a todo, the system shall persist it.
  - REQ-001.AC1: the todo is listed after reload
- REQ-002 [MUST]: 当用户离线时，系统应缓存草稿
- REQ-003 [SHOULD]: The system shall export CSV.
"""
PASS_CMD = f'"{sys.executable}" -c "pass"'


@pytest.fixture
def proj(tmp_path):
    sm.init(tmp_path, "demo", "P4", test_cmd=PASS_CMD)
    (tmp_path / "REQUIREMENTS.md").write_text(REQS, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------- phases.json

def test_phases_contract_is_complete():
    phases = load_phases()
    ids = [p["id"] for p in phases["phases"]]
    assert ids[:3] == ["IF1", "IF2", "IF3"] and ids[-1] == "P12"
    assert len(ids) == len(set(ids)) == 17
    known = {"file_exists", "min_bytes", "glob_count", "no_marker", "json_field", "regex_count",
             "regex_number", "approval", "state_field", "git_repo", "command", "req_ids", "ears",
             "trace", "taskgraph_valid", "tasks_done", "loop_guard_closed"}
    for p in phases["phases"]:
        assert p["gate"], f"{p['id']} has no gate"
        for c in p["gate"]:
            assert c["type"] in known, (p["id"], c)
        if p.get("approval"):
            assert not p["autonomous"], "approval phases must not be autonomous"


# ---------------------------------------------------------------- state machine

def test_init_and_find_root(proj):
    st = load_state(proj)
    assert st["active_phase"] == "P4" and st["phases"]["P0"]["status"] == "skipped"
    assert (sdir(proj) / ".gitignore").is_file()
    (proj / "sub").mkdir()
    assert find_root(proj / "sub") == proj.resolve()
    with pytest.raises(FileExistsError):
        sm.init(proj, "again", "P4")


def test_approval_gate_blocks_until_user_approves(proj):
    res = sm.advance(proj)
    assert not res["ok"] and res["status"] == "awaiting_approval"
    assert "approval" in load_state(proj)["next_action"]
    sm.approve(proj, "requirements", "looks good")
    res = sm.advance(proj)
    assert res["ok"] and res["to"] == "P5"
    kinds = [e["kind"] for e in read_jsonl(sdir(proj) / "ledger.jsonl")]
    assert kinds.count("phase_start") == 2 and "approve" in kinds and "phase_done" in kinds


def test_goto_marks_downstream_stale(proj):
    sm.approve(proj, "requirements")
    sm.advance(proj)
    sm.goto(proj, "P4")
    st = load_state(proj)
    assert st["active_phase"] == "P4" and st["phases"]["P5"]["status"] == "stale"


def test_wait_resume_pause(proj):
    assert sm.wait(proj, "need API key")["status"] == "awaiting_user"
    assert "API key" in load_state(proj)["next_action"]
    assert sm.resume(proj)["status"] == "executing"
    assert sm.pause(proj)["status"] == "paused"


def test_config_sections(proj):
    sm.set_config(proj, "budget.usd_limit", 5)
    sm.set_config(proj, "test_cmd", "pytest -q")
    st = load_state(proj)
    assert st["budget"]["usd_limit"] == 5 and st["config"]["test_cmd"] == "pytest -q"


# ---------------------------------------------------------------- gates

def test_gate_static_skips_commands(tmp_path):
    sm.init(tmp_path, "c", "P7", test_cmd=PASS_CMD)
    res = gate_check.run(tmp_path, "P7", static=True)
    cmd = [c for c in res["checks"] if c["type"] == "command"][0]
    assert cmd["ok"] is None and res["skipped"] == 1
    full = gate_check.run(tmp_path, "P7", static=False)
    assert [c for c in full["checks"] if c["type"] == "command"][0]["ok"] is True
    assert [c for c in full["checks"] if c["type"] == "git_repo"][0]["ok"] is False
    assert (sdir(tmp_path) / "gates" / "P7.json").is_file()


def test_gate_warn_severity_does_not_block(tmp_path):
    sm.init(tmp_path, "w", "P1")
    (tmp_path / "FEASIBILITY_REPORT.md").write_text("CC-FPS score: 0.5", encoding="utf-8")
    (tmp_path / "RISK_REGISTER.md").write_text("risks", encoding="utf-8")
    res = gate_check.run(tmp_path, "P1")
    assert res["passed"] and res["warnings"] == 1


def test_gate_json_field(tmp_path):
    sm.init(tmp_path, "j", "IF3")
    (tmp_path / "PROPOSAL.md").write_text("p", encoding="utf-8")
    (tmp_path / "SCORECARD.json").write_text(json.dumps({"verdict": "revise"}), encoding="utf-8")
    res = gate_check.run(tmp_path, "IF3")
    jf = [c for c in res["checks"] if c["type"] == "json_field"][0]
    assert jf["ok"] is False and "revise" in jf["msg"]


def test_unknown_check_type_fails_loudly(tmp_path):
    sm.init(tmp_path, "u", "P0")
    phases = {"phases": [{"id": "P0", "name": "x", "gate": [{"type": "bogus"}]}]}
    res = gate_check.run(tmp_path, "P0", phases=phases)
    assert not res["passed"] and "unknown check type" in res["checks"][0]["msg"]


# ---------------------------------------------------------------- task graph

def test_taskgraph_ready_waves_claim(proj):
    a = taskgraph.add(proj, "a", covers="REQ-001", verify="true")
    b = taskgraph.add(proj, "b", covers="REQ-002", after=a["id"])
    c = taskgraph.add(proj, "c", covers="REQ-001.AC1", after=a["id"])
    tasks = taskgraph.load(proj)["tasks"]
    assert [t["id"] for t in taskgraph.ready(tasks)] == [a["id"]]
    assert taskgraph.waves(tasks) == [[a["id"]], sorted([b["id"], c["id"]])]
    got = taskgraph.claim(proj, "w1")
    assert got["id"] == a["id"] and taskgraph.claim(proj, "w2") is None
    taskgraph.set_status(proj, a["id"], "done")
    assert len(taskgraph.ready(taskgraph.load(proj)["tasks"])) == 2


def test_taskgraph_cycle_and_unknown_dep(proj):
    taskgraph.add(proj, "x", task_id="T-010", after="T-011")
    taskgraph.add(proj, "y", task_id="T-011", after="T-010")
    taskgraph.add(proj, "z", task_id="T-012", after="T-999")
    res = taskgraph.validate(taskgraph.load(proj)["tasks"])
    assert not res["ok"]
    assert any("cycle" in e for e in res["errors"]) and any("T-999" in e for e in res["errors"])


def test_taskgraph_fail_blocks_after_max_attempts(proj):
    t = taskgraph.add(proj, "flaky")
    for _ in range(taskgraph.MAX_ATTEMPTS):
        t = taskgraph.fail(proj, t["id"], "boom")
    assert t["status"] == "blocked" and t["attempts"] == taskgraph.MAX_ATTEMPTS


def test_taskgraph_markdown_roundtrip(proj, tmp_path):
    md = tmp_path / "BACKLOG.md"
    md.write_text("- [ ] T-001: Build API | covers: REQ-001 | verify: pytest -q\n"
                  "- [x] T-002: Docs | after: T-001 | complexity: 2\n", encoding="utf-8")
    assert taskgraph.import_md(proj, md) == 2
    tasks = taskgraph.load(proj)["tasks"]
    assert tasks[1]["status"] == "done" and tasks[1]["complexity"] == 2
    out = taskgraph.export_md(tasks)
    assert "- [ ] T-001: Build API" in out and "verify: pytest -q" in out


def test_complexity_heuristic_flags_risky_work():
    small = {"title": "rename label", "verify": "pytest"}
    big = {"title": "refactor auth and migrate schema", "files": ["a", "b", "c", "d"], "covers": ["R1", "R2"]}
    assert taskgraph.estimate_complexity(small) <= 3
    assert taskgraph.estimate_complexity(big) > taskgraph.SPLIT_THRESHOLD


# ---------------------------------------------------------------- traceability

def test_parse_requirements_and_ears(proj):
    reqs = trace_matrix.parse_requirements(proj / "REQUIREMENTS.md")
    assert [r["id"] for r in reqs] == ["REQ-001", "REQ-001.AC1", "REQ-002", "REQ-003"]
    assert reqs[3]["priority"] == "SHOULD" and reqs[1]["is_ac"]
    assert trace_matrix.ears_lint(proj / "REQUIREMENTS.md")["ok"]
    bad = proj / "BAD.md"
    bad.write_text("- REQ-009: fast and nice UI\n", encoding="utf-8")
    assert not trace_matrix.ears_lint(bad)["ok"]


def test_trace_requires_tasks_then_tests(proj):
    res = trace_matrix.build(proj, require="tasks")
    assert not res["ok"] and "REQ-001 has no task" in res["problems"]
    taskgraph.add(proj, "persist", covers="REQ-001.AC1")
    taskgraph.add(proj, "cache", covers="REQ-002")
    taskgraph.add(proj, "orphan", covers="REQ-404")
    res = trace_matrix.build(proj, require="tasks")
    assert any("orphan task" in p for p in res["problems"])
    taskgraph.set_status(proj, "T-003", "dropped")
    assert trace_matrix.build(proj, require="tasks")["ok"]
    tests = proj / "tests"
    tests.mkdir()
    (tests / "test_todo.py").write_text("def test_req_001_ac1():\n    pass  # REQ-002 too\n", encoding="utf-8")
    res = trace_matrix.build(proj, require="tests")
    assert res["ok"] and res["coverage"]["tests"] == 1.0
    assert (sdir(proj) / "trace.md").read_text(encoding="utf-8").count("REQ-") >= 3


# ---------------------------------------------------------------- loop guard

def test_breaker_trips_on_no_progress_and_recovers(proj):
    for _ in range(3):
        st = loop_guard.record(proj, progress=False)
    assert st["state"] == loop_guard.OPEN
    ok, why = loop_guard.can_proceed(proj)
    assert not ok and "OPEN" in why
    st = loop_guard.load(proj)
    st["opened_epoch"] -= st["cooldown_s"] + 1
    loop_guard.save(proj, st)
    assert loop_guard.can_proceed(proj)[0] and loop_guard.load(proj)["state"] == loop_guard.HALF_OPEN
    assert loop_guard.record(proj, progress=True)["state"] == loop_guard.CLOSED


def test_breaker_same_error_normalizes_volatile_bits(proj):
    st = loop_guard.load(proj)
    st["thresholds"]["no_progress"] = 99
    loop_guard.save(proj, st)
    for i in range(5):
        st = loop_guard.record(proj, progress=False, error=f"Error at /tmp/x{i}.py line {i}: boom 0x{i}f")
    assert st["state"] == loop_guard.OPEN and "same error" in st["reason"]


def test_pressure_ladder_and_exit_signal():
    assert loop_guard.pressure(1)[0] == 0
    assert loop_guard.pressure(2)[0] == 1 and "different" in loop_guard.pressure(2)[1]
    assert loop_guard.pressure(9)[0] == 4
    assert loop_guard.exit_ok("done\nEXIT_SIGNAL: true\n", True)
    assert not loop_guard.exit_ok("EXIT_SIGNAL: true", False)
    assert not loop_guard.exit_ok("all good", True)


def test_stuck_detector_patterns():
    rep = [{"ev": "PostToolUse", "tool": "Bash", "summary": "pytest", "out_hash": "h", "ok": False}] * 4
    pats = {f["pattern"] for f in loop_guard.detect_stuck(rep)}
    assert {"repeat_action", "repeat_error"} <= pats
    alt = [{"ev": "PostToolUse", "tool": "Edit", "summary": "a.py" if i % 2 else "b.py",
            "out_hash": str(i), "ok": True} for i in range(6)]
    assert "alternation" in {f["pattern"] for f in loop_guard.detect_stuck(alt)}
    mono = [{"ev": "PostToolUse", "tool": "Read", "summary": "x", "ok": True}] + [{"ev": "Stop"}] * 3
    assert "monologue" in {f["pattern"] for f in loop_guard.detect_stuck(mono)}
    healthy = [{"ev": "PostToolUse", "tool": "Edit", "summary": f"f{i}.py", "out_hash": str(i), "ok": True}
               for i in range(10)]
    assert loop_guard.detect_stuck(healthy) == []


# ---------------------------------------------------------------- brief / hand-off / CLI

def test_brief_and_handoff(proj):
    taskgraph.add(proj, "persist", covers="REQ-001", verify="pytest")
    text = brief.build_brief(proj, source="compact")
    assert "P4" in text and "next ready task: T-001" in text and "engine CLI" in text
    body = brief.write_handoff(proj, "test").read_text(encoding="utf-8")
    assert "Hand-off" in body and "Recent ledger" in body
    assert "Last hand-off" in brief.build_brief(proj, source="compact")


def test_ss_cli_smoke(proj, capsys):
    assert ss.main(["--root", str(proj), "status"]) == 0
    assert "P4" in capsys.readouterr().out
    assert ss.main(["--root", str(proj), "gate", "P4"]) == 1
    assert ss.main(["--root", str(proj), "log", "hello"]) == 0
    assert ss.main(["task", "--root", str(proj), "add", "t"]) == 0
    assert ss.main(["--root", str(proj), "config", "budget.usd_limit", "3"]) == 0
    assert load_state(proj)["budget"]["usd_limit"] == 3


# ---------------------------------------------------------------- ralph (fake agent)

FAKE_AGENT = """import pathlib, sys
prompt = sys.stdin.read()
if "EXIT_SIGNAL" in prompt:
    print("complete\\nEXIT_SIGNAL: true")
else:
    tid = prompt.split("## Task ", 1)[1].split(":", 1)[0]
    pathlib.Path(f"{tid}.done").write_text("ok")
    print("did it\\nLEARNINGS:\\n- wrote marker")
"""


def test_ralph_runs_tasks_and_honours_dual_exit(proj):
    (proj / "fake_agent.py").write_text(FAKE_AGENT, encoding="utf-8")
    py = sys.executable
    for tid in ("T-001", "T-002"):
        taskgraph.add(proj, f"make {tid}", task_id=tid,
                      verify=f'"{py}" -c "import pathlib,sys; sys.exit(0 if pathlib.Path(\'{tid}.done\').exists() else 1)"')
    res = ralph.run(proj, agent_cmd=f'"{py}" fake_agent.py', max_iterations=6, commit=False)
    assert res["exit"] == "all_done+exit_signal" and res["kept"] == 2
    rows = (proj / "experiments.tsv").read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("ts\t") and sum("\tkeep\t" in r for r in rows) == 2
    assert "wrote marker" in (proj / "progress.txt").read_text(encoding="utf-8")


def test_ralph_discards_failed_verify_and_blocks_task(proj):
    py = sys.executable
    taskgraph.add(proj, "impossible", task_id="T-001", verify=f'"{py}" -c "raise SystemExit(3)"')
    res = ralph.run(proj, agent_cmd=f'"{py}" -c "print(1)"', max_iterations=10, commit=False)
    assert res["discarded"] >= 3 and res["kept"] == 0
    assert res["exit"] in ("only_blocked_tasks", "no_ready_tasks") or res["exit"].startswith("breaker")
    assert taskgraph.load(proj)["tasks"][0]["status"] == "blocked"
