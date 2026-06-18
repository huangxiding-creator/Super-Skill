# IdeaForge (Super-Skill V4.0) — Architecture

> Idea-driven software factory, bolted onto V3.21. Turns a vague idea into a deployable, monetizable product with zero mid-flow interaction (except the Proposal Approval Gate).

## Layered design

```
┌─ IDEA FACTORY (new front-end) ─────────────────────────────────────────┐
│ idea-intake → research-orchestrator → proposal-forge → [Approval Gate] │
└────────────────────────────────────────────────────────────────────────┘
                                  ↓ feeds Phase 0–4 docs
┌─ V3.21 BACKBONE (kept) ─────────────────────────────────────────────────┐
│ Vision → Feasibility → Knowledge → Requirements → Architecture → WBS   │
│ → Init → Autonomous Dev → QA → Ralph → Deploy(+monetization-scaffold)  │
└────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─ EVOLUTION (enhanced) ──────────────────────────────────────────────────┐
│ proposal outcome → GEP winning-pattern KB; health-check hook refreshes  │
└────────────────────────────────────────────────────────────────────────┘
```

## New sub-skills (in skills/)

| Sub-skill | Type | Responsibility | Key artifact |
|---|---|---|---|
| `idea-intake` | prose + script | Ingest idea (text/attachment), ambiguity-score, hybrid clarification gate | `IDEA_SEED.md` |
| `research-orchestrator` | prose + scripts | Pluggable channels, per-channel strategy, gap analysis, dedup, quality gate, checkpoint | `RESEARCH_DOCKET/`, `RESEARCH_DIGEST.md` |
| `proposal-forge` | prose + scripts | Synthesize → maturity/tenx/blue-ocean/pricing → scorecard + gate | `PROPOSAL.md`, `BUSINESS_MODEL.md` |
| `monetization-scaffold` | prose + templates | Stripe/Docker/CI-CD/API-gateway/one-command deploy generator | scaffold files |

## Channels (research-orchestrator/scripts/channels/)

Uniform interface `Channel.harvest(seed) -> list[Doc]`. Each has 3-level fallback + cache.

`github`, `sogou_wechat`, `reddit`, `hackernews`, `producthunt`, `appstore`, `googletrends`, `npm_pypi`, `competitor_site`.

## Core algorithms (deterministic Python, so they're testable & non-hallucinated)

1. **Ambiguity score** (idea-intake): 5 fields × {0,1,2} → [0,10]; ≥8 auto, 4–7 ask ≤3, ≤3 sharpen.
2. **Maturity index** (proposal-forge): weighted 0–100 from GitHub+ecosystem signals.
3. **TenX delta index** (proposal-forge): `max_axis log10(ours/best_existing)`; ≥1.0 = tenx-qualified.
4. **Proposal scorecard**: feasibility25 · value30 · monetization20 · tenx25; ≥0.72 → gate.

## Data contract between stages

```
IDEA_SEED.md        # {summary, persona, pain, constraints, success_form, value_hypothesis, assumptions[], score}
  ↓
RESEARCH_DOCKET/    # per-channel subdir of harvested docs (markdown)
RESEARCH_DIGEST.md  # synthesized: pains[], competitors[], signals[], coverage_matrix, gaps[]
  ↓
PROPOSAL.md         # pitch + differentiators + maturity + tenx + blue-ocean + mvp_scope
BUSINESS_MODEL.md   # pricing_model + price_band (data-backed) + cac + compliance + billing_ui
SCORECARD.json      # {feasibility, value, monetization, tenx, weighted, verdict}
  ↓ [Approval Gate: human]
VISION/REQUIREMENTS/ARCHITECTURE... (auto-populated for V3.21 Phase 0–4)
```

## Reused from ResearchFactory-Eng (architecture, not channels)

gap-analysis coverage matrix, dedup (title-normalize + content-hash), smart-packer (≤N files), quality-gate (摘要质检), checkpoint (resume), per-channel GLM strategy-matrix idea.

## Wiring into V3.21

- `SKILL.md`: insert "Phase -1/0: Idea Factory" before existing Phase 0; mark old Phase 2 (github-discovery) as subsumed when research-orchestrator ran.
- `references/phases.md`: add Idea Factory stage detail.
- `references/skills-matrix.md`: register 4 new sub-skills.
- `scripts/health_check.py` + `.claude/settings.json` Notification hook: deps/API/repo-activity scan → alerts/degradation.
- `assets/gep/genes.json`: add `ideaforge-outcome` evolution gene.

## Non-goals (this build)

- Not auto-deploying/billing with live keys (user runs one-command deploy with own creds).
- Not porting EPC-specific channels (知网/djyanbao/etc.) — irrelevant to software ideas.
