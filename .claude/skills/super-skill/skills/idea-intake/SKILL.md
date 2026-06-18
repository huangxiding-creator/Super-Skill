---
name: idea-intake
description: IdeaForge Stage 1. Ingest a raw idea (text/attachment/voice transcript), ambiguity-score it, and run the Hybrid Clarification Gate. Use FIRST, before any research, whenever the user gives an undeveloped idea instead of a spec.
---

# idea-intake — Idea Intake & Hybrid Clarification Gate

**Stage 1 of the Idea Factory.** Turns a fuzzy idea into a structured, investment-grade `IDEA_SEED.md` with the *minimum* questions asked.

## Philosophy

- **Autonomy-first**: most ideas can be extracted autonomously. We only interrupt when ambiguity is *measurably* high.
- **Score, don't guess**: a deterministic scorer decides whether to proceed, ask, or push back.
- **One shot**: when we do ask, it's a single batch of ≤3 questions — never a back-and-forth.

## Workflow

```
raw idea (text | attachment | transcript)
   │
   ▼
1. EXTRACT  → pull the 5 canonical fields (see below)
   │          (autonomous; best-effort from whatever the user gave)
   ▼
2. SCORE    → python scripts/ambiguity_scorer.py <idea> --fields
   │          returns {score 0..10, action: auto|ask|sharpen, questions_on[], assumptions[]}
   ▼
3. GATE (Hybrid Clarification)
   ├─ action == "auto"     → proceed to research-orchestrator (note assumptions in IDEA_SEED)
   ├─ action == "ask"      → ask the ≤3 questions ONCE (with AI-proposed defaults),
   │                          fold answers in, re-score, then proceed
   └─ action == "sharpen"  → idea too vague; tell the user which fields are empty,
                             give a concrete sharpening example, stop
   ▼
4. EMIT     → IDEA_SEED.md (the contract research-orchestrator consumes)
```

## The 5 canonical fields

| Field | Question it answers | Strong (score 2) example |
|---|---|---|
| `persona` | Who specifically? | "独立跨境电商运营" |
| `pain` | What concrete pain, when/where? | "选品时要手工翻5个平台比价，每天2小时" |
| `constraints` | Hard non-negotiables? | "必须离线、兼容Win10、数据不出本地" |
| `success_form` | What shape = done? | "桌面 SaaS + 浏览器插件" |
| `value_hypothesis` | Why now / why 10×? | "GPT-4o 多模态刚成熟，可自动比价，比人工快10×" |

## Scorer thresholds (tunable in ambiguity_scorer.py)

| Total | Action |
|---|---|
| ≥ 8 | **auto** — proceed, assumptions noted |
| 4–7 | **ask** — one batch of ≤3 questions (weakest fields) |
| ≤ 3 | **sharpen** — push back, idea too vague |

## How to ask (only when action == "ask")

- Ask **once**, all questions in a single message.
- Every question includes an **AI-proposed default** the user can one-tap accept.
- Never exceed 3 questions. If more fields are weak, the rest become *assumptions* flagged in IDEA_SEED.

Use `render_questions(result)` from the scorer for default wording; refine to the idea's context.

## IDEA_SEED.md contract

```markdown
# IDEA_SEED
summary: <one-line>
persona: <...>
pain: <...>
constraints: <...>
success_form: <...>
value_hypothesis: <...>
assumptions:   # fields scored 0 that we proceeded on; user confirms at Proposal Gate
  - <assumption 1>
  - <assumption 2>
ambiguity_score: <0..10>
intake_action: <auto|ask|sharpen>
source: <text|attachment|transcript>
```

## Files

- [scripts/ambiguity_scorer.py](scripts/ambiguity_scorer.py) — deterministic scorer + CLI
- [scripts/test_ambiguity_scorer.py](scripts/test_ambiguity_scorer.py) — 8 tests, all green

## Integration

- **Feeds**: [research-orchestrator](../research-orchestrator/SKILL.md) consumes `IDEA_SEED.md`
- **Part of**: Idea Factory (see [references/ideaforge.md](../../references/ideaforge.md))
