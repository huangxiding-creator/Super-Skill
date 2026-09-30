"""Tests for cost_meter.py -- synthetic data only, no network."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cost_meter as cm  # noqa: E402


# ---------------------------------------------------------------- helpers

def asst(mid, rid, model="claude-sonnet-x", inp=0, out=0, cw=0, cr=0,
         ts="2026-01-01T00:00:00.000Z", **extra) -> dict:
    return {
        "type": "assistant", "requestId": rid, "timestamp": ts,
        "message": {"id": mid, "model": model, "role": "assistant",
                    "usage": {"input_tokens": inp, "output_tokens": out,
                              "cache_creation_input_tokens": cw,
                              "cache_read_input_tokens": cr}},
        **extra,
    }


def write_jsonl(path: Path, recs: list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    return path


def make_project(tmp_path: Path, state: dict | None = None) -> Path:
    root = tmp_path / "proj"
    (root / ".super-skill").mkdir(parents=True)
    (root / ".super-skill" / "state.json").write_text(
        json.dumps(state or {}), encoding="utf-8")
    return root


# ---------------------------------------------------------------- parsing

def test_dedup_by_message_and_request_id(tmp_path):
    t = write_jsonl(tmp_path / "s.jsonl", [
        {"type": "user", "message": {"role": "user", "content": "hi"}},
        asst("m1", "r1", inp=1_000_000),
        asst("m1", "r1", inp=1_000_000),        # same response, another block
        asst("m1", "r2", inp=1_000_000),        # different request -> counted
        asst("m2", "r3", out=1_000_000, ts="2026-01-01T00:05:00Z"),
        {"type": "assistant", "message": "not-a-dict"},
        "non-object-line-is-skipped",
    ])
    u = cm.session_usage(t)
    assert u["messages"] == 3
    assert u["tokens"]["input"] == 2_000_000
    assert u["tokens"]["output"] == 1_000_000
    assert u["tokens"]["total"] == 3_000_000
    assert u["usd_estimate"] == pytest.approx(2 * 3 + 15)   # sonnet rates
    assert u["estimate"] is True
    assert u["first_ts"].startswith("2026-01-01T00:00")
    assert u["last_ts"].startswith("2026-01-01T00:05")


def test_duplicate_keeps_larger_usage(tmp_path):
    t = write_jsonl(tmp_path / "s.jsonl", [
        asst("m1", "r1", out=10), asst("m1", "r1", out=500), asst("m1", "r1", out=10)])
    assert cm.session_usage(t)["tokens"]["output"] == 500


def test_subagent_transcripts_included(tmp_path):
    t = write_jsonl(tmp_path / "abc.jsonl",
                    [asst("m1", "r1", model="claude-opus-9", inp=1_000_000)])
    write_jsonl(tmp_path / "abc" / "subagents" / "agent-1.jsonl",
                [asst("m9", "r9", model="claude-haiku-9", out=1_000_000)])
    u = cm.session_usage(t)
    assert u["files"] == 2
    assert u["messages"] == 2
    assert set(u["by_model"]) == {"claude-opus-9", "claude-haiku-9"}
    assert u["usd_estimate"] == pytest.approx(5 + 5)


def test_pricing_families_and_cache_multipliers(tmp_path):
    t = write_jsonl(tmp_path / "s.jsonl", [
        asst("a", "1", model="claude-opus-4-7", cw=1_000_000, cr=1_000_000),
        asst("b", "2", model="mystery-model", inp=1_000_000),
    ])
    u = cm.session_usage(t)
    # opus: cache_write 5*1.25, cache_read 5*0.1 ; unknown -> sonnet input 3
    assert u["usd_estimate"] == pytest.approx(6.25 + 0.5 + 3)


def test_cost_usd_preferred(tmp_path):
    t = write_jsonl(tmp_path / "s.jsonl", [
        asst("a", "1", inp=1_000_000, costUSD=0.42),
        asst("b", "2", inp=1_000_000),
    ])
    u = cm.session_usage(t)
    assert u["usd_estimate"] == pytest.approx(0.42 + 3)
    assert u["cost_usd_reported_messages"] == 1


def test_pricing_override(tmp_path):
    root = make_project(tmp_path)
    (root / ".super-skill" / "pricing.json").write_text(
        json.dumps({"sonnet": {"input": 10, "output": 20},
                    "custom": {"input": 1, "output": 2}}),
        encoding="utf-8")
    t = write_jsonl(tmp_path / "s.jsonl", [
        asst("a", "1", inp=1_000_000, cr=1_000_000),
        asst("b", "2", model="my-custom-llm", out=1_000_000),
    ])
    u = cm.session_usage(t, root=root)
    assert u["usd_estimate"] == pytest.approx(10 + 1.0 + 2)
    # without a root the defaults apply
    assert cm.session_usage(t)["usd_estimate"] == pytest.approx(3 + 0.3 + 15)


# ---------------------------------------------------------------- cache

def test_cache_hit_and_invalidation(tmp_path, monkeypatch):
    root = make_project(tmp_path)
    t = write_jsonl(tmp_path / "s.jsonl", [asst("a", "1", out=100)])
    calls = {"n": 0}
    real = cm._entries

    def counting(files):
        calls["n"] += 1
        return real(files)

    monkeypatch.setattr(cm, "_entries", counting)
    first = cm.session_usage(t, root=root)
    second = cm.session_usage(t, root=root)
    assert (first["cached"], second["cached"]) == (False, True)
    assert calls["n"] == 1
    assert second["tokens"] == first["tokens"]
    assert (root / ".super-skill" / "cost_cache.json").is_file()

    with open(t, "a", encoding="utf-8") as fh:  # size changes -> recompute
        fh.write(json.dumps(asst("b", "2", out=50)) + "\n")
    third = cm.session_usage(t, root=root)
    assert third["cached"] is False and third["tokens"]["output"] == 150
    assert calls["n"] == 2


# ---------------------------------------------------------------- budget

@pytest.mark.parametrize("budget,level", [
    (None, "off"),
    ({"usd_limit": None, "token_limit": None}, "off"),
    ({"usd_limit": 100.0}, "ok"),                               # 0.15
    ({"usd_limit": 20.0}, "warn"),                              # 0.75 >= 0.7
    ({"usd_limit": 20.0, "warn_ratio": 0.8}, "ok"),
    ({"token_limit": 1_000_000}, "exceeded"),
    ({"usd_limit": 1000.0, "token_limit": 1_200_000}, "warn"),  # worse of both
])
def test_budget_levels(tmp_path, budget, level):
    state = {"budget": budget} if budget is not None else {}
    root = make_project(tmp_path, state)
    t = write_jsonl(tmp_path / "s.jsonl", [asst("a", "1", out=1_000_000)])  # ~$15
    st = cm.budget_status(root, t)
    assert st["level"] == level
    assert st["spent_usd"] == pytest.approx(15)
    assert st["spent_tokens"] == 1_000_000
    if level == "off":
        assert st["ratio"] is None


# ---------------------------------------------------------------- report

def test_phase_report_attribution(tmp_path):
    root = make_project(tmp_path)
    s = root / ".super-skill"
    write_jsonl(s / "ledger.jsonl", [
        {"ts": "2026-01-01T10:00:00+08:00", "kind": "phase_start", "phase": "P1"},
        {"ts": "2026-01-01T10:10:00+08:00", "kind": "gate", "phase": "P1", "passed": False,
         "failures": ["x"]},
        {"ts": "2026-01-01T10:15:00+08:00", "kind": "breaker", "state": "OPEN", "reason": "r"},
        {"ts": "2026-01-01T10:20:00+08:00", "kind": "gate", "phase": "P1", "passed": True},
        {"ts": "2026-01-01T10:25:00+08:00", "kind": "cost", "usd": 1.5, "tokens": 100,
         "phase": "P1"},
        {"ts": "2026-01-01T10:30:00+08:00", "kind": "phase_done", "phase": "P1"},
        {"ts": "2026-01-01T11:00:00+08:00", "kind": "phase_start", "phase": "P2"},
        {"ts": "2026-01-01T11:05:00+08:00", "kind": "note", "msg": "hello"},
    ])
    write_jsonl(s / "events.jsonl", [
        {"ts": "2026-01-01T10:01:00+08:00", "ev": "PreToolUse", "tool": "Bash", "ok": None},
        {"ts": "2026-01-01T10:01:05+08:00", "ev": "PostToolUse", "tool": "Bash", "ok": True},
        {"ts": "2026-01-01T02:05:00Z", "ev": "PostToolUse", "tool": "Edit", "ok": False},
        {"ts": "2026-01-01T10:45:00+08:00", "ev": "PostToolUse", "tool": "Read", "ok": True},
        {"ts": "2026-01-01T11:30:00+08:00", "ev": "PostToolUseFailure", "tool": "Bash",
         "ok": None},
    ])
    rep = cm.phase_report(root)
    by = {p["phase"]: p for p in rep["phases"]}
    p1, p2 = by["P1"], by["P2"]
    assert p1["duration_s"] == 1800
    assert p1["gate_failures"] == 1 and p1["breaker_trips"] == 1
    assert (p1["tool_calls"], p1["tool_failures"]) == (2, 1)  # UTC stamp attributed too
    assert p1["cost_usd_estimate"] == 1.5 and len(p1["cost_snapshots"]) == 1
    assert p2["end"] is None
    assert (p2["tool_calls"], p2["tool_failures"]) == (1, 1)
    assert rep["unattributed"] == {"tool_calls": 1, "tool_failures": 0}
    assert rep["totals"]["tool_calls"] == 4 and rep["totals"]["tool_failures"] == 2
    assert rep["totals"]["latest_cost_usd_estimate"] == 1.5

    md = cm.render_report_md(rep)
    assert "| P1 |" in md and "| P2 |" in md
    assert "estimate" in md.lower()


def test_phase_report_empty_project(tmp_path):
    rep = cm.phase_report(make_project(tmp_path))
    assert rep["phases"] == [] and rep["totals"]["tool_calls"] == 0
    assert "Totals" in cm.render_report_md(rep)


# ---------------------------------------------------------------- CLI

def test_cli_smoke(tmp_path, capsys):
    root = make_project(tmp_path, {"phase": "P3", "budget": {"usd_limit": 10}})
    t = write_jsonl(tmp_path / "s.jsonl", [asst("a", "1", out=1_000_000)])

    assert cm.main(["session", str(t), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["tokens"]["output"] == 1_000_000

    assert cm.main(["session", str(t)]) == 0
    assert "usd_estimate=~$15.00" in capsys.readouterr().out

    assert cm.main(["budget", "--root", str(root), "--transcript", str(t), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["level"] == "exceeded"

    assert cm.main(["snapshot", "--root", str(root), "--transcript", str(t)]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["kind"] == "cost" and rec["phase"] == "P3" and rec["usd"] == pytest.approx(15)
    ledger_text = (root / ".super-skill" / "ledger.jsonl").read_text(encoding="utf-8")
    assert '"kind": "cost"' in ledger_text

    assert cm.main(["snapshot", "--root", str(root), "--transcript", str(t),
                    "--phase", "P9"]) == 0
    assert json.loads(capsys.readouterr().out)["phase"] == "P9"

    assert cm.main(["report", "--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "# Super-Skill run report" in out and "| P3 |" in out
    assert (root / ".super-skill" / "REPORT.md").is_file()

    assert cm.main(["report", "--root", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["phases"] == 2
