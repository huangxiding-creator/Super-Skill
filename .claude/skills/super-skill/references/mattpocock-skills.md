# mattpocock/skills → Super-Skill Integration Map

**Source**: [mattpocock/skills](https://github.com/mattpocock/skills) — "Skills For Real Engineers" by Matt Pocock (MIT, © 2026). Integrated in Super-Skill V4.1.4 as the [`real-engineering`](../skills/real-engineering/SKILL.md) sub-skill.

**Philosophy**: small, composable, adaptable skills that work with any model — explicitly *not* another process-owning framework ("Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control"). Super-Skill keeps its 14-phase autonomous spine; this source contributes the disciplines that live at the **interaction points** — alignment, language, and human-only steps — where control matters most.

## Status legend

- **absorbed** — mechanism adopted as a named, runnable part of Super-Skill
- **strengthened** — existing Super-Skill mechanism upgraded with the source's sharper version
- **covered** — Super-Skill already had an equivalent; binding documented, no change

## Full mapping (25 stable skills)

### Engineering (18)

| Source skill | What it does | Super-Skill binding | Status |
|---|---|---|---|
| `grilling` | Relentless interview over a design tree (rounds + frontier; facts are the agent's job, decisions the user's) | `real-engineering` Mechanism 1; deep path at Phase 4 alongside the Hybrid Clarification Gate | **absorbed** |
| `grill-with-docs` | Grilling that also builds CONTEXT.md + ADRs inline (the stateful variant for working directories) | `real-engineering` Mechanisms 1+2 combined; Phase 3/4 wiring | **absorbed** |
| `domain-modeling` | Active discipline: challenge terms, sharpen fuzzy language, stress-test scenarios, cross-reference code, update glossary inline | `real-engineering` Mechanism 2; `context_lint.py` verifies the artifacts | **absorbed** |
| `codebase-design` | Deep-module vocabulary: module/interface/depth/seam/adapter/leverage/locality — "a lot of behaviour behind a small interface at a clean seam" | Phase 5b design guidance; vocabulary layer under Phase 6 ticket seams | covered |
| `to-spec` | Turn the conversation into a spec, published to the tracker | Phase 4 `REQUIREMENTS.md` | covered |
| `to-tickets` | Break a plan into tracer-bullet vertical slices, each declaring blocking edges; wide refactors sequence expand–contract | `real-engineering` Mechanism 3; Phase 6 WBS upgrade | **absorbed** |
| `implement` | Build ticketed work: `/tdd` at pre-agreed seams, regular typecheck + single test files, full suite once at the end, `/code-review` before commit | Phase 8 Autonomous Loop (same loop discipline) | covered |
| `tdd` | Red-green-refactor, one vertical slice at a time | `testing-automation` (Phase 8/9) | covered |
| `code-review` | Two-axis review of the diff since a fixed point — **Standards** (repo conventions + Fowler smell baseline) and **Spec** (faithful to the originating issue) — as parallel sub-agents | `real-engineering` Strengthened; Phase 9 `verification-gate` upgrade | **strengthened** |
| `diagnosing-bugs` | Red-first diagnosis: build one command that already goes red on *this* bug (10-rung ladder), tighten it, raise repro rate for flakes, never hypothesise without it | `real-engineering` Mechanism 5; Phase 8/9 `systematic-debugging` upgrade | **absorbed** |
| `prototype` | Throwaway program answering one design question (single shareable HTML); kept on a `prototype/<name>` branch as a primary source | Phase 5 design option; snippet rule in Mechanism 3 | covered |
| `research` | Background agent investigates against primary sources, leaves a cited Markdown file | `research-orchestrator` (Idea Factory; product-flavoured) + Phase 3 | covered |
| `triage` | Move incoming (not self-created) issues through a triage-role state machine → agent-ready issues | Phase 6 backlog grooming; feeds Phase 8 | covered |
| `wayfinder` | For efforts too big for one session: chart a shared map of **decision tickets** on the tracker — decisions, not deliverables — until the fog clears, then hand off to `/to-spec` | `real-engineering` Phase Wiring row (foggy big efforts); complements Phase 0–6 for greenfield giants | **absorbed** |
| `resolving-merge-conflicts` | Resolve conflicts hunk by hunk by intent traced to each side's primary source; never `--abort` | Cross-repo maintenance practice (used for the V4.0 OpenWolf merge) | covered |
| `improve-codebase-architecture` | Scan for deepening opportunities, present as HTML report, grill through the chosen one | Phase 10 Ralph Loop (Analyze step) | covered |
| `wizard` | Generate an interactive bash wizard for steps only a human can perform (provisioning, credentials, CI secrets, dashboards, cutover) | `real-engineering` Mechanism 4 + `scripts/wizard_template.sh`; Phase 7/11 human-only steps | **absorbed** |
| `ask-matt` | Router over the skill set: main flow, on-ramps, standalone skills, phase boundaries | `real-engineering` SKILL.md flow map; this document | **absorbed** |

### Productivity (7)

| Source skill | What it does | Super-Skill binding | Status |
|---|---|---|---|
| `grill-me` | Stateless grilling (no repo) | `real-engineering` Mechanism 1 (same primitive) | **absorbed** |
| `handoff` | Compact the conversation into a portable handoff doc (new harness / new directory / colleague / mid-phase side-task); reference artifacts by path, redact secrets | `context-compressor` (9-part handoff) — strengthen with "reference, don't duplicate" + redaction rules | **strengthened** |
| `teach` | Multi-session teaching workspace (mission, glossary, learning record, resources) | D7 long-term memory in `ai-mastery-7`; pairs with `weekly_retrospective.py` | covered |
| `to-questionnaire` | Interview the user about the *send* — write a questionnaire for the one person who can answer | Idea Factory clarification for externally-blocked decisions | covered |
| `wait-what` | The moment a message doesn't land: re-pitch with missing context, plain technical English, CONTEXT.md vocabulary | `real-engineering` Strengthened (cross-cutting habit) | **strengthened** |
| `writing-for-agents` | Reference for documents agents consume by pointer: skills, AGENTS.md/CLAUDE.md | Token Budget Discipline + memory rules already encode this | covered |
| `grilling` (primitive) | The interview primitive `/triage`, `/wayfinder`, `/improve-codebase-architecture` run internally | `real-engineering` Mechanism 1 | **absorbed** |

## Key mechanisms in depth

### Grilling — rounds and the frontier

Map the discussion as a **design tree**. The **frontier** is every decision whose prerequisites are settled — the questions askable *now* without guessing at unheard answers. Ask the whole frontier in one round (numbered, each with a recommended answer), wait, recompute. A question depending on another question still open belongs to a *later* round. Facts come from sub-agents, never the user. Done when the frontier is empty; act only after the user confirms shared understanding.

### Tracer-bullet tickets — vertical slices + expand–contract

Each ticket: a narrow but COMPLETE path through every layer, demoable alone, sized to one fresh context window, declaring its **blocking edges**. Exception — **wide refactors** (one mechanical change, blast radius across the codebase): **expand** (new form beside old, nothing breaks) → **migrate** call sites in blast-radius-sized batches, each green → **contract** (delete the old form once no caller remains). When batches can't stay green alone, share an integration branch blocking a final integrate-and-verify ticket.

### ADR — the 3-part test

Record an ADR (`docs/adr/NNNN-slug.md`; scan for the highest number and increment; 1–3 sentences suffice) only when ALL of: **hard to reverse** · **surprising without context** · **the result of a real trade-off**. Qualifiers: architectural shape, cross-context integration patterns, lock-in-carrying tech choices, boundary/scope decisions (the no-s especially), deliberate deviations from the obvious path, invisible constraints, non-obvious rejections.

### CONTEXT.md — glossary and nothing else

`**Term**: definition (what it IS, 1–2 sentences)` + `_Avoid_: banned synonyms`. Be opinionated; keep definitions tight; include only project-specific concepts (general programming concepts never belong); subheadings when natural clusters emerge. Single `CONTEXT.md` at root, or `CONTEXT-MAP.md` pointing at per-context glossaries. Devoid of implementation detail — not a spec, not a scratch pad. Verified by `context_lint.py`.

### Phase boundaries — the five options

At each phase boundary: **Continue** (rule out first — primary-source cost) · `/clear` · **handoff file** (only for a new harness, new directory, colleague, or mid-phase fork) · **subagent** (tightly scoped, report back) · `/compact` (the default at the bottom of the tree). The binding constraint is the **smart zone** — the window (~150k tokens) within which the model still reasons sharply; don't push on degraded. Full decision tree: source `skills/engineering/ask-matt/PHASE-BOUNDARIES.md`.

### Red-first diagnosis — the 10-rung ladder

Failing test → curl/HTTP script → CLI + snapshot diff → headless browser → replay a captured trace → throwaway harness → property/fuzz loop → `git bisect run` harness → differential old-vs-new → HITL bash script. Then **tighten** (faster / sharper signal / more deterministic) and, for flakes, **raise the reproduction rate** until debuggable. Redact every secret in anything shown. Lock the fix with a regression test.

## What Super-Skill deliberately did NOT absorb

- **`setup-matt-pocock-skills`** (tracker/labels/doc-layout config) — Super-Skill's Phase 7 initialization and repo conventions already fix these choices.
- **The plugin/Codex packaging** — Super-Skill is itself the distribution unit.
- **In-progress / misc / deprecated skills** (claude-handoff, loop-me, writing-*, setup-ts-deep-modules, git-guardrails, migrate-to-shoehorn, scaffold-exercises, setup-pre-commit) — unstable or too niche for the core skill.

## Verification

- `skills/real-engineering/scripts/test_context_lint.py` — 14/14 tests (glossary parsing, ADR numbering, lazy-creation semantics, CLI exit codes + JSON, wizard template syntax probe).
- Auto-discovered by `scripts/health_check.py` (7th test suite).
