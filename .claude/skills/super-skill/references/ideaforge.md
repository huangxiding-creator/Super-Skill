# IdeaForge — Method & Algorithms (Super-Skill V4.0 reference)

The front-end that turns a raw idea into a falsifiable 10× proposal. Loaded on demand from [SKILL.md](../SKILL.md).

## Why it exists
V3.x required a clear spec to start. Users usually only have a hunch (often a voice transcript). IdeaForge extends Super-Skill backwards to the moment of the hunch, then hands off to the unchanged 14-phase pipeline.

## The three stages

### 1. idea-intake — Hybrid Clarification Gate
Score the raw idea on 5 fields (0/1/2 each, max 10): `persona`, `pain`, `constraints`, `success_form`, `value_hypothesis`.
- ≥8 → **auto** (note assumptions, proceed)
- 4–7 → **ask** (one batch of ≤3 questions on the weakest fields, each with an AI default)
- ≤3 → **sharpen** (push back; idea too vague)

Script: [skills/idea-intake/scripts/ambiguity_scorer.py](../skills/idea-intake/scripts/ambiguity_scorer.py) (8 tests). Output: `IDEA_SEED.md`.

### 2. research-orchestrator — 9 channels + gap analysis
Pluggable channels, uniform `Channel.harvest(seed)→[Doc]`, 3-level fallback, **never raises** (a blocked channel emits a `degraded` note and the run continues). Channels: `github`, `sogou_wechat`, `hackernews`, `npm_pypi`, `appstore`, `reddit`, `producthunt` (needs `PRODUCTHUNT_TOKEN`), `googletrends` (no free API → degrades), `competitor_site`.

Post-harvest: dedup (title-normalize + content-hash) → quality gate (min docs, degraded ratio, avg credibility) → **gap analysis** (proposal-dimension × evidence coverage matrix → targeted re-research on weak dims) → checkpoint (resume). Output: `RESEARCH_DOCKET/`, `RESEARCH_DIGEST.md`, `GAP_REPORT.md`, `_quality.json`.

Borrows the orchestration *architecture* from ResearchFactory-Eng (`survey_runner`/`gap_analyzer`/`deduper`/`quality_gate`/`checkpoint`) — **not** its EPC channels, which are irrelevant to software ideas.

### 3. proposal-forge — the 10× gate
Four deterministic scorers:

| Scorer | What it computes | Gate |
|---|---|---|
| `maturity_index` | repo/landscape 0–100 (recency 0.25 · adoptability 0.25 · health 0.20 · ecosystem 0.15 · license 0.15) | → feasibility |
| `tenx_delta_index` | `max_axis log10(ours/best_existing)` | ≥1.0 = tenx_qualified; 0.3–1.0 = incremental; <0.3 = red_ocean |
| `pricing` | price bands from competitor prices → recommend by positioning (cost_leader/value/premium) | data-backed price |
| `scorecard` | weighted: feasibility 0.25 · user_value 0.30 · monetization 0.20 · tenx 0.25 | ≥0.72 proceed · ≥0.55 revise · else reject |

The **ten× delta index** is the heart: "ten-times-better" stops being a slogan — if no axis shows ≥10×, the verdict is `incremental` and the proposal does not proceed until a new angle is found. This is the falsifiable kill-switch that stops CC from burning dev cycles on incremental ideas.

Output: `PROPOSAL.md`, `BUSINESS_MODEL.md`, `SCORECARD.json`.

## Approval Gate (interaction point ✋)
On `proceed`: present the proposal once → approve / revise / reject. Approve → auto-populate `VISION.md`/`REQUIREMENTS.md`/`ARCHITECTURE.md` → Phase 0. This is the only new human touchpoint; after it the pipeline is fully autonomous as before.

## Data contracts
```
IDEA_SEED.md ─▶ research-orchestrator ─▶ RESEARCH_DOCKET/**/_all.json
                                          └─▶ proposal-forge ─▶ PROPOSAL.md + BUSINESS_MODEL.md + SCORECARD.json
                                                                └─▶ [Approval Gate] ─▶ Phase 0
```

## Honesty contract (critical)
Degraded channels never silently fabricate data. A blocked Sogou returns a low-credibility `degraded` note; `user_value` (the one LLM-judged dimension) is capped at 0.5 when there is no pain evidence. Proposals are evidence-backed or they don't proceed.

## Tests
- idea-intake: 8 · research-orchestrator: 20 (M1 9 + M3 11) · proposal-forge: 15 scoring + 13 pricing = **56+ checks green**
- Live-verified channels: github, npm_pypi, appstore, hackernews
