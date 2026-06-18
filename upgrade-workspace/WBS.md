# WBS — IdeaForge (V4.0) Build

Epic → Story → Task. Each Story is independently testable & committable.

## M1 — Intake + Research skeleton (2 channels)
- S1.1 idea-intake: `skills/idea-intake/SKILL.md` + `scripts/ambiguity_scorer.py` + tests
- S1.2 research-orchestrator: `skills/research-orchestrator/SKILL.md` + `scripts/orchestrator.py` (dispatch/normalize/persist)
- S1.3 channel framework: `scripts/channels/{base,github,sogou_wechat}.py` + tests (mocked)
- S1.4 dedup + checkpoint: `scripts/{deduper,checkpoint}.py` + tests

## M2 — Proposal engine + gate
- S2.1 maturity-index: `proposal-forge/scripts/maturity_index.py` + tests
- S2.2 tenx-delta-index: `proposal-forge/scripts/tenx_delta_index.py` + tests
- S2.3 proposal-forge SKILL.md + scorecard.py + templates (PROPOSAL.md, BUSINESS_MODEL.md, SCORECARD.json)
- S2.4 Approval Gate spec (interaction contract)

## M3 — Channel expansion + gap analysis
- S3.1 channels: reddit, hackernews, producthunt, appstore, googletrends, npm_pypi, competitor_site (+ tests)
- S3.2 gap_analyzer.py (coverage matrix → targeted re-research) + tests
- S3.3 quality_gate.py (摘要/字数/重复/可信度) + tests

## M4 — Pipeline integration
- S4.1 update main SKILL.md (Idea Factory phases, subsumed Phase 2 note)
- S4.2 update references/{phases,skills-matrix}.md + add references/ideaforge.md
- S4.3 handoff: proposal docs auto-populate VISION/REQUIREMENTS/ARCHITECTURE
- S4.4 end-to-end dry run on a sample idea (no external keys → degraded-mode test)

## M5 — Monetization scaffold
- S5.1 monetization-scaffold SKILL.md + templates (Dockerfile, docker-compose, stripe webhook, billing tiers, API gateway, deploy.md)
- S5.2 one-command deploy script (Vercel/Railway/Fly) with env templating

## M6 — Health + evolution
- S6.1 scripts/health_check.py (deps/API/repo-activity) + tests
- S6.2 wire into .claude/settings.json Notification hook (non-fatal warnings)
- S6.3 GEP: add ideaforge-outcome gene + capsule template; post-run feedback

## M7 — Acceptance
- S7.1 real idea → research → proposal → CC dev → deployable+billable scaffold
- S7.2 package_skill.py bump to V4.0; CHANGELOG; README update
- S7.3 sync to global install; smoke test

## Test strategy
- Each `.py` ships with unit tests (pytest) targeting ≥80% on scoring/normalization logic.
- Channels tested with HTTP mocks (no live keys in CI) + a manual live-smoke flag.
- SKILL.md validated by a structural linter (frontmatter present, <500 lines, links resolve).
