---
name: research-orchestrator
description: IdeaForge Stage 2. Run pluggable multi-source research (GitHub, Sogou WeChat, +7 more) against an IDEA_SEED, with per-channel strategy, gap analysis, dedup, quality gate, and checkpoint resume. Ports the ResearchFactory-Eng orchestration architecture. Use after idea-intake, before proposal-forge.
---

# research-orchestrator — Multi-Source Research

**Stage 2 of the Idea Factory.** Harvests real-world evidence (user pain + existing solutions + maturity signals) so proposals are evidence-backed, not hallucinated.

## What it borrows from ResearchFactory-Eng

| ResearchFactory asset | IdeaForge reuse |
|---|---|
| `survey_runner` (channel dispatch) | `orchestrator.py` |
| per-channel GLM strategy matrix | per-channel `_keywords` + query builder |
| `gap_analyzer` (coverage matrix) | `gap_analyzer.py` (M3) |
| `deduper` (title + hash) | `deduper.py` |
| `quality_gate` | `quality_gate.py` (M3) |
| `checkpoint` (resume) | `checkpoint.py` |

**Not reused:** the 17 EPC-specific channels (知网/洞见研报/B站/专利/招投标) — irrelevant to software-product ideas. We use software channels instead.

## Channels (M1 = first 2; M3 adds 7)

| Channel | doc_type | Signal | Status |
|---|---|---|---|
| `github` | repo | stars/forks/issues/lang/license/topics/updated | ✅ M1 live |
| `sogou_wechat` | article | Chinese user pain (graceful degrade on anti-bot) | ✅ M1 |
| `reddit` `hackernews` `producthunt` `appstore` `googletrends` `npm_pypi` `competitor_site` | various | demand/competitor/pricing | M3 |

Uniform interface: `Channel.harvest(seed) -> list[Doc]`. 3-level fallback (primary → degraded → stub). **Never raises** — a blocked channel returns a `degraded` note and the run continues.

## How to run

```bash
# seed.json = the IDEA_SEED from idea-intake (or a minimal {summary, ...})
python scripts/orchestrator.py seed.json ./RESEARCH_DOCKET github,sogou_wechat
```

Outputs in `RESEARCH_DOCKET/`:
```
RESEARCH_DOCKET/
├── _checkpoint.json          # resume state
├── RESEARCH_DIGEST.md        # human/LLM-readable synthesis
├── github/{_all.md,_all.json}
└── sogou_wechat/{_all.md,_all.json}
```

## Graceful degradation contract

- Blocked channel → emits ONE `doc_type="degraded"` note (credibility 0.1) → the LLM substitutes domain knowledge or the user runs a manual fetcher.
- This is intentional: a blocked Sogou must **not** silently fake data. Honesty > coverage.

## Files

- [scripts/orchestrator.py](scripts/orchestrator.py) — dispatcher + digest writer
- [scripts/channels/base.py](scripts/channels/base.py) — `Channel` ABC, `Doc`, `real_http`, dedup-key
- [scripts/channels/github.py](scripts/channels/github.py) / [sogou_wechat.py](scripts/channels/sogou_wechat.py)
- [scripts/deduper.py](scripts/deduper.py) — title + content-hash dedup
- [scripts/checkpoint.py](scripts/checkpoint.py) — stage resume
- [scripts/test_orchestrator.py](scripts/test_orchestrator.py) — 9 tests, all green

## Integration

- **Consumes**: [idea-intake](../idea-intake/SKILL.md) `IDEA_SEED.md`
- **Feeds**: [proposal-forge](../proposal-forge/SKILL.md) reads `RESEARCH_DOCKET/**/_all.json` + `RESEARCH_DIGEST.md`
