# NOTICE — third-party provenance

Super-Skill is MIT-licensed (see [LICENSE](LICENSE)).

**V5.0.0 vendors no third-party source code.** Every V5 module was written for this repository.
The projects below shaped designs or algorithms (pattern-level reuse). Where a licence forbids
copying (GPL/AGPL/unlicensed/source-available) only the published idea was used, clean-room.
The full research dossier (204 repositories, verified with `gh api` on 2026-09-30) is in
[`upgrade-workspace/research/`](upgrade-workspace/research/).

| V5 component | Inspired by (licence) | What was borrowed |
|---|---|---|
| `phases.json` + `gate_check.py` + `state_machine.py` | github/spec-kit (MIT), gotalab/cc-sdd (MIT), GSD Core (MIT), LangGraph (MIT) | constitution/phase gates, `spec.json` approvals, resumable state pointer, checkpoints |
| `trace_matrix.py` (EARS + REQ IDs) | spec-kit `FR-###` coverage (MIT), cc-sdd EARS format (MIT), Kiro specs (pattern only, no licence) | stable requirement IDs, EARS lint, coverage matrix |
| `taskgraph.py` | steveyegge/beads (MIT), Task Master (Commons Clause — pattern only) | `ready` queue + atomic claim, complexity scoring/expansion |
| `loop_guard.py`, `ralph.py` | frankbria/ralph-claude-code (MIT), snarktank/ralph (MIT), OpenHands stuck detector (MIT), tanweai/pua (pattern only, no licence), karpathy/autoresearch (pattern only, no licence) | circuit breaker + dual-condition exit, prd/progress loop, stuck patterns, pressure ladder, keep/discard ledger |
| `hooks/*` | obra/superpowers (MIT), planning-with-files (MIT), parcadei/Continuous-Claude (MIT), GowayLee/cchooks (MIT), disler/claude-code-hooks-mastery & trailofbits/claude-code-config (pattern only, no licence) | valid hook layout, Stop-gate anti-loop rules, hand-off on compaction, guard deny baseline |
| `cost_meter.py` | ryoppippi/ccusage (MIT) | transcript parsing, (message.id, requestId) de-duplication |
| `playbook.py`, `memindex.py`, `skill_router.py` | ACE (Apache-2.0), ExpeL, getzep/graphiti (Apache-2.0), thedotmack/claude-mem, mem0 (Apache-2.0), MineDojo/Voyager (MIT) | delta-only playbook with helpful/harmful votes, invalidate-not-delete, 3-layer retrieval, skill library retrieval |
| `evolver/` | jennyzzt/dgm (Apache-2.0), gepa-ai/gepa (MIT), autogame-17/evolver (now GPL-3.0 — **clean-room, no code used**) | archive + parent selection, staged eval, reflective mutation, Pareto front, GEP strategy presets |
| `agents/ss-*.md` | obra/superpowers subagent-driven development (MIT), Claude Code subagent `isolation: worktree` (official) | Planner → Worker → Judge with isolated workers |
| `evals/` | Claude Code `claude plugin eval` (official), anthropics/skills skill-creator (Apache-2.0), Harbor/Terminal-Bench (Apache-2.0) | with/without-skill ablation, task + verifier format |
| `install.py` | davila7/claude-code-templates (MIT), vercel-labs/skills (MIT) | component installer shape |

Earlier versions: `skills/darwin-evolution/selector.js` / `signals.js` were adapted from
autogame-17/evolver while it was MIT-licensed (V3.8, 2026-03); OpenWolf (AGPL-3.0) and
mattpocock/skills (MIT) inspired V4 sub-skills at the pattern level. See `CHANGELOG.md`.
