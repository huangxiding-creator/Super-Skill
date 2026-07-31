# AI-Mastery Protocol — Boris Cherny's 7 Disciplines

> **Source**: distilled from Boris Cherny's (creator of Claude Code) talk on extracting AI
> capability. Boris notes Anthropic compresses new-hire onboarding from 2–3 **weeks** to 2–3
> **days** by pointing Claude at the company knowledge base — most users extract <1% of their
> AI's value. The fix is a mindset shift: **don't treat AI as a tool — it's an autonomous
> agent; give it context + tools and let it run the whole workflow.**
>
> Integration home: [`skills/ai-mastery-7/SKILL.md`](../skills/ai-mastery-7/SKILL.md).

This reference maps each of the 7 disciplines to the Super-Skill mechanism that already
implements it, marks the **gaps** that V4.1 fills, and gives deeper operational protocols
for the disciplines that are prompts rather than scripts.

## Mapping at a glance

| # | Discipline (Boris) | Super-Skill mechanism | Status before V4.1 | V4.1 change |
|---|-------------------|----------------------|-------------------|-------------|
| 1 | Let AI teach you how to use itself | onboarding dialog | gap | **protocol added** (ai-mastery-7) |
| 2 | Domain onboarding via KB Q&A | Phase 3 KB · `continuous-learning-v2` | exists | documented |
| 3 | Understand history → understand "why" | git-as-experiment-tracker | gap | **`rationale_mining.py`** added |
| 4 | Weekly retrospective from logs | `post-run-evolution` (session) · `extract_log.js` | gap (week-level) | **`weekly_retrospective.py`** added |
| 5 | Plan before code | Phase 4 gate · `brainstorming` | exists | reinforced as guardrail |
| 6 | Feedback tools → self-iteration | `verification-gate` · Phase 10 Ralph Loop · TDD | exists | reinforced |
| 7 | Long-term memory / CLAUDE.md | `memory-pipeline` · `cerebrum` · MEMORY.md | exists | documented |

**Net**: 3 genuine gaps closed (D1, D3, D4); 4 existing strengths named and cross-linked so
they're discoverable as one coherent mastery curriculum rather than scattered features.

## Deeper protocols

### Discipline 1 — Onboarding dialog (calibrate capability boundaries)

> "你该怎么使用你？什么样的问题你能一次搞定？什么样的需要分几步？你的能力边界在哪里？"

Run **once per new user/project**, before assigning real work:

1. **Self-interview the agent.** Ask it to enumerate, *for this skill tree*: what it can do
   in one shot, what needs 2–3 steps, what needs interactive help, where its hard limits are.
2. **Map to the goal.** Point the agent at [`references/skills-matrix.md`](skills-matrix.md)
   and ask it to name the 3–5 skills most relevant to the user's stated goal, and what each
   will *not* do.
3. **Persist the boundary.** Write the agreed capability boundary + preferred workflow into
   `CLAUDE.md` (Discipline 7). Future sessions start calibrated.

**Why this beats tutorials**: a tutorial is *someone else's* calibration. A direct dialog is
real-time calibration to *your* scenario — strictly faster, and it doubles as prompt-practice.

### Discipline 5 — Plan-before-code guardrail

> Boris: "先构思几个方案，做个计划，跑给我看，等我同意了你再写代码。"

The anti-pattern to block: "just build X" with no plan. Super-Skill already enforces this at
the **Phase 4 approval gate** and via `brainstorming`; V4.1 makes it a named, reusable rule:

- **One-line guardrail** (inject when the user says "just build X"):
  > "写代码之前先做个计划，跑给我看，同意了你再写。"
- **Multi-step intent** → the "咒语" `commit push PR` is enough. A strong agent chains git
  tools itself (style, history, commit format) — do not hand-hold.
- **Anti-rationalization** (from `high-agency`): never accept "I can't" without evidence the
  agent exhausted its options. Symmetrically, never accept "I'll just start coding" without a
  plan when the task is non-trivial.

### Discipline 6 — Feedback-loop harness (verifier > generator)

> Give the agent a way to *see its own output*; it iterates to near-perfect in 2–3 rounds.

**Variance inequality** (Super-Skill core philosophy): when improvement stalls, strengthen
the **verifier**, not the generator. Concretely, wire one of these into every non-trivial task:

| Task type | Verifier to wire in |
|-----------|--------------------|
| UI work | `design-qc` sectioned screenshots, Playwright |
| Library code | unit tests + `verification-gate` read-only challenge |
| Refactor | behavior-equality tests before/after |
| Docs | a checklist the agent self-runs |
| Migration | exact scripts + idempotency check |

Phase 10 (Ralph Loop) operationalizes the round-robin: Analyze → Improve → Validate → Document
→ check convergence. The discipline says: **never ship a task that has no verifier** — an
agent without feedback stops at "八九不离十"; with feedback it converges.

## Anti-patterns (what the 7 disciplines forbid)

- **Tool-thinking**: "what prompt do I type?" → wrong question. Ask "what context + tools do I
  hand the agent so it runs the whole workflow?"
- **Drive-by coding**: "just build X" → blocked by D5.
- **Fuzzy retrospectives**: "I was busy this week" → replaced by D4's clear list.
- **Mechanical techniques**: applying a pattern without knowing *why* → replaced by D3.
- **Memory amnesia**: re-explaining the project every session → replaced by D7.
- **Verifier-free work**: shipping "八九不离十" without a feedback loop → blocked by D6.

## Script reference

Both scripts are pure-stdlib, offline, deterministic, and UTF-8-safe on Windows.

```bash
# D4 — weekly retrospective
python skills/ai-mastery-7/scripts/weekly_retrospective.py                 # this week
python skills/ai-mastery-7/scripts/weekly_retrospective.py --since 14 --area src --json

# D3 — rationale timeline
python skills/ai-mastery-7/scripts/rationale_mining.py path/to/file.py     # markdown
python skills/ai-mastery-7/scripts/rationale_mining.py path/to/file.py --max 5 --json
```

Tests: `skills/ai-mastery-7/scripts/test_ai_mastery.py` (11 cases, runs on a temp git repo —
discovered automatically by `scripts/health_check.py`).

## How it was validated

- 11/11 unit tests green (including a Windows UTF-8 regression for non-ASCII commit messages).
- Live smoke test on this repo: weekly retrospective correctly buckets commits;
  rationale miner produces origin + formative + blame-segment map for a real file.
