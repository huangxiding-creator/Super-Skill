"""Super-Skill V5 self-evolution loop.

Clean-room implementation of published ideas (no third-party code copied):
DGM archive + parent selection + staged evaluation, GEPA reflective mutation
+ Pareto front, and a simplicity criterion (fitness penalises added lines and
tokens; deletions that keep the score are kept).

Usage::

    python evolve.py --target examples/toy_target.md \
        --eval-cmd "python examples/toy_eval.py {target}" \
        --mutator-cmd "python examples/toy_mutator.py {prompt} {target}" \
        --iterations 5

Eval contract: ``--eval-cmd`` (placeholders ``{workspace} {target} {tasks}``)
prints JSON ``{"tasks": {id: score0..1}, "tokens": int, "feedback": {id: text}}``
to stdout (the last JSON object line is used). Non-zero exit, timeout or bad
JSON => the variant is recorded with status ``crash`` and the loop continues.

Outputs in ``--out`` (default ``<cwd>/.super-skill/evolve/``): ``archive.jsonl``,
``results.tsv``, ``events.jsonl`` (GEP EvolutionEvent lines), ``variants/<id>/``.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engine"))
sys.path.insert(0, str(HERE))

from ss_common import append_jsonl, force_utf8_stdio, now_iso  # noqa: E402

import archive as arch  # noqa: E402
import mutate  # noqa: E402
import strategies  # noqa: E402
from fitness import DEFAULT_CFG, clamp01, fitness, pass_rate  # noqa: E402

ARCHIVE = "archive.jsonl"
RESULTS = "results.tsv"
EVENTS = "events.jsonl"
VARIANTS = "variants"
MAX_STORED_FEEDBACK = 2000


class EvalError(Exception):
    """Evaluation crashed, timed out, or printed unusable output."""


# ------------------------------------------------------------------ eval

def parse_eval_output(stdout: str) -> Dict[str, Any]:
    """Accept either a whole-stdout JSON object or the last JSON-object line."""
    candidates: List[str] = [stdout.strip()]
    candidates += [ln.strip() for ln in reversed(stdout.splitlines()) if ln.strip().startswith("{")]
    for raw in candidates:
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("tasks"), dict):
            return {
                "tasks": {str(k): clamp01(v) for k, v in data["tasks"].items()},
                "tokens": int(data.get("tokens") or 0),
                "feedback": {str(k): str(v) for k, v in (data.get("feedback") or {}).items()},
            }
    raise EvalError("eval output has no JSON object with a 'tasks' map")


def run_eval(cmd_tpl: str, workspace: Path, target: Path, tasks: Optional[Sequence[str]],
             timeout: Optional[float], cwd: Optional[Path]) -> Dict[str, Any]:
    cmd = mutate.fill(cmd_tpl, {"workspace": str(workspace), "target": str(target),
                                "tasks": ",".join(tasks or [])})
    res = mutate.run_command(cmd, cwd=cwd, timeout=timeout, shell=True)
    if res["timed_out"]:
        raise EvalError(f"eval timed out after {timeout}s")
    if res["returncode"] != 0:
        tail = (res["stderr"] or res["stdout"]).strip().splitlines()[-3:]
        raise EvalError(f"eval exit {res['returncode']}: {' | '.join(tail)[:300]}")
    return parse_eval_output(res["stdout"])


def restrict(result: Dict[str, Any], tasks: Sequence[str]) -> Dict[str, Any]:
    keep = set(tasks)
    return {"tasks": {t: s for t, s in result["tasks"].items() if t in keep},
            "tokens": result.get("tokens", 0),
            "feedback": {t: f for t, f in (result.get("feedback") or {}).items() if t in keep}}


def staged_evaluate(evaluate: Callable[[Optional[List[str]]], Dict[str, Any]],
                    smoke_tasks: Sequence[str], threshold: float,
                    cfg: Optional[Dict[str, float]] = None,
                    lines_added: int = 0) -> Tuple[Dict[str, Any], str]:
    """DGM staged evaluation.

    With smoke tasks: evaluate them first; if the smoke fitness is below
    ``threshold`` (the archive's second-best score) stop there and return
    stage ``"smoke"``. Otherwise (or without smoke tasks) run the full suite
    and return stage ``"full"``. ``evaluate(None)`` means "all tasks".
    """
    if smoke_tasks:
        smoke = restrict(evaluate(list(smoke_tasks)), smoke_tasks)
        smoke["lines_added"] = lines_added
        if fitness(smoke, cfg) < threshold:
            return smoke, "smoke"
    full = evaluate(None)
    full["lines_added"] = lines_added
    return full, "full"


# ------------------------------------------------------------------ helpers

def next_id(archive: List[dict]) -> str:
    nums = [int(m.group(1)) for r in archive
            for m in [re.match(r"^v(\d+)$", str(r.get("id", "")))] if m]
    return f"v{(max(nums) + 1) if nums else 0:04d}"


def _clip_feedback(fb: Dict[str, str]) -> Dict[str, str]:
    return {k: (v if len(v) <= MAX_STORED_FEEDBACK else v[:MAX_STORED_FEEDBACK] + "...")
            for k, v in (fb or {}).items()}


def _tsv(s: Any) -> str:
    return re.sub(r"[\t\r\n]+", " ", "" if s is None else str(s))


def append_result(out: Path, rec: dict, gene_id: str) -> None:
    path = out / RESULTS
    new = not path.exists()
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        if new:
            fh.write("id\tparent\tgene\tscore\tstatus\tdesc\n")
        score = "" if rec.get("score") is None else f"{float(rec['score']):.6f}"
        fh.write("\t".join(_tsv(x) for x in (rec["id"], rec.get("parent") or "-", gene_id or "-",
                                            score, rec["status"], rec.get("desc", ""))) + "\n")


def make_event(rec: dict, parent: Optional[dict], signals: List[str], run_id: str) -> dict:
    mut = rec.get("mutation") or {}
    return {
        "type": "EvolutionEvent",
        "schema_version": "1.5.0",
        "id": rec["event_id"],
        "parent": (parent or {}).get("event_id"),
        "intent": mut.get("intent"),
        "signals": signals,
        "genes_used": [mut["gene_id"]] if mut.get("gene_id") else [],
        "mutation_id": f"mut_{run_id}_{rec['id']}",
        "blast_radius": mut.get("blast_radius") or {"files": 0, "lines": 0},
        "outcome": {"status": "success" if rec["status"] in ("keep", "seed") else "failed",
                    "score": rec.get("score")},
        "timestamp": now_iso(),
        "meta": {"variant_id": rec["id"], "parent_variant": rec.get("parent"),
                 "variant_status": rec["status"], "target": rec.get("target"),
                 "source": "super-skill/evolver"},
    }


def variant_file(out: Path, rec: dict) -> Path:
    return out / rec["workspace"] / rec["target"]


def apply_best(out: Path, target: Path, archive: List[dict], log=print) -> Optional[dict]:
    """Copy the best keep variant over ``target`` iff it beats the seed.
    A backup ``<target>.bak-<ts>`` is written first."""
    seed = next((r for r in archive if r.get("status") == "seed"), None)
    top = arch.best(archive, ("keep",))
    if not seed or not top or float(top["score"]) <= float(seed["score"]) + arch.EPS:
        log("apply: no keep variant beats the seed; target left unchanged")
        return None
    src = variant_file(out, top)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target.with_name(f"{target.name}.bak-{ts}")
    shutil.copy2(str(target), str(backup))
    shutil.copyfile(str(src), str(target))
    log(f"apply: {top['id']} (score {top['score']:.4f} > seed {seed['score']:.4f}) -> {target}"
        f"; backup {backup.name}")
    return {"variant": top["id"], "backup": str(backup), "score": top["score"]}


# ------------------------------------------------------------------ loop

def evolve(target: Path, eval_cmd: str, mutator: Optional[str], out: Path,
           iterations: int = 5, strategy: str = "balanced",
           smoke_tasks: Sequence[str] = (), seed: Optional[int] = None,
           cfg: Optional[Dict[str, float]] = None, leeway: float = 0.0,
           selection: str = "dgm", eval_timeout: float = 600,
           mutator_timeout: float = 900, budget_usd: float = 0.5,
           cwd: Optional[Path] = None, genes_file: Optional[Path] = None,
           do_apply: bool = False, log: Callable[[str], None] = print) -> Dict[str, Any]:
    target = Path(target).resolve()
    out = Path(out).resolve()
    cwd = Path(cwd or Path.cwd()).resolve()
    cfg = {**DEFAULT_CFG, **(cfg or {})}
    rng = random.Random(seed)
    genes = strategies.load_genes(genes_file)
    strategies.get_weights(strategy)  # validate early
    if iterations > 0 and not mutator:
        raise ValueError("--mutator-cmd is required when --iterations > 0")
    (out / VARIANTS).mkdir(parents=True, exist_ok=True)
    apath = out / ARCHIVE
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    tname = target.name

    def evaluator(ws: Path, tfile: Path):
        cache: Dict[str, Any] = {}

        def evaluate(tasks: Optional[List[str]]) -> Dict[str, Any]:
            if "{tasks}" not in eval_cmd:  # eval can't subset: run once, reuse
                if "full" not in cache:
                    cache["full"] = run_eval(eval_cmd, ws, tfile, None, eval_timeout, cwd)
                return json.loads(json.dumps(cache["full"]))
            return run_eval(eval_cmd, ws, tfile, tasks, eval_timeout, cwd)
        return evaluate

    # ---- seed (unmodified target), evaluated first
    archive = arch.load(apath)
    if not any(r.get("status") == "seed" for r in archive):
        vid = next_id(archive)
        ws = out / VARIANTS / vid
        ws.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(target), str(ws / tname))
        rec: Dict[str, Any] = {
            "id": vid, "parent": None, "created": now_iso(),
            "workspace": f"{VARIANTS}/{vid}", "target": tname, "source": str(target),
            "children": 0, "lines_added": 0, "lines_removed": 0,
            "desc": "seed (unmodified target)", "mutation": None,
            "event_id": f"evt_{int(time.time() * 1000)}_{vid}",
        }
        try:
            res = evaluator(ws, ws / tname)(None)
            res["lines_added"] = 0
            rec.update(status="seed", eval_stage="full", score=fitness(res, cfg),
                       per_task=res["tasks"], tokens=res["tokens"],
                       feedback=_clip_feedback(res["feedback"]))
        except EvalError as exc:
            rec.update(status="crash", eval_stage="none", score=None, per_task={},
                       tokens=0, feedback={}, desc=f"seed eval crashed: {exc}")
        arch.append(apath, rec)
        append_result(out, rec, "")
        log(f"[{vid}] seed score={rec['score']} status={rec['status']}")
        if rec["status"] == "crash":
            return {"ok": False, "error": rec["desc"], "out": str(out)}

    for _ in range(iterations):
        archive = arch.load(apath)
        parent = arch.select_parent(archive, rng, selection)
        if parent is None:
            log("no selectable parent (keep/seed) in archive; stopping")
            break
        stagnant = sorted(strategies.detect_stagnation(strategies.history_from_archive(archive)))
        signals = strategies.extract_signals(parent.get("per_task"), parent.get("feedback"), genes)
        if stagnant:
            signals = sorted(set(signals) | {"evolution_stagnation_detected"})
        gene, intent = strategies.pick_gene(strategy, genes, signals, rng, exclude=stagnant)

        vid = next_id(archive)
        ws = out / VARIANTS / vid
        ws.mkdir(parents=True, exist_ok=True)
        tfile = ws / tname
        shutil.copyfile(str(variant_file(out, parent)), str(tfile))
        parent_text = tfile.read_text(encoding="utf-8", errors="replace")
        failed = sorted(t for t, s in (parent.get("per_task") or {}).items() if float(s) < 1.0)

        prompt = mutate.build_prompt(parent_text, tname, parent.get("per_task") or {},
                                     parent.get("feedback") or {}, gene, intent)
        ppath = mutate.write_prompt(ws, prompt)
        mres = mutate.run_mutator(mutator, ppath, ws, tfile, timeout=mutator_timeout,
                                  budget_usd=budget_usd, cwd=cwd)
        archive = arch.update_children(apath, parent["id"])

        rec = {
            "id": vid, "parent": parent["id"], "created": now_iso(),
            "workspace": f"{VARIANTS}/{vid}", "target": tname, "source": str(target),
            "children": 0, "score": None, "per_task": {}, "tokens": 0, "feedback": {},
            "lines_added": 0, "lines_removed": 0, "eval_stage": "none",
            "stagnant": stagnant,
            "event_id": f"evt_{int(time.time() * 1000)}_{vid}",
            "mutation": {
                "gene_id": gene.get("id"), "intent": intent, "target_files": [tname],
                "expected_signal": (f"raise score on: {', '.join(failed)}" if failed
                                    else "keep score while simplifying"),
                "blast_radius": {"files": 0, "lines": 0},
            },
        }
        if mres["timed_out"] or mres["returncode"] != 0:
            why = "timeout" if mres["timed_out"] else f"exit {mres['returncode']}"
            tail = " | ".join((mres["stderr"] or "").strip().splitlines()[-2:])[:200]
            rec.update(status="crash", desc=f"mutator failed ({why}) {tail}".strip())
        else:
            new_text = tfile.read_text(encoding="utf-8", errors="replace")
            stats = mutate.diff_stats(parent_text, new_text)
            rec.update(stats)
            rec["mutation"]["blast_radius"] = {
                "files": 1 if new_text != parent_text else 0,
                "lines": stats["lines_added"] + stats["lines_removed"]}
            desc = mutate.read_desc(ws) or f"{gene.get('id')} ({intent})"
            if new_text == parent_text:
                rec.update(status="discard", desc=f"no-op mutation: {desc}")
            else:
                threshold = arch.second_best_score(archive)
                try:
                    res, stage = staged_evaluate(evaluator(ws, tfile), list(smoke_tasks),
                                                 threshold, cfg, stats["lines_added"])
                    rec.update(score=fitness(res, cfg), per_task=res["tasks"],
                               tokens=res["tokens"], feedback=_clip_feedback(res["feedback"]),
                               eval_stage=stage)
                    if stage == "smoke":
                        rec.update(status="discard",
                                   desc=f"{desc} [smoke {rec['score']:.4f} < 2nd-best "
                                        f"{threshold:.4f}; full eval skipped]")
                    else:
                        ok = arch.is_improvement(rec, parent, leeway)
                        rec.update(status="keep" if ok else "discard", desc=desc)
                except EvalError as exc:
                    rec.update(status="crash", desc=f"{desc} [eval crashed: {exc}]")

        arch.append(apath, rec)
        append_result(out, rec, gene.get("id"))
        append_jsonl(out / EVENTS, make_event(rec, parent, signals, run_id))
        sc = "-" if rec["score"] is None else f"{rec['score']:.4f}"
        log(f"[{vid}] parent={parent['id']} gene={gene.get('id')} score={sc} "
            f"status={rec['status']} {rec['desc']}")

    archive = arch.load(apath)
    top = arch.best(archive)
    seed_rec = next((r for r in archive if r.get("status") == "seed"), None)
    summary: Dict[str, Any] = {
        "ok": True, "out": str(out), "variants": len(archive),
        "seed_score": seed_rec.get("score") if seed_rec else None,
        "best": {"id": top["id"], "score": top["score"],
                 "pass_rate": pass_rate(top.get("per_task"))} if top else None,
        "pareto_front": [r["id"] for r in arch.pareto_front(archive)],
        "counts": {s: sum(1 for r in archive if r.get("status") == s)
                   for s in ("seed", "keep", "discard", "crash")},
        "applied": None,
    }
    if do_apply:
        summary["applied"] = apply_best(out, target, archive, log=log)
    return summary


# ------------------------------------------------------------------ CLI

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="evolve.py",
        description="Evolve a text target (e.g. a SKILL.md) with a DGM/GEPA-style loop.")
    ap.add_argument("--target", required=True, help="file to evolve")
    ap.add_argument("--eval-cmd", required=True,
                    help='command with {workspace} {target} {tasks}; prints JSON '
                         '{"tasks":{id:score},"tokens":int,"feedback":{id:text}}')
    ap.add_argument("--mutator-cmd",
                    help='command with {prompt} {workspace} {target}, or the literal '
                         '"claude" for the built-in Claude Code mutator')
    ap.add_argument("--smoke-tasks", default="", help="comma list evaluated first (staged eval)")
    ap.add_argument("--iterations", type=int, default=5)
    ap.add_argument("--strategy", default="balanced", choices=sorted(strategies.PRESETS))
    ap.add_argument("--selection", default="dgm", choices=["dgm", "pareto"])
    ap.add_argument("--out", help="output dir (default <cwd>/.super-skill/evolve/)")
    ap.add_argument("--seed", type=int, default=None, help="rng seed")
    ap.add_argument("--lambda", dest="lam", type=float, default=DEFAULT_CFG["lambda"],
                    help="token penalty weight (per 1e5 tokens)")
    ap.add_argument("--mu", type=float, default=DEFAULT_CFG["mu"],
                    help="added-lines penalty weight (per 100 lines)")
    ap.add_argument("--leeway", type=float, default=0.0,
                    help="keep a child if score > parent - leeway")
    ap.add_argument("--eval-timeout", type=float, default=600)
    ap.add_argument("--mutator-timeout", type=float, default=900)
    ap.add_argument("--budget-usd", type=float, default=0.5, help="per-call budget (claude)")
    ap.add_argument("--genes", help="genes.json path (default assets/gep/genes.json)")
    ap.add_argument("--apply", action="store_true",
                    help="copy best keep variant over target if it beats the seed (backup first)")
    ap.add_argument("--json", action="store_true", help="print the summary as JSON")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    force_utf8_stdio()
    args = build_parser().parse_args(argv)
    target = Path(args.target)
    if not target.is_file():
        print(f"error: target not found: {target}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else Path.cwd() / ".super-skill" / "evolve"
    smoke = [t.strip() for t in args.smoke_tasks.split(",") if t.strip()]
    log = (lambda s: print(s, file=sys.stderr)) if args.json else print
    try:
        summary = evolve(target, args.eval_cmd, args.mutator_cmd, out,
                         iterations=args.iterations, strategy=args.strategy,
                         smoke_tasks=smoke, seed=args.seed,
                         cfg={"lambda": args.lam, "mu": args.mu}, leeway=args.leeway,
                         selection=args.selection, eval_timeout=args.eval_timeout,
                         mutator_timeout=args.mutator_timeout, budget_usd=args.budget_usd,
                         genes_file=Path(args.genes) if args.genes else None,
                         do_apply=args.apply, log=log)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif summary.get("ok"):
        b = summary.get("best")
        print(f"done: {summary['variants']} variants {summary['counts']}; "
              f"seed={summary['seed_score']} best={b['id'] if b else '-'} "
              f"score={b['score'] if b else '-'}; pareto={summary['pareto_front']}")
    else:
        print(f"failed: {summary.get('error')}", file=sys.stderr)
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
