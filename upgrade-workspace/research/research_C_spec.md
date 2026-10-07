# Research C: Spec-Driven Development, Planning and Task-Graph Frameworks for Super-Skill

Date: 2026-09-30. Stars, license and last push were checked with `gh api repos/OWNER/REPO` on this date. Mechanisms were taken from the actual README, template or command files fetched from each repo (file paths are cited). Any item I could not check is marked **UNVERIFIED**.

Super-Skill gaps this research targets:
- **G1**: phases are prose, with no machine-readable phase state
- **G2**: no artifact contracts between phases
- **G3**: no task graph tool
- **G4**: no resume from an arbitrary phase
- **G5**: no traceability from requirement to task to test

Phase shorthand used below: P1 vision, P2 feasibility, P3 GitHub discovery, P4 KB, P5 requirements, P6 architecture, P7 WBS, P8 init, P9 autonomous experiment loop, P10 QA, P11 Ralph optimization, P12 deploy, P13 self-evolution, plus the front end (ambiguity scoring and 10x proposal with approval gate).

---

## 1. Project table (35 verified projects plus 1 closed-source note)

| # | Project | Stars | License | What it is | Mechanism worth borrowing (specific file or command) | Where it goes in Super-Skill | How to adopt |
|---|---|---|---|---|---|---|---|
| 1 | [github/spec-kit](https://github.com/github/spec-kit) | 139,455 | MIT | GitHub's SDD toolkit | `templates/spec-template.md`: prioritized user stories (P1/P2/P3), each with an **Independent Test** and Given/When/Then; `FR-###` / `SC-###` IDs; `[NEEDS CLARIFICATION: …]` markers. `commands/clarify.md`: scans a Clear/Partial/Missing taxonomy, asks **at most 5** questions ranked by Impact×Uncertainty, with a recommended option, and writes answers back into the spec. `plan-template.md`: **Constitution Check GATE** ("must pass before Phase 0 research, re-check after Phase 1 design") plus a Complexity Tracking table for justified violations. `tasks-template.md`: `[T###] [P] [US#] description + exact file path`, phased as Setup → Foundational (blocking) → one phase per story with checkpoints. `commands/analyze.md`: cross-artifact consistency and **coverage** report (every FR/SC has ≥1 task, lists unmapped tasks, constitution conflicts are automatically CRITICAL). | Ambiguity scoring (clarify taxonomy), P5 requirements, P6 (constitution gate), P7 WBS, P10 (analyze as pre-implement gate) | **Direct reuse** (MIT): copy spec, plan and tasks templates plus the analyze and clarify prompts with attribution |
| 2 | [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53,647 | MIT (GitHub reports NOASSERTION; the LICENSE file is MIT, and the BMad name/brand is theirs) | Agile AI-driven development: persona agents plus workflow skills | Persona skills: `bmad-agent-analyst/pm/architect/ux-designer/dev`, plus `bmad-party-mode` (multi-persona discussion). `bmad-ticket`: a `tickets.toml` breakdown beside each epic, with entries carrying a stable `id`, `covers` (CAP-N requirement ids), `after` (prerequisites), a `Verify:` line and uncertainty; the board has states planned/backlog/in-progress/review/done/dropped, and `tickets.py` answers "what's ready". `bmad-architecture`: an "architecture spine" of `AD-n` decisions, each with `Binds/Prevents/Rule`; an append-only `.memlog.md` written via `memlog.py append --type decision|constraint|assumption|question|event`, which supports resume from the memlog; a `lint_spine.py` deterministic gate plus parallel reviewer lenses. Also `bmad-correct-course` (change management) and `bmad-retrospective` (with `git_evidence.py`). | 10x proposal (party-mode personas), P5/P6/P7, P13 (retrospective) | **Direct reuse** (MIT) of the ticket.toml schema idea and memlog; **borrow pattern** for personas |
| 3 | [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master) | 28,113 | MIT **+ Commons Clause** (no selling or hosting for a fee) | AI task manager, CLI plus MCP | `.taskmaster/tasks/tasks.json`: tagged task lists (`master`, feature tags), each task `{id,title,description,status,dependencies[],priority,details,testStrategy,subtasks[]}`. Commands: `parse-prd`, `analyze-complexity` → `task-complexity-report.json` (`complexityScore` 1-10, `recommendedSubtasks`, `expansionPrompt`, `reasoning`, `thresholdScore`), `expand --id`, `next` (the highest-priority task whose deps are done), `move --with-dependencies`, `research`. MCP tool tiers: core (7), standard (15), all (36). | P7 WBS (task graph), P9 (next-task selector) | **Borrow pattern** only. Reimplement the schema in Super-Skill's Python; do not vendor the code (Commons Clause) |
| 4 | [gotalab/cc-sdd](https://github.com/gotalab/cc-sdd) | 3,691 | MIT | Kiro-style SDD as 17 Agent Skills | `.kiro/specs/<feature>/spec.json`: `{phase:"tasks-generated", approvals:{requirements:{generated,approved}, design:{…}, tasks:{…}}, ready_for_implementation}`, a **machine-readable approval gate**. `settings/rules/ears-format.md`: EARS patterns (When/While/If/Where/Ubiquitous). `rules/tasks-generation.md`: `_Requirements: 1.2_` and `_Depends: 1.2, 2.3_` annotations, `(P)` parallel marker, component **Boundary** per task. `/kiro-discovery` routes to extend spec / no spec / new spec / multi-spec and writes `brief.md` + `roadmap.md`. `/kiro-impl`: a fresh implementer per task running TDD RED→GREEN, an independent reviewer, auto-debug after repeated rejection, learnings in `## Implementation Notes` in tasks.md, resumable from recorded task state. `/kiro-spec-batch`: specs by dependency wave with cross-spec contradiction review. `kiro-validate-gap` for brownfield. | Approval gate (spec.json), P5 (EARS), P7, P9 | **Direct reuse** (MIT): copy `ears-format.md`, `tasks-generation.md` and the `spec.json` schema |
| 5 | [buildermethods/agent-os](https://github.com/buildermethods/agent-os) | 5,457 | MIT | Standards injection plus spec shaping | Discover Standards (extract conventions from the codebase), Index Standards, Deploy Standards (inject only the standards relevant to the current task), Shape Spec | P4 KB (standards index), P8 init | Borrow pattern |
| 6 | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) (formerly glittercowboy) | 64,435 | MIT | GSD v1 meta-prompting SDD (archived; points to GSD Core) | See GSD Core | n/a | n/a |
| 7 | [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) | 10,016 | MIT | Current GSD home | **`.planning/STATE.md` with YAML frontmatter** (`docs/reference/state-md.md`): `gsd_state_version, milestone, status, active_phase, next_action (discuss/plan/execute/verify-phase), next_phases[], progress{total_phases,completed_phases,total_plans,completed_plans,percent}, current_plan, last_updated, state_head (git sha), stopped_at, paused_at`, kept under 100 lines and read first by every workflow. Phase loop: Discuss → `CONTEXT.md` (decisions), Plan → `RESEARCH.md` + `PLAN.md` files in **dependency waves**, with a plan-checker, Execute (fresh 200k-context executor per plan, atomic commits, one `SUMMARY.md` per plan), Verify → `VERIFICATION.md` checking REQ-ID coverage and decision coverage and generating fix plans, Ship. `ROADMAP.md` + milestones. `/gsd-quick` for small work. | **G1/G4 core**: Super-Skill `state` file; P9 execution waves; P10 verify | **Direct reuse** (MIT) of the STATE.md schema concept; borrow the loop |
| 8 | [gsd-build/gsd-2](https://github.com/gsd-build/gsd-2) | 7,782 | MIT | GSD v2 long-running autonomy variant | Same `.planning/` artifacts aimed at long unattended runs | P9 | Borrow pattern |
| 9 | [Pimzino/claude-code-spec-workflow](https://github.com/Pimzino/claude-code-spec-workflow) | 3,860 | MIT | Requirements → Design → Tasks → Implement slash commands, plus a bug workflow | Separate **bug path**: Report → Analyze → Fix → Verify; per-task command generation | P10 QA (bugfix sub-workflow) | Borrow pattern |
| 10 | [Pimzino/spec-workflow-mcp](https://github.com/Pimzino/spec-workflow-mcp) | 4,297 | **GPL-3.0** | MCP server for SDD with a dashboard | Approval requests via dashboard (approve / request changes / revisions), steering docs, implementation logs | Approval gate UI | **Borrow pattern only** (GPL is incompatible with vendoring) |
| 11 | [automazeio/ccpm](https://github.com/automazeio/ccpm) | 8,393 | MIT | PM skill using GitHub Issues plus worktrees | PRD → Epic → Task files in `.claude/epics/<name>/` with frontmatter (`depends_on`, `parallel: true`, `conflicts_with`); `epic-sync` creates an epic issue plus sub-issues; an **issue analysis splits one issue into parallel work streams**; one worktree per epic; scripts `epic-status.sh`, `epic-show.sh`; "PRD → Epic → Task → Issue → Code → Commit" traceability | P7, P9 parallel, G5 | **Direct reuse** (MIT) of the epic/task frontmatter and scripts |
| 12 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 70,695 | MIT | Brownfield-first SDD with change proposals | `openspec/specs/` (source of truth) vs `openspec/changes/<id>/{proposal.md, specs/ (deltas), design.md, tasks.md}`. **Delta headers** `## ADDED / MODIFIED / REMOVED Requirements`, each `### Requirement:` using SHALL with `#### Scenario:` WHEN/THEN. `/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive` (merges deltas into specs and moves to `changes/archive/YYYY-MM-DD-<id>/`). "Stores" for cross-repo specs. | P11 Ralph optimization and P13 self-evolution (changes as deltas); the 10x proposal format | **Direct reuse** (MIT) of the delta format; borrow the archive flow |
| 13 | [steveyegge/beads](https://github.com/gastownhall/beads) (now gastownhall/beads) | 27,518 | MIT | Dependency-aware issue graph and memory for agents (`bd`) | `bd ready --json` lists work with no open blockers; `bd update <id> --claim` claims atomically; `bd dep add <child> <parent>` (blocks / related / parent-child / discovered-from); hash IDs `bd-a1b2` avoid merge collisions; `bd prime` injects workflow context and memories; `bd remember`; **compaction** summarizes old closed issues; storage is Dolt (versioned SQL) with push/pull. | **G3 task-graph engine**, P9 loop picker | **Direct reuse** (MIT): either call `bd` as an optional backend or replicate the `ready` semantics |
| 14 | [snarktank/ai-dev-tasks](https://github.com/snarktank/ai-dev-tasks) | 7,788 | Apache-2.0 | Three markdown prompts | `create-prd.md` (clarifying questions, then PRD) → `generate-tasks.md` (parent tasks, then "Go" confirmation, then sub-tasks plus relevant files) → one sub-task at a time with a human check | P5→P7 lightweight path | Direct reuse (Apache-2.0) |
| 15 | [snarktank/ralph](https://github.com/snarktank/ralph) | 21,885 | MIT | Ralph loop driven by prd.json | `prd.json`: `{project, branchName, userStories:[{id:"US-001", title, description, acceptanceCriteria[] (each verifiable, e.g. "Typecheck passes"), priority, passes:false, notes}]}`. `ralph.sh` starts a **fresh instance per iteration**, picks the highest-priority story with `passes:false`, implements it, runs checks, commits, sets `passes:true`, and appends learnings to `progress.txt`. Skills `/prd` and `/ralph` (converts PRD to prd.json). | P9 and P11 (the Ralph loop) | **Direct reuse** (MIT) of the prd.json schema and loop |
| 16 | [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) | 9,640 | MIT | Hardened Ralph for Claude Code (784 tests) | **Dual-condition exit gate**: completion indicators AND an explicit `EXIT_SIGNAL: true`. Circuit breaker (stuck-loop and multi-line error detection, force exit after 5 consecutive completion indicators, thresholds set via env). Rate limit of 100 calls/hour. Three-layer API-limit detection. `--resume <session_id>` (not `--continue`). Session expiry after 24h. | P11 loop safety, P9 | Direct reuse (MIT) |
| 17 | [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 11,627 | Apache-2.0 | Research → Plan → Implement command set | `.claude/commands/`: `research_codebase`, `create_plan`, `iterate_plan`, `validate_plan`, `implement_plan`, `create_handoff`/`resume_handoff`, `ralph_research/plan/impl`, `oneshot_plan`. Plans live in `thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-*.md`, with each phase's **Success Criteria split into Automated Verification (exact commands) and Manual Verification**. Handoffs are written to `thoughts/shared/handoffs/<ticket>/<timestamp>_*.md`, then `/resume_handoff <path>`. | G4 (handoff/resume), P6/P7 plan format, P10 | Direct reuse (Apache-2.0) |
| 18 | [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | 26,467 | Apache-2.0 (code) / CC BY-SA content (**UNVERIFIED split**) | Principles for production agents | Factor 5 "Unify execution state and business state", 6 "Launch/Pause/Resume", 8 "Own your control flow", 9 "Compact errors into context", 12 "Stateless reducer" | Design principles for the phase-runner script | Borrow pattern |
| 19 | [coleam00/context-engineering-intro](https://github.com/coleam00/context-engineering-intro) | 13,891 | MIT | PRP (Product Requirement Prompt) origin | `PRPs/templates/prp_base.md`: Goal/Why/What/Success Criteria; an **All Needed Context** YAML (`url/file/doc/docfile` + `why` + `critical`); current vs desired tree; Known Gotchas; Implementation Blueprint (a task list using `MODIFY/CREATE/MIRROR pattern from`); Integration Points; **Validation Loop Level 1 syntax/style → Level 2 unit tests → Level 3 integration**; final checklist. `INITIAL.md` → `/generate-prp` → `/execute-prp`. | P4 KB → P7 per-task context packs; P10 validation levels | Direct reuse (MIT) |
| 20 | [Wirasm/PRPs-agentic-eng](https://github.com/Wirasm/prp) (now Wirasm/prp) | 2,254 | MIT | PRP skills plugin (`prp-core`) | Skills: `prp-prd` (PRD with implementation phases), `prp-plan`, `prp-implement`, `prp-loop`, `prp-issue-contract`, `prp-research-team`, `prp-review`, `prp-spike`, `prp-orchestrate`, `prp-deliver` | Candidate sub-skills for P5-P10 | Direct reuse (MIT) |
| 21 | [MrLesk/Backlog.md](https://github.com/MrLesk/Backlog.md) | 6,897 | MIT | Git-native markdown task board plus CLI/MCP | One markdown file per task under `backlog/`, with acceptance criteria, a **reusable Definition-of-Done checklist**, milestones, dependencies (shows "waits on" and "blocks"), `--plain` agent-friendly output, `backlog board` (terminal kanban), `backlog browser` (web UI), `board export` (markdown report) | P7/P9 human-visible board | Borrow pattern, or use the tool directly |
| 22 | [BloopAI/vibe-kanban](https://github.com/BloopAI/vibe-kanban) | 28,223 | Apache-2.0 | Kanban orchestrator for parallel coding agents | One git worktree per task attempt, agent runs from the board, diff review before merge | P9 parallel execution UI | Borrow pattern |
| 23 | [shotgun-sh/shotgun](https://github.com/shotgun-sh/shotgun) | 687 | MIT | Codebase-aware spec writer | Codebase graph index → research → spec → **staged PRs with file-by-file instructions**; Planning mode (checkpoint per step, cascaded doc updates when one change affects others) vs Drafting mode (end to end) | P3/P4 → P7 | Borrow pattern |
| 24 | [gemini-cli-extensions/conductor](https://github.com/gemini-cli-extensions/conductor) | 3,750 | Apache-2.0 | Google's SDD plugin (Gemini CLI, Antigravity, Claude Code) | `/conductor:conductor-setup` writes project context (product, product guidelines, tech stack, workflow such as TDD and commit strategy). Work unit is a **track** with spec.md + plan.md (phases → tasks). **Smart revert**: git-aware revert by logical unit (track/phase/task) rather than commit hash. | G4 rollback to a phase; P8 init | Borrow pattern (Apache-2.0 permits reuse) |
| 25 | [spec-kitty/spec-kitty](https://github.com/spec-kitty/spec-kitty) | 1,652 | MIT | Spec-kit fork aimed at a governed "software factory" | Pipeline `spec → plan → tasks → next → review → accept → merge`; artifacts in `kitty-specs/`; **work packages with lanes** planned/in_progress/for_review/approved/done; `.worktrees/` isolation; `spec-kitty next --agent claude --mission <slug>` (the runtime picks the next action); `spec-kitty dashboard`; automatic retrospective per mission (`.kittify/config.yaml#retrospective`) | Closest analogue to the whole Super-Skill; P9, P13 | Direct reuse (MIT) |
| 26 | [coleam00/Archon](https://github.com/coleam00/Archon) | 23,583 | MIT | YAML workflow engine for AI coding ("GitHub Actions for agents") | `.archon/workflows/*.yaml` define phases, **validation gates** and artifacts; deterministic nodes (bash, tests, git) mixed with AI nodes; one worktree per run | **G1: encode the 14 phases as a YAML workflow** | Borrow pattern, or run it as the engine |
| 27 | [parcadei/Continuous-Claude-v3](https://github.com/parcadei/Continuous-Claude-v3) | 3,944 | MIT | Continuity via hooks, ledgers and handoffs | YAML handoffs (token-efficient), continuity ledger, hooks that force `create_handoff` before a session ends | G4 | Borrow pattern |
| 28 | [gastownhall/gastown](https://github.com/gastownhall/gastown) | 18,212 | MIT | Multi-agent workspace manager built on Beads | "Mayor" coordinator agent; work state in a Beads ledger; git-backed hooks so work survives agent restarts | P9 multi-agent | Borrow pattern |
| 29 | [tesslio/spec-driven-development-tile](https://github.com/tesslio/spec-driven-development-tile) | 55 | MIT | Tessl's SDD "tile" (tessl CLI itself: tesslio/cli, 70 stars, license NOASSERTION) | Spec-as-source, with specs linked to tests; package registry of "tiles" (usage specs for libraries) | P4 KB (library usage specs) | Borrow pattern; details of tessl internals **partly UNVERIFIED** |
| 30 | [vanzan01/cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank) | 3,059 | none listed | Mode-based workflow (VAN/PLAN/CREATIVE/IMPLEMENT) | `/van` detects **complexity level 1-4**, and the level decides how much planning runs; memory files `tasks.md`, `activeContext.md`, `progress.md` | Right-sizing the 14 phases | Borrow pattern (no license, so no copying) |
| 31 | [Helmi/claude-simone](https://github.com/Helmi/claude-simone) | 558 | MIT | Directory-based PM for Claude Code | Milestones → sprints → task files with a project manifest | P7 | Borrow pattern |
| 32 | [Gentleman-Programming/agent-teams-lite](https://github.com/Gentleman-Programming/agent-teams-lite) | 1,244 | MIT (archived) | Orchestrator plus 9 SDD sub-agents | Orchestrator delegates sdd-explore/propose/spec/design/tasks/apply/verify/archive to sub-agents; Engram persistent memory | Sub-agent-per-phase pattern | Borrow pattern |
| 33 | [liatrio-labs/spec-driven-workflow](https://github.com/liatrio-labs/spec-driven-workflow) | 95 | Apache-2.0 | Lightweight markdown SDD prompts | Spec → task list → proof artifacts (evidence per task) | G5 evidence | Borrow pattern |
| 34 | [obra/superpowers](https://github.com/obra/superpowers) | 292,988 | MIT | Skills methodology | Skills `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `dispatching-parallel-agents`, `verification-before-completion`, `using-git-worktrees`, `finishing-a-development-branch` | P9/P10 execution discipline | Direct reuse (MIT) |
| 35 | [kirodotdev/Kiro](https://github.com/kirodotdev/Kiro) | 4,341 | no license (issue tracker; the IDE is proprietary AWS) | Kiro IDE specs | `requirements.md` (or `bugfix.md`) + `design.md` + `tasks.md`; EARS acceptance criteria; task **waves** from dependency analysis run concurrently; Requirements-First vs Design-First; Quick Spec with no approval gates (per kiro.dev/docs/specs) | P5-P7 format standard | Borrow pattern (use cc-sdd's MIT EARS rules) |
| n | Traycer (traycer.ai) | n/a | closed source | Planning layer for coding agents (phases, plan, verify) | Repo `traycerai/traycer-vscode` returned 404; **UNVERIFIED, not counted** | n/a | n/a |

Also seen and verified but not examined in depth: `JuliusBrussee/cavekit` (1,150, MIT, frozen), `maxritter/pilot-shell` (2,080, NOASSERTION), `ruvnet/ruflo`, formerly claude-flow (73,522, MIT), `SuperClaude-Org/SuperClaude_Framework` (23,914, MIT), `wshobson/agents` (40,095, MIT), `smtg-ai/claude-squad` (8,551, **AGPL-3.0**), `stravu/crystal` (3,122, MIT).

---

## 2. Top 8 mechanisms to adopt (with concrete specs for Super-Skill)

### M1. Machine-readable project state plus a resume pointer (fixes G1 and G4)
**Sources:** GSD Core `STATE.md` frontmatter, cc-sdd `spec.json`, 12-factor Factors 5, 6 and 12.

Add `.super-skill/state.json`, or a `STATE.md` with YAML frontmatter, that is rewritten after every phase transition by a new `scripts/phase_state.py`:

```yaml
schema_version: "1.0"
project: <slug>
status: executing            # idea|researching|proposed|approved|executing|paused|done|failed
active_phase: "P9"
next_action: "run P9 iteration"   # the exact sub-skill or command to run next
phases:
  P5_requirements: {status: done, artifacts: [specs/requirements.md], approved: true, approved_at: ...}
  P6_architecture: {status: done, artifacts: [specs/design.md, specs/adr/]}
  P9_experiment_loop: {status: in_progress, iteration: 7, last_commit: <sha>}
approvals: {proposal_10x: {generated: true, approved: true}}
progress: {total_tasks: 42, done: 19, percent: 45}
state_head: <git sha>        # resume validity check
stopped_at: "T-019 green, reviewer pending"
last_updated: <iso>
```

Every phase sub-skill starts with "read state; refuse to run if prerequisite phases are not `done` or `approved`". `super-skill resume` reads `next_action`. `super-skill goto P7` resets downstream phases to `stale`.

### M2. Phase artifact contracts plus a gate linter (fixes G2)
**Sources:** spec-kit Constitution Check GATE and `/analyze`, BMAD `lint_spine.py` plus reviewer lenses, Archon YAML gates.

Add `phases.yaml` that declares for each phase: `inputs` (required artifact paths and states), `outputs` (paths plus required sections or IDs), `gate` (deterministic checks plus an optional reviewer rubric), and `approval: human|auto`. Then add `scripts/gate_check.py P6` that runs the checks: files exist, required headings exist, no `[NEEDS CLARIFICATION]` is left, every FR has an owner, and constitution MUSTs are met. Keep a `constitution.md` (spec-kit `memory/constitution.md`) as the non-negotiable principles, where any violation is automatically CRITICAL.

### M3. Stable-ID requirements in EARS form with a coverage matrix (fixes G5)
**Sources:** spec-kit `FR-###`/`SC-###` and `analyze.md` coverage table, cc-sdd `ears-format.md` plus `_Requirements:` annotations, GSD verifier REQ-ID coverage, ccpm traceability chain.

- P5 writes `REQ-001 … REQ-n`, each as EARS: *When [event], the [system] shall [response]* / *While* / *If* / *Where* / ubiquitous. Each has ≥1 acceptance scenario with an ID (`REQ-003.AC2`).
- P7 tasks must carry `covers: [REQ-003.AC2]`.
- Tests carry the ID in their name or docstring.
- `scripts/trace_matrix.py` builds `trace.json` and `trace.md` (REQ → tasks → tests → status). It fails the P10 gate if coverage is below 100% of must-have REQs, or if orphan tasks exist.

### M4. Task graph with a `ready` queue and atomic claim (fixes G3)
**Sources:** beads (`bd ready`, `--claim`, `dep add`, hash IDs, compaction), Task Master `tasks.json` plus `next`, BMAD `tickets.toml` (`after`, `covers`, `Verify:`), ccpm `parallel` / `conflicts_with`.

Proposed `tasks.json` item:

```json
{"id":"T-a1b2","title":"...","covers":["REQ-003.AC2"],"after":["T-9f3c"],
 "parallel":true,"boundary":"auth-service","files":["src/auth/*.py"],
 "status":"pending|ready|in_progress|review|done|blocked|dropped",
 "complexity":6,"verify":"pytest tests/test_auth.py::test_ac2",
 "testStrategy":"...","notes":"","claimed_by":null}
```

Add `scripts/taskgraph.py` with `ready`, `next`, `claim`, `done`, `waves` (a topological sort into parallel waves, as in Kiro and GSD), `validate` (cycle detection plus missing covers), and `compact`. Optionally delegate to `bd` when it is installed.

### M5. Complexity analysis and recursive expansion in the WBS phase
**Source:** Task Master `analyze-complexity` → `task-complexity-report.json`.

P7 scores each task 1-10 and records `recommendedSubtasks`, `expansionPrompt` and `reasoning`, with `thresholdScore: 5`. Tasks above the threshold are expanded until every leaf fits one fresh-context iteration. This is the same "small tasks" rule Ralph and GSD depend on. Reimplement it; do not copy the code (Commons Clause).

### M6. Ralph loop contract: prd.json, progress.txt, dual exit gate and circuit breaker
**Sources:** snarktank/ralph and frankbria/ralph-claude-code.

For P9 and P11:
- Each iteration runs in a fresh context and picks `next` (M4).
- It implements exactly one task, runs that task's `verify` command, commits, flips the status, and appends learnings to `progress.txt` (or cc-sdd's `## Implementation Notes`).
- Exit requires BOTH "all tasks done" AND an explicit `EXIT_SIGNAL: true`.
- A circuit breaker stops the loop after N no-progress or repeated-error iterations.
- A rate limit and `--resume <session_id>` apply.
- An independent reviewer per task and auto-debug after 2 rejections come from `/kiro-impl`.

### M7. Clarify with a question budget, and approval as data
**Sources:** spec-kit `clarify.md` (taxonomy Clear/Partial/Missing, max 5 questions, Impact×Uncertainty ranking, recommended option first, answers written back under `## Clarifications / Session <date>`), cc-sdd `approvals{generated,approved}`, spec-workflow-mcp dashboard approvals.

This directly upgrades Super-Skill's ambiguity scoring. The score becomes the count and weight of Partial/Missing categories. The approval gate for the 10x proposal becomes a field in `state.json` that downstream gates check.

### M8. Change deltas, handoffs and logical-unit revert for evolution and resume
**Sources:** OpenSpec `changes/<id>/{proposal.md, specs/ with ADDED/MODIFIED/REMOVED, tasks.md}` → `archive/`; HumanLayer `create_handoff`/`resume_handoff` plus plans whose phases hold **Automated vs Manual Verification**; Conductor smart revert by track/phase/task; BMAD append-only `.memlog.md` of decisions.

- P11 optimization and P13 self-evolution produce OpenSpec-style change folders instead of rewriting specs in place, so there is an audit trail and they can be merged or archived.
- Every phase end or context limit writes a timestamped handoff.
- Tag phase-boundary commits (`ss/P6-done`) so "revert to phase" works.

---

## 3. Suggested adoption order
1. M1 `state.json` + `phase_state.py`, and M2 `phases.yaml` + `gate_check.py`. This is the base the others build on.
2. M3 REQ IDs and EARS (copy cc-sdd `ears-format.md` and spec-kit `spec-template.md`, both MIT) plus `trace_matrix.py`.
3. M4 `taskgraph.py` and M5 complexity expansion.
4. M6 loop hardening in the existing Ralph phase.
5. M7 clarify budget in the front end; M8 deltas, handoffs and tags.

License cautions:
- Task Master (Commons Clause): borrow the pattern, never vendor the code.
- spec-workflow-mcp (GPL-3.0) and claude-squad (AGPL-3.0): borrow the pattern only.
- cursor-memory-bank and Kiro (no license): do not copy text.
- Everything else cited is MIT or Apache-2.0, so templates can be reused with attribution.
