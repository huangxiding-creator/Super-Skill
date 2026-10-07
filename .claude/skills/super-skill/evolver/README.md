# Super-Skill V5 Evolver / 自进化引擎

用评测驱动的进化循环改进一个文本目标文件（如 `SKILL.md`）。
An evaluation-driven evolution loop for a text target (e.g. a `SKILL.md`).
Python 3.9+, stdlib only, Windows + Linux.

## Quick start / 快速上手

```bash
cd .claude/skills/super-skill/evolver
python evolve.py --target examples/toy_target.md \
  --eval-cmd "python examples/toy_eval.py {target}" \
  --mutator-cmd "python examples/toy_mutator.py {prompt} {target}" \
  --iterations 5 --seed 1
```

Real use with Claude Code as the mutator. You must choose this explicitly, and it costs money:

```bash
python evolve.py --target ../SKILL.md --eval-cmd "python my_eval.py {target} --tasks {tasks}" \
  --mutator-cmd claude --budget-usd 0.5 --smoke-tasks t1,t2 --iterations 10 --apply
```

| Option | Meaning |
|---|---|
| `--target PATH` | File to evolve. The original is never touched unless you pass `--apply`. |
| `--eval-cmd` | Placeholders are `{workspace} {target} {tasks}`. It must print `{"tasks":{id:0..1},"tokens":int,"feedback":{id:"text"}}`. |
| `--mutator-cmd` | Placeholders are `{prompt} {workspace} {target}`. The literal `claude` runs `claude -p --max-turns 8 --max-budget-usd <b> --permission-mode acceptEdits` with cwd set to the variant dir. |
| `--smoke-tasks a,b` | Staged eval: the smoke tasks run first, and the full suite runs only if the smoke score is at least the archive's 2nd-best score. |
| `--strategy` | `balanced` (.34/.33/.33), `innovate` (.2/.2/.6), `harden` (.5/.4/.1), `repair-only`. The weights are for repair/optimize/innovate. |
| `--selection` | `dgm` (default) or `pareto` (parents come only from the GEPA Pareto front). |
| `--lambda --mu --leeway` | Fitness weights and the keep tolerance. |
| `--out DIR` | Default is `<cwd>/.super-skill/evolve/`. A rerun with the same `--out` resumes the archive. |
| `--apply` | Copies the best `keep` variant over the target, but only if it beats the seed. It writes `target.bak-<ts>` first. |
| `--json` | Prints the summary as JSON; logs go to stderr. |

Commands run from the invoking cwd, except the `claude` mutator, which runs in the variant dir.

## Loop / 循环

The seed is the unmodified target, and it is evaluated first. Each iteration then runs these steps:

1. **Select a parent (DGM).** Parents come from the `keep`/`seed` variants, each weighted by `sigmoid(10·(score−0.5)) / (1+children)`.
2. **Pick a gene.** Draw a category using the strategy weights. Within it, take the gene from `assets/gep/genes.json` whose `signals_match` hits the most current failure signals. **Stagnation:** a gene used 3 times in a row with no improvement is excluded for the next round and recorded as `stagnant`.
3. **Set up the workspace.** The parent's file is copied into `variants/<id>/`.
4. **Write the reflective prompt (GEPA).** The prompt goes to `MUTATION_PROMPT.md`. It holds the parent text (or only the most relevant section if the file is large), the failed tasks with evaluator feedback (ASI), the gene strategy, and the simplicity rule: "smallest change, change ONE section, deleting text that keeps score is a win".
5. **Run the mutator.** It edits the copy in place and may write `MUTATION_DESC.txt`.
6. **Evaluate.** `lines_added`/`lines_removed` are counted with difflib, then the staged eval runs.
7. **Keep or discard.** The child is `keep` if it beats its parent (or ties while shrinking the file), otherwise `discard`. An eval or mutator failure or timeout gives `crash`, and the loop continues.
8. **Log.** The iteration is appended to `archive.jsonl`, `results.tsv` (`id parent gene score status desc`) and `events.jsonl` (GEP `EvolutionEvent`).

## Fitness / 适应度

```
fitness = pass_rate − λ·(tokens/1e5) − μ·(lines_added/100)     # λ=0.05, μ=0.02
```

`pass_rate` is the mean per-task score in [0,1]. Added tokens and lines must be paid for by real gains.
This follows the autoresearch-style simplicity criterion (pattern only): a change that deletes lines and keeps the score is also kept.

## Clean-room note / 洁净室声明

autogame-17/evolver is GPL-3.0. **None of its code was fetched or copied.** This module is written from these published algorithm descriptions:

- **DGM** (jennyzzt/dgm, Apache-2.0): the archive of all variants, the parent weighting, and staged evaluation.
- **GEPA** (gepa-ai/gepa, MIT): reflective mutation from failure feedback, and the Pareto front.
- **autoresearch**: the simplicity criterion (pattern only).

It reuses only this repo's own GEP assets (`genes.json`, the EvolutionEvent shape).

## Files

`fitness.py` · `archive.py` · `strategies.py` · `mutate.py` · `evolve.py` · `examples/` (toy eval/mutator/target) · `tests/`

Run the tests with `python -m pytest -q tests`.
