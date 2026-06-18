---
name: proposal-forge
description: IdeaForge Stage 3. Synthesize RESEARCH_DOCKET into a falsifiable "10× proposal" — maturity index, tenX delta index, blue/red-ocean judgment, data-driven pricing, 4-dim scorecard, and the Proposal Approval Gate. Use after research-orchestrator, before V3.21 Phase 0.
---

# proposal-forge — Ten× Proposal Generation + Approval Gate

**Stage 3 of the Idea Factory.** Converts harvested evidence into an investment-grade proposal and a yes/no/revise gate. This is where "十倍好" stops being a slogan.

## Pipeline

```
RESEARCH_DOCKET/**/_all.json  (repo signals, articles, ...)
   │
   ├─ maturity_index.score_landscape(repos)      → feasibility + landscape
   ├─ tenx_delta_index.score(claims)             → tenx + verdict + best_axis
   ├─ pricing.recommend(comp_prices, positioning)→ data-backed price
   │     positioning ← pricing.positioning_from_tenx(tenx_verdict, best_axis)
   │
   ▼
scorecard.compute(feasibility, user_value, monetization, tenx)
   │
   ├─ verdict == "proceed"  → render PROPOSAL.md + BUSINESS_MODEL.md + SCORECARD.json
   │                           → **PROPOSAL APPROVAL GATE** (human yes/no/revise)
   ├─ verdict == "revise"   → re-research weakest_dim (scorecard.weakest_dim)
   └─ verdict == "reject"   → back to idea-intake (idea is red-ocean / no value)
```

## How dimensions are derived (keep honest, no hallucination)

| Dimension | Source | Script |
|---|---|---|
| `feasibility` | median landscape maturity | `maturity_index.derive_feasibility` |
| `user_value` | pain-signal strength × frequency × WTP (from research digest + LLM judgment on articles) | LLM, cite ≥1 doc |
| `monetization` | pricing data-backed? compliance clear? billing UI defined? | `pricing` + checklist |
| `tenx` | max order-of-magnitude advantage | `tenx_delta_index.derive_tenx_score` |

**user_value** is the one dimension that needs LLM judgment (it reads pain articles). Require it to cite ≥1 harvested doc; if Sogou degraded and no pain evidence, cap user_value at 0.5 and flag it.

## The Ten× claims (the heart of it)

The user must articulate, for at least one axis, a concrete `{ours, baseline}` pair:
- e.g. `deploy_cost: {ours: 1, baseline: 16}` (we deploy for 1/16 the cost)
- The index computes `log10(16)=1.2` → ≥1.0 → **tenx-qualified**.
- No axis ≥10× → **incremental** → must find a new angle or the proposal doesn't proceed.

This is the falsifiable gate that kills incremental ideas before CC burns dev cycles.

## Approval Gate contract

When `verdict == "proceed"`, present `PROPOSAL.md` + `BUSINESS_MODEL.md` + `SCORECARD.json` to the user and ask **one** decision:
- **Approve** → auto-populate VISION/REQUIREMENTS/ARCHITECTURE, hand off to V3.21 Phase 5+
- **Revise** → user states what to change; weakest dim re-researched or claims adjusted
- **Reject** → loop to idea-intake

Never auto-proceed past this gate. This is interaction point #3 (idea → clarify → **proposal** → dev).

## Files

- [scripts/maturity_index.py](scripts/maturity_index.py) — 0–100 repo + landscape scoring
- [scripts/tenx_delta_index.py](scripts/tenx_delta_index.py) — order-of-magnitude delta
- [scripts/pricing.py](scripts/pricing.py) — data-backed price bands
- [scripts/scorecard.py](scripts/scorecard.py) — 4-dim weighted gate
- [scripts/test_scoring.py](scripts/test_scoring.py) — 15 tests, all green
- [templates/PROPOSAL.md](templates/PROPOSAL.md) · [BUSINESS_MODEL.md](templates/BUSINESS_MODEL.md) · [SCORECARD.json](templates/SCORECARD.json)

## Integration

- **Consumes**: [research-orchestrator](../research-orchestrator/SKILL.md) `RESEARCH_DOCKET/`
- **Feeds**: V3.21 Phase 0–4 docs (auto-populated), then Phase 5+ development
