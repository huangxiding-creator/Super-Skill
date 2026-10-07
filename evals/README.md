# Super-Skill evals

Two layers of evidence that the skill works:

| Layer | What | Cost | Command |
|---|---|---|---|
| Offline bench | 13 deterministic engine scenarios (gates, guard precision/recall, breaker, stuck detector, Ralph end-to-end) | free, ~5 s | `python .claude/skills/super-skill/evals/bench_offline.py --pretty` |
| Model evals | `claude plugin eval` cases in this folder, each run **with and without** the skill (Δ score + cost) | real API usage | `claude plugin eval . --runs 1 --case trigger-raw-idea` |

Model-eval cases (`<case>/prompt.md` + `<case>/graders/*.md`):

- `trigger-raw-idea` — a vague idea must trigger Super-Skill and a think-first front end (no immediate code).
- `no-code-before-approval` — "just build it" must still go through a plan + approval gate.

Run the full suite only when you accept the cost: `claude plugin eval . --runs 3 --no-publish`.
Results land in `evals/results/` (git-ignored).
