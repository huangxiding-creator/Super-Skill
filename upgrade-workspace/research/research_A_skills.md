# Research A: Skill, plugin and command ecosystems to borrow from for Super-Skill

**Scope:** Claude Code / agent skill ecosystems, plugin marketplaces, curated skill/agent/command collections, slash-command frameworks.
**Date:** 2026-09-30. Star counts, licenses and push dates were pulled live with `gh api repos/OWNER/REPO` today. "none" means GitHub reports no license and the repo root has no LICENSE file, so all rights are reserved and only the pattern can be borrowed. Every repo listed was confirmed to exist.
**Files read in full or in part:** anthropics/skills `skill-creator`, anthropics/claude-code `plugins/ralph-wiggum`, `plugins/plugin-dev`, `plugins/hookify`, obra/superpowers `hooks/`, `docs/testing.md`, ECC `continuous-learning-v2`, OthmanAdi/planning-with-files `scripts/check-complete.sh`, `gate-stop.sh`, `hooks/hooks.json`, frankbria/ralph-claude-code `lib/circuit_breaker.sh`, agentskills spec plus `skills-ref`, gstack `autoplan/SKILL.md`, oh-my-claudecode `skills/deep-interview/SKILL.md`, SuperClaude `confidence-check`.

## Context: the defect this research targets

Super-Skill's `.claude/settings.json` was inspected. It has these problems:

- **`Notification` and `Stop` use the wrong shape.** Both are written as `{"handler": {"type":"prompt", ...}}` objects. The real schema is an array of `{matcher?, hooks:[{type, command|prompt, timeout}]}`.
- **`PreToolUse` matchers are objects.** They are written as `{"toolName":"Read"}`, but a matcher must be a regex string such as `"Read"` or `"Write|Edit"`.
- **Commands read an env var that does not exist.** They use `$CLAUDE_TOOL_INPUT_FILE_PATH`. Hook input actually arrives as JSON on stdin (`tool_input.file_path`, `transcript_path`, `stop_hook_active`).
- **A session-start sequence is attached to the wrong event.** It is hung on `Notification`; it belongs on `SessionStart`.
- **The Stop "hook" only asks the model to reflect.** It is a prompt that asks the model to run a retrospective. Nothing enforces it.

Several of the projects below ship working, tested versions of these exact mechanisms.

---

## Master table (36 projects)

| # | Project | Stars | License | What it is | Concrete borrowable mechanism | Maps to Super-Skill | Adoption mode |
|---|---|---|---|---|---|---|---|
| 1 | [anthropics/skills](https://github.com/anthropics/skills) | 179,008 | Per-skill; `skill-creator/LICENSE.txt` = Apache-2.0 (docx/pdf/pptx/xlsx are source-available, not OSS) | Official Anthropic Agent Skills repo | `skills/skill-creator/`: `evals/evals.json` schema; with-skill vs baseline subagent runs launched in the same turn; `agents/grader.md` writes `grading.json` (`text/passed/evidence`); `scripts/aggregate_benchmark.py` writes `benchmark.json` (pass-rate/time/tokens, mean±stddev, delta); `scripts/run_loop.py` + `improve_description.py` for trigger optimisation (20 should/should-not-trigger queries); `quick_validate.py`, `package_skill.py`; `history.json` version lineage (won/lost/tie) | Fixes "no benchmark/eval". Covers all 48 sub-skills plus the top-level SKILL.md; also feeds GEP self-evolution (keep a version only if it wins) | **Direct reuse** (Apache-2.0): copy `skill-creator/scripts/*`, `agents/grader.md`, `agents/analyzer.md`, `agents/comparator.md`, `references/schemas.md`, `eval-viewer/` with NOTICE |
| 2 | [anthropics/claude-code](https://github.com/anthropics/claude-code) `plugins/` | 148,591 | Proprietary (© Anthropic, Commercial ToS) | Official CLI repo with 13 reference plugins | (a) `plugins/ralph-wiggum/hooks/stop-hook.sh`: Stop hook reads `.claude/ralph-loop.local.md` frontmatter (`iteration`, `max_iterations`, `completion_promise`), parses the last assistant message from `transcript_path` JSONL, exits only when `<promise>TEXT</promise>` matches, else emits `{"decision":"block","reason":<prompt>,"systemMessage":...}`. (b) `plugins/plugin-dev/skills/hook-development/scripts/validate-hook-schema.sh`, `hook-linter.sh`, `test-hook.sh`. (c) `plugins/hookify/core/rule_engine.py`: markdown-frontmatter rules (`*.local.md`) compiled into Pre/PostToolUse/Stop/UserPromptSubmit checks. (d) `plugins/feature-dev`: explorer → architect → reviewer agent trio | Phase 11 "Ralph loop" becomes a real Stop-hook loop; fixes the invalid hooks; Phase 10 QA gates | **Borrow pattern** only (not OSS). Re-implement in Python |
| 3 | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) | 37,206 | Apache-2.0 | Official plugin directory/marketplace | `.claude-plugin/marketplace.json` catalogue format; inclusion quality bar | Distribution: ship Super-Skill as a plugin with `marketplace.json` so `/plugin install` works | Borrow pattern (schema) |
| 4 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | 25,868 | Apache-2.0 | Anthropic's plugin bundles for knowledge work (finance, legal, data…) | Domain plugin packaging: one plugin = skills + commands + MCP connectors | Packaging the 48 sub-skills as themed sub-plugins | Direct reuse of layout conventions |
| 5 | [agentskills/agentskills](https://github.com/agentskills/agentskills) | 25,795 | Apache-2.0 | Open Agent Skills specification | `docs/specification.mdx`: `name` ≤64 chars `[a-z0-9-]`, `description` ≤1024, `compatibility` ≤500, `metadata`, experimental `allowed-tools`. Progressive disclosure: ~100-token metadata, <5000-token body, **SKILL.md under 500 lines**, details moved to `references/`. `skills-ref/` Python validator CLI (`skills_ref/cli.py`) | CI lint of all 48 sub-skills; splitting the 500-line SKILL.md | **Direct reuse**: `pip install -e skills-ref` in CI (the maintainers label it demo-grade) |
| 6 | [obra/superpowers](https://github.com/obra/superpowers) | 292,988 | MIT | Skills framework plus dev methodology | (a) `hooks/hooks.json`: `SessionStart` matcher `startup\|clear\|compact` runs `hooks/session-start`, which injects `using-superpowers/SKILL.md` via `hookSpecificOutput.additionalContext`, with per-harness output branches. (b) `hooks/run-hook.cmd` polyglot wrapper for Windows (`docs/windows/polyglot-hooks.md`). (c) Skills `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `verification-before-completion`, `test-driven-development`, `using-git-worktrees`, `writing-skills` (TDD for skills: RED baseline without the skill, then GREEN). (d) `tests/explicit-skill-requests/prompts/*.txt` trigger tests plus `tests/claude-code/analyze-token-usage.py` | Replaces the broken Notification session-start; Phase 7–9 implementation via SDD; Windows (user is on win32) | **Direct reuse** (MIT): copy `hooks/session-start`, `run-hook.cmd`, `verification-before-completion`, `subagent-driven-development` |
| 7 | [prime-radiant-inc/superpowers-evals](https://github.com/prime-radiant-inc/superpowers-evals) | 122 | none reported | "Quorum" behavioural eval lab for superpowers | Scenario dirs `evals/scenarios/<name>/` with acceptance criteria plus deterministic post-checks; drives real CLI sessions in tmux; LLM actor plus verifier; static gates on PR, live sweep nightly | End-to-end eval of the whole idea→product pipeline (does it actually stop at the approval gate? does it write the WBS?) | Borrow pattern |
| 8 | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) (ECC) | 269,666 | MIT | Very large harness: skills, hooks, agents, rules | (a) `skills/continuous-learning-v2`: PreToolUse/PostToolUse hooks append to `projects/<hash>/observations.jsonl`; a background Haiku observer mints atomic **instincts** (YAML: `trigger`, `confidence 0.3–0.9`, `domain`, `scope: project\|global`, evidence); `/evolve` clusters instincts into skills/commands/agents; promoted to global when seen in 2+ projects. (b) `scripts/hooks/*.js`: working Node hooks, e.g. `quality-gate.js`, `config-protection.js`, `block-no-verify.js`, `cost-tracker.js`, `pre-compact.js`, `session-end.js`, `evaluate-session.js`, `run-with-flags.js` (per-hook enable flags). (c) `skills/eval-harness`, `santa-method`, `gateguard` | GEP self-evolution plus Cerebrum/Buglog become data-driven, not prose; token-tracker becomes `cost-tracker.js` | **Direct reuse** (MIT): `scripts/hooks/cost-tracker.js`, `config-protection.js`, `run-with-flags.js`; copy the instinct YAML schema |
| 9 | [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | 27,184 | MIT | Manus-style file-based plans with a completion gate | `scripts/check-complete.sh --gate` via `gate-stop.sh` on the Stop hook. It blocks only when ALL hold: `<plan-dir>/.mode` contains `gate`; an `in_progress` phase exists; `stop_hook_active` is not true; the `.stop_blocks` counter is below `PWF_GATE_CAP` (default 20); the ledger advanced since the last block (otherwise it is a stall and stop is allowed). Also `ledger-append.sh`, `session-catchup.py` (recovery after /clear or compaction), `inject-plan.sh` (per-turn re-injection on UserPromptSubmit), `.ps1` twins for Windows. `hooks/hooks.json` is a valid-schema reference | Enforcing the 14-phase workflow: phase state in `task_plan.md`, deterministic "cannot stop until phase N done" | **Direct reuse** (MIT): `check-complete.sh/.ps1`, `gate-stop.sh`, `ledger-append.*`, `session-catchup.py`, `hooks.json` |
| 10 | [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) | 9,640 | MIT | Autonomous Claude Code loop with exit detection (784 tests) | `lib/circuit_breaker.sh`: CLOSED/HALF_OPEN/OPEN state in `.ralph/.circuit_breaker_state`; thresholds `CB_NO_PROGRESS_THRESHOLD=3`, `CB_SAME_ERROR_THRESHOLD=5`, `CB_OUTPUT_DECLINE_THRESHOLD=70%`, `CB_PERMISSION_DENIAL_THRESHOLD=2`, `CB_COOLDOWN_MINUTES=30`. **Dual-condition exit gate**: completion indicators AND an explicit `EXIT_SIGNAL: true`. `lib/response_analyzer.sh`, rate limiting (100 calls/h), three-layer API-limit detection | Phase 9 autonomous experiment loop and Phase 11 Ralph optimisation: stop runaway loops | **Direct reuse** (MIT): port `circuit_breaker.sh` thresholds and state machine to Python |
| 11 | [snarktank/ralph](https://github.com/snarktank/ralph) | 21,885 | MIT | Minimal Ralph loop that runs until all PRD items are done | `prd.json` user stories with `passes: true/false`; loop picks the next failing story, fresh context per iteration, appends `progress.txt` learnings; `AGENTS.md` updated with discovered conventions | Phase 5 requirements output a machine-checkable `prd.json`; Phase 9 loop iterates stories | Direct reuse (MIT) of the `prd.json` schema and loop script |
| 12 | [garrytan/gstack](https://github.com/garrytan/gstack) | 134,511 | MIT | 23+ role skills (CEO, eng manager, designer, QA, release) | (a) `autoplan/SKILL.md`: sequential CEO→design→eng→DX reviews with **6 Decision Principles** (completeness, boil lakes, pragmatic, DRY, explicit>clever, bias to action) and per-phase tiebreakers; taste decisions surfaced only at a final approval gate. (b) **Skill-scoped hooks in SKILL.md frontmatter** (`hooks:` → PreToolUse guard that denies with `permissionDecision:"deny"` if the guard script is missing). (c) `SKILL.md.tmpl` → `scripts/gen-skill-docs.ts` generates SKILL.md from templates with a shared preamble. (d) `scripts/eval-select.ts`, `eval-compare.ts`, `eval-flake-rank.ts` (diff-based eval selection, flake ranking). (e) Decision-brief format with "human: ~2 days / CC: ~15 min" effort labels | Phase 1–2 vision/feasibility as CEO/eng review; proposal scorecard; the approval gate (auto-decide in spawned sessions, ask only on taste); de-duplicating the 48 sub-skills with templates | **Direct reuse** (MIT): 6-principles text, `gen-skill-docs.ts` approach, frontmatter-hook pattern |
| 13 | [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) (OMC) | 39,426 | MIT | Teams-first multi-agent orchestration plugin | (a) `skills/deep-interview/SKILL.md`: Socratic interview with **mathematical ambiguity gating**; threshold resolved from `omc.deepInterview.ambiguityThreshold` in settings (default 0.2); Round-0 topology lock; each question targets the weakest clarity dimension; mission and evaluator clarity are hard gates; flow deep-interview → consensus plan → pending approval → execution. (b) `/autopilot --workflow` stage profiles (`[ralplan, execution, ralph, qa]`) in `.claude/omc.jsonc`. (c) `/team N:executor` in-session teams plus `omc team 2:codex` tmux workers | Super-Skill's ambiguity scoring (currently prose) becomes configurable and gated; the 14 phases become declarable stage profiles; a real multi-agent runtime | **Direct reuse** (MIT): deep-interview scoring rubric and threshold logic |
| 14 | [SuperClaude-Org/SuperClaude_Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) | 23,914 | MIT | Command, persona and mode framework (`/sc:*`) | `.claude/skills/confidence-check/SKILL.md` + `confidence.ts`: pre-implementation score = duplicate check 25% + architecture compliance 25% + official docs verified 20% + OSS reference 15% + root cause 15%; ≥0.90 proceed, ≥0.70 present alternatives, below that stop. `docs/memory/reflexion.jsonl` mistake log; `/sc:spec-panel`, `/sc:business-panel` expert panels | Gate between Phase 6 architecture and Phase 8 init; feasibility scorecard; Buglog becomes reflexion.jsonl | **Direct reuse** (MIT): `confidence.ts` weights |
| 15 | [github/spec-kit](https://github.com/github/spec-kit) | 139,455 | MIT | Spec-Driven Development toolkit | `templates/commands/{constitution,specify,clarify,plan,tasks,analyze,checklist,implement,converge,taskstoissues}.md` plus `constitution-template.md`, `spec-template.md`, `plan-template.md`, `tasks-template.md`; `/analyze` cross-artifact consistency check; `[NEEDS CLARIFICATION]` markers; extension and preset system | Phase 5 requirements → 6 architecture → 7 WBS use proven templates; `/analyze` as a consistency gate | **Direct reuse** (MIT): templates |
| 16 | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | 70,695 | MIT | Lightweight SDD with change proposals | `openspec/changes/<id>/{proposal.md,tasks.md,specs/}` delta specs, then `archive` merges into `openspec/specs/`; validate command | Phase 11 optimisation and GEP changes as auditable change proposals | Direct reuse (MIT) of directory convention |
| 17 | [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | 64,435 | MIT | Meta-prompting, context-engineering SDD system | `commands/gsd/{discuss-phase,plan-phase,execute-phase,autonomous,audit-milestone,extract-learnings,forensics,health}.md`; phase directories with PLAN/SUMMARY; fresh-context subagent per plan; milestone audit | 14-phase workflow skeleton; `autonomous.md` for unattended runs; `forensics` for failed runs | Direct reuse (MIT) of command files |
| 18 | [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 25,331 | MIT | 36-skill plugin built on a brainstorm→plan→work→review→**compound** loop | "Compound" step writes learnings where the next change reads them (`docs/solutions/`); `ce-pov` recommendation plus "oracle this" multi-model opinions; `.compound-engineering/config.example.yaml` | GEP self-evolution: every run ends by writing a reusable solution doc; multi-model review for the proposal | Direct reuse (MIT) |
| 19 | [wshobson/agents](https://github.com/wshobson/agents) | 40,095 | MIT | 94 plugins / 202 agents / 184 skills / 105 commands, 6 harnesses | Granular plugins (small, single-purpose, token-cheap); one source `plugins/` generating Codex/Cursor registries; `agent-orchestration`, `agent-teams`, `before-you-build` plugins; model tiering per agent | Splitting the 48 sub-skills into installable plugins; per-agent model assignment (Haiku for scans) | Direct reuse (MIT) |
| 20 | [wshobson/commands](https://github.com/wshobson/commands) | 2,644 | MIT | Production slash commands (last push 2025-10) | `workflows/` multi-agent orchestration commands vs `tools/` single-purpose commands | Super-Skill slash-command entry points per phase (`/ss:research`, `/ss:propose`…) | Direct reuse (MIT) |
| 21 | [mattpocock/skills](https://github.com/mattpocock/skills) | 272,119 | MIT | Lean engineering skills (`grilling`, `tdd`, `domain-modeling`, `prototype`, `research`, `wizard`) | `grilling` one-question-at-a-time interrogation; `.agents/adr/*.md` recording design decisions for the skill pack itself; `.changeset/` per-skill release notes; `writing-for-agents` | Idea-intake questioning before ambiguity scoring; ADRs for Super-Skill's own evolution; changesets instead of README_V2/V3 | Direct reuse (MIT) |
| 22 | [ruvnet/claude-flow](https://github.com/ruvnet/claude-flow) (now "Ruflo") | 73,522 | MIT | Swarm/hive-mind harness with MCP tools | MCP server exposing `swarm_init`, `agent_spawn`, `memory_store` (as `mcp__plugin_ruflo-core_ruflo__*`); router → swarm → agents → memory; plugin split `ruflo-swarm`, `ruflo-rag-memory` | Possible real multi-agent runtime/memory backend, but heavy. Borrow the tool-surface idea only | Borrow pattern |
| 23 | [parcadei/Continuous-Claude-v3](https://github.com/parcadei/Continuous-Claude-v3) | 3,944 | MIT | Context management via hooks, ledgers and handoffs | `.claude/agents/*.md` + `*.json` agent definitions (architect, critic, judge, oracle, maestro…); continuity ledger plus handoff docs written by PreCompact/SessionEnd hooks | Cross-session continuity for a 14-phase run that spans many sessions | Direct reuse (MIT) |
| 24 | [LearnPrompt/cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills) | 236 | MIT | 6 portable skills distilled from a CC-style harness | `verification-gate`, `dream-memory` (offline memory consolidation), `kairos-lite` (proactive jobs), `memory-extractor`, coordinator; `skills/check_all.sh` validation; `TEST_REPORT.md` | Phase 10 QA verification gate; cerebrum consolidation | Direct reuse (MIT) |
| 25 | [cytostack/openwolf](https://github.com/cytostack/openwolf) | 2,366 | **AGPL-3.0** | Project memory plus token accounting from transcripts | `anatomy.md`, `cerebrum.md`, buglog; token counters parsed from harness transcripts (not guessed from file size); repeated-read detection | Super-Skill already copies these ideas (anatomy/cerebrum/token-tracker) | **Borrow pattern only.** AGPL is incompatible with copying code into a permissively-licensed skill. Re-implement token accounting from `transcript_path` JSONL |
| 26 | [tanweai/pua](https://github.com/tanweai/pua) | 19,706 | none | High-agency "PIP" skill | Pressure escalation L0–L4 keyed on consecutive failures (2nd failure → switch to a fundamentally different approach; L3 → 7-point checklist enforced); explicit "does NOT trigger on first failure" | Phase 9/11 stuck-loop recovery ladder (pairs with the circuit breaker) | Borrow pattern (no license) |
| 27 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 25,408 | MIT | 161+ subagents in 10 categories, installable as plugins | Subagent frontmatter (`tools:`, `model:`) conventions; `voltagent-meta` orchestration agents | Ready-made subagents for Phases 6/10 (architect, QA, security) | Direct reuse (MIT) |
| 28 | [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates) | 32,181 | MIT | `npx claude-code-templates` installer plus aitmpl.com catalogue | Component-typed installer (`--agent`, `--command`, `--hook`, `--setting`, `--mcp`, `--skill`); analytics and health-check dashboards | One-line Super-Skill installer; settings/hook templates known to validate | Direct reuse (MIT) |
| 29 | [vercel-labs/skills](https://github.com/vercel-labs/skills) (skills.sh CLI) | 32,792 | MIT | `npx skills` open installer | `skills add owner/repo --skill X -a claude-code -g -y`; `skills use` (temporary prompt); update checks; multi-agent targets | Super-Skill's Pre-Run Upgrade can call `npx skills check/update` instead of prose | Direct reuse (MIT, call the CLI) |
| 30 | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 31,727 | none | Vercel's official skills | `web-design-guidelines`, React best-practice skills with rule files | Phase 10 frontend QA rules | Borrow pattern |
| 31 | [openai/skills](https://github.com/openai/skills) | 27,813 | Per-skill `LICENSE.txt` Apache-2.0 | Codex skills catalogue | `skills/.system` vs `skills/.curated` vs experimental tiers; `define-goal`, `gh-fix-ci`, `cli-creator` skills | Tiering the 48 sub-skills (core / curated / experimental) | Direct reuse (Apache-2.0 per skill) |
| 32 | [openai/codex](https://github.com/openai/codex) | 127,213 | Apache-2.0 | Codex CLI (native skills + AGENTS.md) | Skills discovery from `~/.codex/skills` / `.agents/skills`; AGENTS.md convention | Cross-harness portability (write AGENTS.md alongside CLAUDE.md) | Borrow pattern |
| 33 | [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) | 47,132 | MIT | 168 scientific skills | CI rule: **any skill shipping `scripts/` must ship a test suite, else the PR is blocked** (`skill-tests.yml`); provenance and safety-boundary sections per skill | Enforce tests for Super-Skill's ~10 Python scripts | Direct reuse (MIT) of the CI workflow |
| 34 | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 75,896 | none | Curated skills list | Discovery source | Phase 3 GitHub discovery seed list | Reference only |
| 35 | [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) | 15,220 | none | Curated skills list | Discovery source | Phase 3 seed list | Reference only |
| 36 | [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 54,813 | CC BY-NC-ND 4.0 | Curated Claude Code resources (skills, hooks, status lines, plugins) | Discovery source; categorised hook/orchestrator lists | Phase 3 seed list | Reference only (ND: no derivatives) |

Additional repos verified but not expanded above:

| Project | Stars | License | Note |
|---|---|---|---|
| [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) | 1,284 | MIT | Minimal third-party `marketplace.json` example |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | 26,926 | MIT | 380 skills incl. C-level advisory and product. A source for proposal/business sub-skills |
| [jeremylongshore/tons-of-skills-marketplace](https://github.com/jeremylongshore/tons-of-skills-marketplace) | 2,798 | MIT | Harness-free canonical skill layer plus adapters |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | 3,930 | none | Examples for all hook events (uv single-file Python hooks). Pattern only |
| [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | 53,647 | custom (NOASSERTION) | Analyst→PM→Architect→SM→Dev agent roles; story-sharding. Pattern only |
| [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 11,627 | NOASSERTION | research→plan→implement commands with human approval. Pattern only |
| [karpathy/autoresearch](https://github.com/karpathy/autoresearch) | 97,013 | none | The experiment loop Super-Skill cites. Pattern only (no license) |
| [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) | 53,070 | MIT | Agent-pattern notebooks (orchestrator-workers, evaluator-optimizer) |

---

## Top 8 mechanisms to adopt (with specifics)

### 1. Fix and harden the hooks first: copy valid-schema hooks and add a schema lint
**Source:** planning-with-files `hooks/hooks.json` and obra/superpowers `hooks/hooks.json` + `run-hook.cmd` (MIT). The validator pattern comes from claude-code `plugin-dev/.../validate-hook-schema.sh` (not OSS, so re-implement it).

**How:** rewrite `.claude/settings.json` in this form:
```json
"hooks": {
  "SessionStart": [{"matcher": "startup|resume|clear|compact",
    "hooks": [{"type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/.claude/skills/super-skill/scripts/hooks/session_start.py\"", "timeout": 15}]}],
  "PreToolUse":  [{"matcher": "Read|Write|Edit", "hooks": [{"type": "command", "command": "python .../pre_tool.py"}]}],
  "Stop":        [{"hooks": [{"type": "command", "command": "python .../phase_gate.py"}]}]
}
```
The scripts read stdin JSON (`tool_input.file_path`, `transcript_path`, `stop_hook_active`). SessionStart context is emitted as `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":...}}`, following superpowers' `session-start`.

Add `scripts/validate_hooks.py` with these checks: events must be in the valid set; each entry needs a string `matcher` and a `hooks[]` array; `type` must be `command` or `prompt`; timeouts must be sane. Wire it into `health_check.py` and CI. Use superpowers' polyglot `run-hook.cmd` for Windows.

### 2. Make the 14-phase workflow enforceable with a Stop-hook phase gate
**Source:** planning-with-files `scripts/check-complete.sh --gate` + `gate-stop.sh` (MIT). Ralph-wiggum `stop-hook.sh` supplies the `<promise>` pattern.

**How:** keep `.super-skill/state/phase_plan.md` (phases with `status: pending|in_progress|complete`) plus a `ledger.jsonl`. The Stop hook returns `{"decision":"block","reason":"<next phase instructions>"}` only when ALL of these hold:
- gate mode is on
- a phase is `in_progress`
- `stop_hook_active` is false
- the `.stop_blocks` counter is below the cap (default 20)
- the ledger has advanced since the last block

If the ledger has not advanced, the run has stalled and the hook lets it stop. Completion requires the exact `<promise>PHASE_14_DONE</promise>` token. Add `session_catchup.py` to rebuild context after `/clear` or compaction, and `inject_plan` on `UserPromptSubmit` to fight context rot.

### 3. Add a real skill benchmark: the skill-creator eval stack
**Source:** anthropics/skills `skills/skill-creator` (Apache-2.0, copy with notice).

**How:**
- Each sub-skill gets `evals/evals.json` (`id`, `prompt`, `expected_output`, `files`, `expectations[]`).
- `run_eval.py` runs with-skill and baseline (no skill, or the previous snapshot) in parallel.
- `agents/grader.md` writes `grading.json`, using exactly the fields `text/passed/evidence`.
- `aggregate_benchmark.py` writes `benchmark.json`/`.md` (pass-rate, time, tokens, mean±stddev, delta).
- `agents/analyzer.md` flags non-discriminating or flaky assertions.
- `history.json` tracks v0→vN with won/lost/tie results.

Also run `run_loop.py` + `improve_description.py` with 20 near-miss trigger queries per sub-skill; this matters because 48 sub-skills compete for triggering. Add superpowers-style `tests/explicit-skill-requests/prompts/*.txt` for top-level triggering.

### 4. Loop safety: circuit breaker, dual-condition exit and a pressure ladder
**Source:** frankbria/ralph-claude-code `lib/circuit_breaker.sh` (MIT) plus tanweai/pua (pattern only, no license).

**How:** add `scripts/loop_guard.py` for Phase 9 (autoresearch-style experiments) and Phase 11 (Ralph).
- It keeps a CLOSED/HALF_OPEN/OPEN state file.
- It opens on 3 no-progress loops, 5 same-error loops, a >70% output decline, or 2 permission denials, then cools down for 30 minutes.
- Exit requires BOTH completion indicators AND an explicit `EXIT_SIGNAL: true` line (the dual-condition gate), which stops premature "done" claims.
- On the 2nd consecutive failure it forces a fundamentally different approach; at L3 it forces a 7-point diagnostic checklist (PUA ladder).

Log every experiment to `experiments.tsv` with keep/discard, as Super-Skill already intends.

### 5. Turn ambiguity scoring and the proposal gate into configurable math
**Source:** oh-my-claudecode `skills/deep-interview/SKILL.md` (MIT), SuperClaude `confidence-check` (MIT) and gstack `autoplan` 6 principles (MIT).

**How:**
- **Resolve the threshold first.** Read `superSkill.ambiguityThreshold` from project, then user settings, else default 0.2, and print its source.
- **Lock the scope.** Round-0 topology lock of top-level components.
- **Score every answer.** Score clarity dimensions (goal, users, constraints, success metric/evaluator, scope) after each answer, and aim the next question at the weakest dimension. Mission clarity and evaluator clarity are hard gates.
- **Gate before implementation.** Use the SuperClaude weighted checklist (dup 25 / arch 25 / docs 20 / OSS ref 15 / root cause 15; ≥0.90 go).
- **Auto-decide mechanical choices.** Apply gstack's 6 principles and surface only taste decisions at the approval gate. In spawned or headless sessions, auto-pick the recommended non-destructive option and log it.

Implement the scoring in `scripts/ambiguity.py` so the number is computed, not narrated.

### 6. Self-evolution driven by data: instincts, then a compounding doc
**Source:** ECC `skills/continuous-learning-v2` (MIT) and compound-engineering (MIT).

**How:**
- PostToolUse and Stop hooks append to `.super-skill/observations.jsonl`.
- A Haiku background pass mints atomic instincts (`id`, `trigger`, `confidence 0.3–0.9`, `domain`, `scope: project|global`, `evidence`).
- Confidence rises on repeat and falls on contradiction.
- `/ss:evolve` clusters instincts with ≥0.7 confidence into sub-skill patches. Each patch is kept **only if its skill-creator benchmark wins** (mechanism 3); this makes GEP a real keep/discard loop.
- An instinct seen in 2+ projects is promoted to global.
- Every run ends by writing `docs/solutions/<slug>.md` (compound step).

This replaces the prose Cerebrum/Buglog Stop prompt.

### 7. Shrink SKILL.md with templates and progressive disclosure; lint in CI
**Source:** agentskills spec + `skills-ref` (Apache-2.0), gstack `SKILL.md.tmpl` + `scripts/gen-skill-docs.ts` (MIT) and K-Dense CI rule (MIT).

**How:**
- **Cut the root SKILL.md.** Aim for ≤150 lines: a router table from phase to sub-skill, plus the gate rules. Move phase detail into `references/phase-XX.md`.
- **Generate the sub-skills from templates.** Use `SKILL.md.tmpl` plus a shared preamble (state-file paths, gate protocol) and a Python generator, so the 48 files do not drift.
- **Lint and test in CI.** Run `skills-ref validate` (name `[a-z0-9-]` ≤64, description ≤1024 and "pushy", body <5k tokens). Add a K-Dense-style check that fails if any `scripts/` directory lacks tests.
- **Track changes per skill.** Use `.changeset/` (mattpocock) instead of README_V2/V3.

### 8. Real multi-agent execution and packaging as a plugin
**Source:** superpowers `subagent-driven-development` + `dispatching-parallel-agents` (MIT), OMC `/team` and stage profiles (MIT), claude-code `feature-dev` agent trio (pattern), wshobson/agents granular plugins (MIT) and anthropics marketplace schema (Apache-2.0).

**How:**
- **Ship real subagents.** Add `.claude/agents/{researcher,architect,implementer,spec-reviewer,code-reviewer,qa}.md` with `tools:` and `model:` frontmatter (Haiku for scans, Sonnet/Opus for architecture).
- **Run tasks through SDD.** Phase 7 WBS emits tasks; Phase 9 dispatches one fresh implementer subagent per task, then a spec-compliance review, then a code-quality review, with worktrees for parallel tasks.
- **Make phase order configurable.** Declare it as stage profiles (`[research, propose, gate, plan, build, qa, ralph, deploy]`) in `.super-skill/config.json`.
- **Package it as a plugin.** Ship `.claude-plugin/plugin.json` + `marketplace.json` (and optionally split into themed sub-plugins) so installs run through `/plugin install` or `npx skills add huangxiding-creator/Super-Skill`.

---

## License quick reference for direct reuse
- **Safe to copy with attribution (MIT):** superpowers, ECC, planning-with-files, frankbria/ralph, snarktank/ralph, gstack, OMC, SuperClaude, spec-kit, OpenSpec, GSD, compound-engineering, wshobson/*, mattpocock/skills, cc-harness-skills, Continuous-Claude-v3, VoltAgent, davila7, vercel-labs/skills, K-Dense.
- **Safe to copy with attribution and NOTICE (Apache-2.0):** anthropics/skills `skill-creator` (per-skill LICENSE.txt), openai/skills (per-skill), agentskills, claude-plugins-official, knowledge-work-plugins, openai/codex.
- **Do NOT copy code:**
  - anthropics/claude-code plugins (proprietary)
  - openwolf (AGPL-3.0)
  - hesreallyhim list (CC BY-NC-ND)
  - pua, karpathy/autoresearch, vercel-labs/agent-skills, awesome lists (no license)
  - BMAD and humanlayer (custom/NOASSERTION)

  Borrow patterns only.
