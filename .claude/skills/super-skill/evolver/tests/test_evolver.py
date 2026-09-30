"""Tests for the Super-Skill V5 evolver (stdlib + pytest, no network, no claude)."""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

EVOLVER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVOLVER))

import archive as arch  # noqa: E402
import evolve  # noqa: E402
import mutate  # noqa: E402
import strategies  # noqa: E402
from fitness import fitness, pass_rate  # noqa: E402

EXAMPLES = EVOLVER / "examples"
PY = mutate.quote(sys.executable)


def q(p) -> str:
    return mutate.quote(str(p))


def toy_cmds():
    ev = f"{PY} {q(EXAMPLES / 'toy_eval.py')} {{target}}"
    mu = f"{PY} {q(EXAMPLES / 'toy_mutator.py')} {{prompt}} {{target}}"
    return ev, mu


# ------------------------------------------------------------------ fitness

def test_fitness_penalties():
    base = {"tasks": {"a": 1.0, "b": 0.5}, "tokens": 0, "lines_added": 0}
    assert fitness(base) == pytest.approx(0.75)
    assert pass_rate({"a": 2.0, "b": -1}) == pytest.approx(0.5)  # clamped
    tok = dict(base, tokens=100000)
    assert fitness(tok) == pytest.approx(0.75 - 0.05)
    lines = dict(base, lines_added=100)
    assert fitness(lines) == pytest.approx(0.75 - 0.02)
    both = dict(base, tokens=200000, lines_added=50)
    assert fitness(both, {"lambda": 0.1, "mu": 0.2}) == pytest.approx(0.75 - 0.2 - 0.1)
    assert fitness({"tasks": {}}) == 0.0


# ------------------------------------------------------------------ archive

def test_dgm_weight_monotonic_and_children_penalty():
    scores = [i / 10 for i in range(11)]
    ws = [arch.dgm_weight(s, 0) for s in scores]
    assert all(a < b for a, b in zip(ws, ws[1:]))
    assert arch.dgm_weight(0.5, 0) == pytest.approx(0.5)
    kids = [arch.dgm_weight(0.8, c) for c in range(5)]
    assert all(a > b for a, b in zip(kids, kids[1:]))
    assert kids[1] == pytest.approx(kids[0] / 2)


def test_select_parent_prefers_high_score_and_few_children():
    rng = random.Random(0)
    a = [{"id": "hi", "status": "keep", "score": 0.9, "children": 0},
         {"id": "lo", "status": "keep", "score": 0.2, "children": 0},
         {"id": "dead", "status": "discard", "score": 0.99, "children": 0}]
    counts = {"hi": 0, "lo": 0, "dead": 0}
    for _ in range(2000):
        counts[arch.select_parent(a, rng)["id"]] += 1
    assert counts["dead"] == 0
    assert counts["hi"] > 5 * counts["lo"]
    b = [{"id": "busy", "status": "keep", "score": 0.8, "children": 9},
         {"id": "fresh", "status": "seed", "score": 0.8, "children": 0}]
    counts = {"busy": 0, "fresh": 0}
    for _ in range(2000):
        counts[arch.select_parent(b, rng)["id"]] += 1
    assert counts["fresh"] > 5 * counts["busy"]


def test_pareto_front():
    a = [
        {"id": "A", "status": "keep", "score": 0.5, "per_task": {"t1": 1.0, "t2": 0.0}},
        {"id": "B", "status": "keep", "score": 0.5, "per_task": {"t1": 0.0, "t2": 1.0}},
        {"id": "C", "status": "keep", "score": 0.4, "per_task": {"t1": 0.5, "t2": 0.5}},
        {"id": "D", "status": "seed", "score": 0.5, "per_task": {"t1": 1.0, "t2": 0.0}},
        {"id": "X", "status": "discard", "score": 1.0, "per_task": {"t1": 1.0, "t2": 1.0}},
        {"id": "S", "status": "keep", "score": 1.0, "per_task": {"t1": 1.0}, "eval_stage": "smoke"},
    ]
    front = {r["id"] for r in arch.pareto_front(a)}
    assert front == {"A", "B", "D"}  # C dominated, X discarded, S smoke-only
    assert arch.second_best_score(a) == pytest.approx(0.5)
    assert arch.second_best_score(a[:1]) == float("-inf")
    rng = random.Random(0)
    picks = {arch.select_parent(a, rng, method="pareto")["id"] for _ in range(200)}
    assert picks <= {"A", "B", "D"}


def test_is_improvement_and_simplicity():
    p = {"score": 0.5}
    assert arch.is_improvement({"score": 0.6}, p)
    assert not arch.is_improvement({"score": 0.5}, p)
    assert not arch.is_improvement({"score": 0.49}, p)
    assert arch.is_improvement({"score": 0.49}, p, leeway=0.02)
    assert arch.is_improvement({"score": 0.5, "lines_removed": 3, "lines_added": 0}, p)
    assert not arch.is_improvement({"score": None}, p)


def test_archive_io_and_children(tmp_path):
    path = tmp_path / "archive.jsonl"
    arch.append(path, {"id": "v0000", "status": "seed", "score": 0.1, "children": 0})
    arch.append(path, {"id": "v0001", "parent": "v0000", "status": "keep", "score": 0.2,
                       "children": 0})
    arch.update_children(path, "v0000")
    recs = arch.update_children(path, "v0000")
    assert arch.by_id(recs, "v0000")["children"] == 2
    assert len(arch.load(path)) == 2
    assert evolve.next_id(recs) == "v0002"


# ------------------------------------------------------------------ strategies

@pytest.mark.parametrize("name", sorted(strategies.PRESETS))
def test_strategy_preset_proportions(name):
    rng = random.Random(42)
    weights = strategies.get_weights(name)
    n = 6000
    counts = {c: 0 for c in weights}
    for _ in range(n):
        counts[strategies.pick_category(weights, rng)] += 1
    total = sum(weights.values())
    for c, w in weights.items():
        assert abs(counts[c] / n - w / total) < 0.03, (name, c, counts)


def test_pick_gene_uses_real_genes_and_signals():
    genes = strategies.load_genes()
    ids = {g["id"] for g in genes}
    assert "gene_gep_repair_from_errors" in ids
    rng = random.Random(1)
    for _ in range(50):
        g, cat = strategies.pick_gene("innovate", genes, ["skill_missing"], rng)
        assert g["category"] == cat
        if cat == "innovate":
            assert g["id"] == "gene_gep_skill_creation"  # only gene matching skill_missing
    g, cat = strategies.pick_gene("repair-only", genes, ["failed"], rng)
    assert cat == "repair" and g["id"] == "gene_gep_repair_from_errors"
    with pytest.raises(ValueError):
        strategies.get_weights("nope")


def test_stagnation_detection_and_exclusion():
    h = [("g1", True), ("g2", False), ("g2", False), ("g2", False)]
    assert strategies.detect_stagnation(h) == {"g2"}
    assert strategies.detect_stagnation(h[:-1]) == set()
    assert strategies.detect_stagnation(h[:-1] + [("g2", True)]) == set()
    assert strategies.detect_stagnation([("g2", False), ("g1", False), ("g2", False),
                                         ("g2", False)]) == set()
    archive = [{"status": "seed"}] + [
        {"status": "discard", "mutation": {"gene_id": "gene_gep_repair_from_errors"}}] * 3
    stag = strategies.detect_stagnation(strategies.history_from_archive(archive))
    assert stag == {"gene_gep_repair_from_errors"}
    genes = strategies.load_genes()
    rng = random.Random(3)
    for _ in range(30):
        g, _ = strategies.pick_gene("repair-only", genes, ["failed"], rng, exclude=stag)
        assert g["id"] not in stag


def test_extract_signals():
    genes = strategies.load_genes()
    s = strategies.extract_signals({"a": 0.0}, {"a": "Traceback: Exception raised, "
                                                     "capability_gap here"}, genes)
    assert {"failed", "exception", "capability_gap"} <= set(s)
    assert strategies.extract_signals({"a": 1.0}, {}, genes) == ["stable_success_plateau"]


# ------------------------------------------------------------------ mutate

def test_build_prompt_contents(tmp_path):
    gene = {"id": "gX", "strategy": ["do the thing"]}
    p = mutate.build_prompt("# T\nhello\n", "T.md", {"a": 0.0, "b": 1.0},
                            {"a": "missing keyword 'zap'"}, gene, "repair")
    assert "missing keyword 'zap'" in p and "`b`" not in p
    assert "do the thing" in p and "ONE section" in p and "Deleting text" in p
    assert "hello" in p
    big = "# Intro\n" + ("filler text\n" * 2000) + "# Deploy\nrun the deploy script\n"
    p2 = mutate.build_prompt(big, "T.md", {"d": 0.0}, {"d": "deploy script broken"},
                             gene, "repair", max_full_chars=1000)
    assert "Section to change: `Deploy`" in p2 and "filler text" not in p2
    path = mutate.write_prompt(tmp_path, p)
    assert path.name == "MUTATION_PROMPT.md" and path.read_text(encoding="utf-8") == p


def test_diff_stats():
    assert mutate.diff_stats("a\nb\n", "a\nb\nc\n") == {"lines_added": 1, "lines_removed": 0}
    assert mutate.diff_stats("a\nb\nc\n", "a\nc\n") == {"lines_added": 0, "lines_removed": 1}


def test_claude_mutator_argv_shape():
    argv = mutate.claude_argv(0.25)
    assert argv[1:] == ["-p", "--max-turns", "8", "--max-budget-usd", "0.25",
                        "--permission-mode", "acceptEdits"]


# ------------------------------------------------------------------ staged eval

def _fake_eval(scores, calls):
    def evaluate(tasks):
        calls.append(tasks)
        sel = tasks or list(scores)
        return {"tasks": {t: scores[t] for t in sel}, "tokens": 0, "feedback": {}}
    return evaluate


def test_staged_eval_skips_full_when_smoke_low():
    scores = {"s1": 0.0, "s2": 0.0, "f1": 1.0, "f2": 1.0}
    calls = []
    res, stage = evolve.staged_evaluate(_fake_eval(scores, calls), ["s1", "s2"], 0.5)
    assert stage == "smoke" and calls == [["s1", "s2"]]
    assert set(res["tasks"]) == {"s1", "s2"}


def test_staged_eval_runs_full_when_smoke_ok():
    scores = {"s1": 1.0, "f1": 0.0}
    calls = []
    res, stage = evolve.staged_evaluate(_fake_eval(scores, calls), ["s1"], 0.5)
    assert stage == "full" and calls == [["s1"], None]
    assert set(res["tasks"]) == {"s1", "f1"}
    calls.clear()
    _, stage = evolve.staged_evaluate(_fake_eval(scores, calls), [], 0.99)
    assert stage == "full" and calls == [None]


def test_parse_eval_output():
    out = 'log line\n{"tasks": {"a": 1, "b": 0.5}, "tokens": 7, "feedback": {"b": "x"}}\n'
    r = evolve.parse_eval_output(out)
    assert r["tasks"] == {"a": 1.0, "b": 0.5} and r["tokens"] == 7
    with pytest.raises(evolve.EvalError):
        evolve.parse_eval_output("no json here")


# ------------------------------------------------------------------ end to end

def test_toy_run_improves_and_apply(tmp_path):
    target = tmp_path / "toy_target.md"
    original = (EXAMPLES / "toy_target.md").read_text(encoding="utf-8")
    target.write_text(original, encoding="utf-8")
    out = tmp_path / "evo"
    ev, mu = toy_cmds()
    rc = evolve.main(["--target", str(target), "--eval-cmd", ev, "--mutator-cmd", mu,
                      "--iterations", "5", "--seed", "7", "--out", str(out), "--apply"])
    assert rc == 0
    recs = arch.load(out / "archive.jsonl")
    seed = recs[0]
    assert seed["status"] == "seed" and seed["parent"] is None
    top = arch.best(recs, ("keep",))
    assert top is not None and top["score"] > seed["score"]
    assert pass_rate(top["per_task"]) > pass_rate(seed["per_task"])
    for r in recs[1:]:
        ws = out / r["workspace"]
        assert (ws / "MUTATION_PROMPT.md").is_file() and (ws / "toy_target.md").is_file()
        assert r["mutation"]["gene_id"] and r["mutation"]["intent"] in strategies.CATEGORIES
    rows = (out / "results.tsv").read_text(encoding="utf-8").splitlines()
    assert rows[0].split("\t") == ["id", "parent", "gene", "score", "status", "desc"]
    assert len(rows) == 1 + len(recs)
    events = [json.loads(ln) for ln in
              (out / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(events) == 5
    for e in events:
        assert e["type"] == "EvolutionEvent"
        for k in ("id", "parent", "intent", "genes_used", "mutation_id", "blast_radius",
                  "outcome", "timestamp"):
            assert k in e
        assert set(e["outcome"]) >= {"status", "score"}
    # --apply: backup of the original + target replaced by the best variant
    backups = list(tmp_path.glob("toy_target.md.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == original
    assert target.read_text(encoding="utf-8") == evolve.variant_file(out, top).read_text(
        encoding="utf-8")
    assert sum(int(r.get("children") or 0) for r in recs) == 5


def test_toy_run_resumes_archive(tmp_path):
    target = tmp_path / "t.md"
    target.write_text("# T\ninstall\n", encoding="utf-8")
    out = tmp_path / "evo"
    ev, mu = toy_cmds()
    for _ in range(2):
        assert evolve.main(["--target", str(target), "--eval-cmd", ev, "--mutator-cmd", mu,
                            "--iterations", "2", "--seed", "1", "--out", str(out)]) == 0
    recs = arch.load(out / "archive.jsonl")
    assert len(recs) == 5 and sum(r["status"] == "seed" for r in recs) == 1
    assert len({r["id"] for r in recs}) == 5


def test_apply_skipped_when_no_improvement(tmp_path):
    target = tmp_path / "t.md"
    target.write_text("install usage pytest license verify\n", encoding="utf-8")
    ev, mu = toy_cmds()
    rc = evolve.main(["--target", str(target), "--eval-cmd", ev, "--mutator-cmd", mu,
                      "--iterations", "2", "--seed", "1", "--out", str(tmp_path / "evo"),
                      "--apply"])
    assert rc == 0
    assert not list(tmp_path.glob("t.md.bak-*"))
    recs = arch.load(tmp_path / "evo" / "archive.jsonl")
    assert all(r["status"] in ("seed", "discard") for r in recs)  # no-op mutations


def test_staged_eval_in_loop(tmp_path):
    """With 2+ archive members and a failing smoke task, full eval is skipped."""
    target = tmp_path / "t.md"
    target.write_text("# T\ninstall\n", encoding="utf-8")
    out = tmp_path / "evo"
    ev = f"{PY} {q(EXAMPLES / 'toy_eval.py')} {{target}} --tasks {{tasks}}"
    bad = tmp_path / "bad_mut.py"  # appends an irrelevant line -> smoke task stays 0
    bad.write_text("import sys\np=sys.argv[2]\nopen(p,'a',encoding='utf-8').write('noise\\n')\n",
                   encoding="utf-8")
    _, good = toy_cmds()
    assert evolve.main(["--target", str(target), "--eval-cmd", ev, "--mutator-cmd", good,
                        "--iterations", "2", "--seed", "0", "--out", str(out)]) == 0
    assert evolve.main(["--target", str(target), "--eval-cmd", ev,
                        "--mutator-cmd", f"{PY} {q(bad)} {{prompt}} {{target}}",
                        "--smoke-tasks", "t_verify", "--iterations", "2", "--seed", "0",
                        "--out", str(out)]) == 0
    recs = arch.load(out / "archive.jsonl")
    tail = recs[-2:]
    assert all(r["eval_stage"] == "smoke" and r["status"] == "discard" for r in tail)
    assert all(set(r["per_task"]) == {"t_verify"} for r in tail)


def test_crash_handling(tmp_path):
    target = tmp_path / "t.md"
    target.write_text("hello\n", encoding="utf-8")
    ev_script = tmp_path / "crashy_eval.py"
    ev_script.write_text(
        "import sys, json\n"
        "t = open(sys.argv[1], encoding='utf-8').read()\n"
        "if 'BOOM' in t:\n"
        "    raise SystemExit('eval exploded')\n"
        "print(json.dumps({'tasks': {'a': 0.0}, 'tokens': 1, 'feedback': {'a': 'fail'}}))\n",
        encoding="utf-8")
    mut_script = tmp_path / "boom_mut.py"
    mut_script.write_text("import sys\nopen(sys.argv[2],'a',encoding='utf-8').write('BOOM\\n')\n",
                          encoding="utf-8")
    out = tmp_path / "evo"
    rc = evolve.main(["--target", str(target),
                      "--eval-cmd", f"{PY} {q(ev_script)} {{target}}",
                      "--mutator-cmd", f"{PY} {q(mut_script)} {{prompt}} {{target}}",
                      "--iterations", "3", "--seed", "0", "--out", str(out)])
    assert rc == 0
    recs = arch.load(out / "archive.jsonl")
    assert [r["status"] for r in recs] == ["seed", "crash", "crash", "crash"]
    assert "eval exploded" in recs[1]["desc"]
    events = (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(events) == 3
    assert all(json.loads(e)["outcome"]["status"] == "failed" for e in events)


def test_mutator_failure_and_eval_timeout(tmp_path):
    target = tmp_path / "t.md"
    target.write_text("x\n", encoding="utf-8")
    ev, _ = toy_cmds()
    fail_mut = tmp_path / "fail_mut.py"
    fail_mut.write_text("raise SystemExit(3)\n", encoding="utf-8")
    out = tmp_path / "evo"
    assert evolve.main(["--target", str(target), "--eval-cmd", ev,
                        "--mutator-cmd", f"{PY} {q(fail_mut)}", "--iterations", "2",
                        "--out", str(out)]) == 0
    recs = arch.load(out / "archive.jsonl")
    assert [r["status"] for r in recs] == ["seed", "crash", "crash"]
    assert "mutator failed" in recs[1]["desc"]
    slow = tmp_path / "slow_eval.py"
    slow.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    rc = evolve.main(["--target", str(target), "--eval-cmd", f"{PY} {q(slow)}",
                      "--iterations", "0", "--eval-timeout", "1", "--out", str(tmp_path / "e2")])
    assert rc == 1
    assert arch.load(tmp_path / "e2" / "archive.jsonl")[0]["status"] == "crash"


def test_stagnant_gene_recorded_in_loop(tmp_path):
    """repair-only uses the single repair gene; after 3 failures it is excluded."""
    target = tmp_path / "t.md"
    target.write_text("hello\n", encoding="utf-8")
    ev, _ = toy_cmds()
    noop = tmp_path / "noop.py"
    noop.write_text("pass\n", encoding="utf-8")
    out = tmp_path / "evo"
    assert evolve.main(["--target", str(target), "--eval-cmd", ev,
                        "--mutator-cmd", f"{PY} {q(noop)}", "--strategy", "repair-only",
                        "--iterations", "4", "--seed", "0", "--out", str(out)]) == 0
    recs = arch.load(out / "archive.jsonl")
    genes_used = [r["mutation"]["gene_id"] for r in recs[1:]]
    assert genes_used[:3] == ["gene_gep_repair_from_errors"] * 3
    assert recs[4]["stagnant"] == ["gene_gep_repair_from_errors"]
    assert genes_used[3] != "gene_gep_repair_from_errors"


def test_cli_demo_subprocess(tmp_path):
    """The README demo command works as a real subprocess from the evolver dir."""
    target = tmp_path / "toy.md"
    target.write_text((EXAMPLES / "toy_target.md").read_text(encoding="utf-8"), encoding="utf-8")
    cmd = [sys.executable, "evolve.py", "--target", str(target),
           "--eval-cmd", f"{PY} examples/toy_eval.py {{target}}",
           "--mutator-cmd", f"{PY} examples/toy_mutator.py {{prompt}} {{target}}",
           "--iterations", "3", "--seed", "2", "--out", str(tmp_path / "o"), "--json"]
    p = subprocess.run(cmd, cwd=str(EVOLVER), capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, p.stderr
    summary = json.loads(p.stdout)
    assert summary["ok"] and summary["best"]["score"] > summary["seed_score"]
