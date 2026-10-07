---
name: super-skill
description: "Idea→product factory for building software end-to-end with Claude Code. Use when the user gives a raw product idea, asks to build an app/tool/system from scratch, wants autonomous multi-phase development (research → 10× proposal → approval → requirements → architecture → tasks → build → QA → deploy → evolve), or mentions super-skill / 从想法到产品 / 自主开发 / 全流程开发 / 做一个产品. V5 executable engine: machine-checked phase gates, hooks that block unsafe actions and premature stops, REQ→task→test traceability, parallel worktree workers, circuit-breaker Ralph loop, budgets, evals and benchmark-driven self-evolution."
---

# Super-Skill V5.0 — Idea→Product Factory (executable)

**V5 principle: prose guides, code enforces.** Every rule that must hold is a check in
`phases.json`, a hook, or an engine command — not a sentence you are trusted to remember.

## 0. Operating contract (read first)

1. **Engine CLI.** When this skill loads, Claude Code prints its *Base directory*. Use
   `python "<base>/engine/ss.py" <command>` (the SessionStart hook also prints the exact,
   machine-correct command line). Below, `ss` means that command.
2. **State is owned by the engine.** Never edit `.super-skill/state.json`, `ledger.jsonl` or
   `tasks.json` by hand — the PreToolUse guard denies it. Use `ss` commands.
3. **A phase is done when `ss advance` passes**, not when you believe it is. `ss gate` shows
   exactly which check fails; fix the artifact, re-run.
4. **Approvals belong to the user.** `ss approve <name>` always triggers a confirmation
   prompt; present the artifact, ask, and let the user confirm. Never approve for them.
5. **Autonomy after approval.** In autonomous phases the Stop hook keeps you working until the
   gate passes. For a genuinely human-only step (credentials, payment, legal sign-off) run
   `ss wait "<reason>"`, explain it to the user, then stop.
6. **Honesty (constitution C12/C14).** No fabricated data, numbers, test results or sources.
   Verify with commands; quote real output.

## 1. Start a run

| Situation | Command |
|---|---|
| Raw / vague idea (text, transcript, attachment) | `ss init --project <name> --from IF1` |
| Clear product brief, no requirements yet | `ss init --project <name> --from P0` |
| Requirements already written | `ss init --project <name> --from P4` |
| Set the test command (used by P7–P10 gates) | `ss config test_cmd "pytest -q"` |
| Optional spend cap (warn 70 %, hard stop 100 %) | `ss config budget.usd_limit 20` |

Then loop: `ss next` → do the phase work with its sub-skill → `ss gate` → fix → `ss advance`.
`ss status` shows all phases; `ss goto <phase>` rewinds (later phases become *stale*).

## 2. Core philosophy (condensed — full text in [skill-v4-full](references/skill-v4-full.md))

- **Think first, code later** — maximise upfront thinking; the three human touchpoints are:
  the idea, the **proposal approval** (IF3) and the **requirements approval** (P4).
- **Verifier > generator** — when progress stalls, strengthen the check, not the prompt.
- **C0 复利元则** — every success becomes a repeatable method, every failure a constraint,
  every correction a reusable judgment (→ playbook, §8). [dev-constitution](references/dev-constitution.md)
- **缝合怪原则** — world-class parts × explicit hand-off contracts × whole-system production run;
  optimise the bottleneck only (Amdahl). [stitching-monster](references/stitching-monster.md)
- **Stand on giants' shoulders (C4)** — search before building; from-scratch needs a documented miss.
- **Simplicity criterion** — deleting code that keeps the score is a win; complexity must pay.

## 3. Phase map (contracts live in `phases.json`)

| ID | Phase | Sub-skill | Required outputs | Human? |
|---|---|---|---|---|
| IF1 | Idea Intake | [idea-intake](skills/idea-intake/SKILL.md) | `IDEA_SEED.md` | ≤3 questions if ambiguous |
| IF2 | Research | [research-orchestrator](skills/research-orchestrator/SKILL.md) | `RESEARCH_DIGEST.md`, `GAP_REPORT.md` | – |
| IF3 | Proposal Forge | [proposal-forge](skills/proposal-forge/SKILL.md) | `PROPOSAL.md`, `SCORECARD.json` (verdict=proceed) | **approve `proposal`** |
| P0 | Visionary Elevation | [darwin-evolution](skills/darwin-evolution/SKILL.md) | `VISION.md`, `AI_NATIVE_OPTIONS.md` | – |
| P1 | Feasibility | feasibility check (CC-FPS ≥0.7) | `FEASIBILITY_REPORT.md`, `RISK_REGISTER.md` | – |
| P2 | GitHub Discovery | github-discovery · `ss-researcher` | `GITHUB_DISCOVERY_REPORT.md` (≥3 repos) | – |
| P2b | Skills Discovery | [find-skills](skills/find-skills/SKILL.md) | `SKILLS_DISCOVERY.md` (optional) | – |
| P3 | Knowledge Base | continuous-learning · [get-api-docs](skills/get-api-docs/SKILL.md) | `KNOWLEDGE_BASE/*.md`, `CONTEXT.md` | – |
| P4 | Requirements | [brainstorming](skills/brainstorming/SKILL.md) · [real-engineering](skills/real-engineering/SKILL.md) · `ss-spec-reviewer` | `REQUIREMENTS.md` (EARS + `REQ-###`) | **approve `requirements`** |
| P5 | Architecture | [api-patterns](skills/api-patterns/SKILL.md) · [data-patterns](skills/data-patterns/SKILL.md) | `ARCHITECTURE.md`, `API_DESIGN.md` | – |
| P6 | WBS / task graph | `ss-planner` | `WBS.md`, `.super-skill/tasks.json` (valid, covers all MUST) | – |
| P7 | Project Init | [cicd-automation](skills/cicd-automation/SKILL.md) · [auto-git-create](skills/auto-git-create/SKILL.md) | git repo, `config.test_cmd` passing | – |
| P8 | Autonomous Dev | [autonomous-loop](skills/autonomous-loop/SKILL.md) · `ss-worker` × N · `ss-judge` | all tasks done, tests green | – |
| P9 | QA | [testing-automation](skills/testing-automation/SKILL.md) · [security-scanning](skills/security-scanning/SKILL.md) | `QA_REPORT.md`, every MUST REQ has a test | – |
| P10 | Ralph Loop | [autonomous-loop](skills/autonomous-loop/SKILL.md) | `RALPH_REPORT.md`, tests green | – |
| P11 | Deploy | [cicd-automation](skills/cicd-automation/SKILL.md) · [monitoring-observability](skills/monitoring-observability/SKILL.md) | `DEPLOYMENT.md` | wizard for human-only steps |
| P12 | Evolution | [post-run-evolution](skills/post-run-evolution/SKILL.md) | `EVOLUTION_REPORT.md`, playbook updates | – |

### Phase notes

- **IF1–IF3 Idea Factory** — ambiguity score → Hybrid Clarification Gate; 9-channel research +
  gap analysis; maturity + ten× delta index + pricing → scorecard. 任鑫选品五法 / 三筛 / 第一天变现:
  [renxin-ai-product-methodology](references/renxin-ai-product-methodology.md); research reading/judging/writing:
  [research-methodology](references/research-methodology.md); method + algorithms: [ideaforge](references/ideaforge.md).
- **P0 Vision** — C1 hardest problem, C2 boldness is legal, C3 world-best-and-landable.
- **P2 Discovery** — score ≥80 % → clone-and-adapt (缝合怪律一); reuse `RESEARCH_DOCKET/github` if IF2 ran.
- **P3 Knowledge Base** — 修路: 业务过程留痕 + 5-minute ontology; `CONTEXT.md` glossary (lint: `context_lint.py`).
  [ai-native-coordination](references/ai-native-coordination.md)
- **P4 Requirements** — write every requirement as `- REQ-001 [MUST]: When <event>, the system shall <response>.`
  (Chinese: `当…时，系统应…`) with acceptance criteria `REQ-001.AC1`; no `[NEEDS CLARIFICATION]` left;
  JTBD 三步法. Run `ss-spec-reviewer`, then present for approval.
- **P5 Architecture** — optimal under real constraints; ADRs for rejected options; explicit hand-off
  contracts between components (缝合契约: upstream DoD + downstream entry condition).
- **P6 WBS** — delegate to the `ss-planner` subagent; tracer-bullet vertical slices; each task has
  `covers`, `after`, `verify`; split complexity > 5; `ss task waves` shows parallel waves.
- **P8 Autonomous Dev** — see §5. 检查四层: automatic gates · adversarial Judge (context-isolated) ·
  human spot checks · rollback. Iceberg rule: fix one bug → scan for the pattern everywhere.
- **P9 QA** — two-axis review (standards ∥ spec); `ss trace build --require tests` must pass.
- **P10 Ralph** — bottleneck first (Amdahl); each round: timeline → waste → root cause → fix → verify
  the metric moved (三线复盘). [audit-loop-case-study](references/audit-loop-case-study.md)
- **P11 Deploy** — human-only steps get a generated wizard (`wizard_template.sh`) + `ss wait`.
- **P12 Evolution** — convert learnings into playbook rules (§8) and, when warranted, a
  benchmark-verified skill mutation (§10).

## 4. Requirements → tasks → tests (traceability)

- `ss trace ears` — every requirement is EARS-form.
- `ss task add "title" --covers REQ-001.AC1 --after T-001 --verify "<cmd>" --files a.py`
- `ss task validate | waves | complexity | ready | next | claim | done ID | fail ID`
- `ss trace build --require tasks` (P6 gate) / `--require tests` (P9 gate) → `.super-skill/trace.md`.
- Name tests after requirements (`test_req_001_ac1_*`) so coverage is detected automatically.

## 5. Autonomous development (P8) — Planner → Worker → Judge

1. `ss task waves` → tasks that can run in parallel.
2. For each ready task: `ss task claim <id> --owner <worker>` then spawn an **`ss-worker`**
   subagent (runs in its own git worktree via `isolation: worktree`). Independent tasks of one
   wave may be dispatched in parallel.
3. Each result goes to an **`ss-judge`** subagent (read-only, context-isolated). `KEEP` → merge
   the worktree branch, `ss task done <id>`; `DISCARD` → `ss task fail <id> --note "<why>"`.
4. The **loop guard** watches every tool call: repeated actions/errors or A-B-A-B alternation
   inject a pressure-ladder instruction (L1 switch approach → L4 write a BLOCKER and move on).
5. **Unattended mode**: `ss ralph --max-iterations 30 --budget-usd 2` runs one task per fresh
   `claude -p` iteration, verifies with the task's own command (ground truth), commits on KEEP,
   feeds a circuit breaker (3 no-progress / 5 same-error / 2 permission denials → OPEN, 30 min
   cooldown) and exits only when all tasks pass **and** the agent prints `EXIT_SIGNAL: true`.
   Every iteration is logged to `experiments.tsv` and `progress.txt`.
- Freedom by task: high (reviews/refactors) · medium (features) · low (migrations/deploys — exact scripts).
- Agent role configuration (训虾派): [yitang-agent-forge](references/yitang-agent-forge.md).

## 6. Hooks — what fires when (installed by `install.py`)

| Event | Script | Effect |
|---|---|---|
| SessionStart (startup/resume/clear/compact) | `session_start.py` | injects phase, next action, static gate result, tasks, playbook, last hand-off |
| UserPromptSubmit | `user_prompt.py` | one-line phase reminder; resets the Stop-gate counter |
| PreToolUse (Bash/PowerShell/Read/Edit/Write…) | `pre_tool.py` | **deny** destructive shell, force-push, secrets, direct state edits, blocking playbook rules, exhausted budget · **ask** for approvals, pushes to main, download-and-execute |
| PostToolUse (+Failure) | `post_tool.py` | event log, progress counter, stuck detection, playbook warnings, budget warnings |
| PreCompact | `pre_compact.py` | writes `.super-skill/handoff.md` |
| Stop | `stop_gate.py` | blocks premature stops in autonomous phases (anti-loop: stall detection, 20-nudge cap) |
| SubagentStop / SessionEnd | `log_event.py` | observability |

All hooks are fail-open and do nothing outside a directory containing `.super-skill/state.json`.

## 7. Context engineering

- JIT context: load files with tools when needed; `ss route "<goal>"` ranks the sub-skills to load
  (top-5 instead of all 48).
- Progressive disclosure: this file is the router; details live in `references/` (≤2 levels deep).
- Compaction survival: hand-off before compaction, re-injected on resume.
- Anatomy / token discipline: [anatomy-scanner](skills/anatomy-scanner/SKILL.md), [token-tracker](skills/token-tracker/SKILL.md).

## 8. Memory & learning (replaces prose Cerebrum)

- `ss playbook add do-not-repeat "<rule>" --pattern "<regex>" [--block]` — `--block` rules are
  enforced by the PreToolUse guard; others warn after edits.
- `ss playbook vote <id> --helpful|--harmful` — rules with harmful > helpful + 2 retire automatically;
  updates are append-only deltas (ACE), superseded rules keep their history.
- `ss playbook import-md <cerebrum.md>` migrates V4 cerebrum files.
- `ss mem index` / `ss mem search "<query>"` / `ss mem get <id>` — SQLite FTS5 search over
  KNOWLEDGE_BASE, root docs, hand-offs, progress notes and playbook (Chinese via trigram).
- AI-Mastery 7 disciplines (plan-first, KB onboarding, rationale mining, weekly retro):
  [ai-mastery-7](skills/ai-mastery-7/SKILL.md) · [ai-mastery](references/ai-mastery.md).

## 9. Budget & observability

- `ss config budget.usd_limit N` (and/or `budget.token_limit`) — warn at 70 %, deny new work at
  100 % (`budget.hard_stop false` to only warn). Costs are **estimates** from transcript tokens
  (deduplicated by message id + request id; override rates in `.super-skill/pricing.json`).
- `ss cost report --root .` — per-phase duration, tool calls, failures, gate failures, breaker
  trips → `.super-skill/REPORT.md`. Use it for the P10/P12 retrospective instead of memory.
- Raw event stream: `.super-skill/events.jsonl` (one line per hook call).

## 10. Self-evolution (benchmark-driven GEP)

`ss evolve --target <file> --eval-cmd "<cmd printing {tasks:{id:score}}>" --iterations N [--apply]`
keeps an archive of **all** variants, selects parents DGM-style, mutates one section at a time
from failure feedback (GEPA-style reflection), evaluates smoke-then-full, keeps only
improvements (fitness = pass rate − token cost − added lines) and applies the best only when it
beats the seed (backup first). Default fitness for engine changes:
`python "<base>/evals/bench_offline.py"`. Protocol and genes: [EVOLUTION.md](EVOLUTION.md) ·
[evolver/README](evolver/README.md) · strategies `balanced|innovate|harden|repair-only`.

**Nightly self-update (repo side):** `automation/superskill_daily.py`, scheduled for 22:00 Beijing time by
`automation/schedule_daily.py`, scans GitHub, a watchlist of best-in-class repos and Hacker News; a headless run
stages ≤3 small improvements; a whitelist keeps the verifier (tests, bench, phase contracts, hooks, installer)
out of reach; the full check suite must pass or the run is reverted; then it commits, reinstalls and pushes.
Digests: [references/radar](references/radar/README.md).

## 11. Evals — prove it works

- Offline bench (free, ~5 s, 13 scenarios): `python "<base>/evals/bench_offline.py" --pretty`.
- Model evals with/without the skill: `claude plugin eval <repo> --runs 1` (cases in the repo's `evals/`).

## 12. Install & verify on any machine

`python install.py --global --hooks` (from the repo, or `python ~/.claude/skills/super-skill/install.py --hooks`
after `npx skills add`) copies the skill + subagents, registers hooks with this machine's Python,
merges (never replaces) settings with a backup, then runs `--doctor`. `python install.py --doctor`
re-checks everything; `--uninstall-hooks` removes only Super-Skill hooks. Requires Python ≥ 3.9.

## 13. Sub-skills (48)

| Area | Sub-skills |
|---|---|
| Idea Factory | [idea-intake](skills/idea-intake/SKILL.md) · [research-orchestrator](skills/research-orchestrator/SKILL.md) · [proposal-forge](skills/proposal-forge/SKILL.md) · [monetization-scaffold](skills/monetization-scaffold/SKILL.md) |
| Discipline | [ai-mastery-7](skills/ai-mastery-7/SKILL.md) · [real-engineering](skills/real-engineering/SKILL.md) · [high-agency](skills/high-agency/SKILL.md) · [cognitive-modes](skills/cognitive-modes/SKILL.md) · [verification-gate](skills/verification-gate/SKILL.md) · [systematic-debugging](skills/systematic-debugging/SKILL.md) · [advanced-reasoning](skills/advanced-reasoning/SKILL.md) · [brainstorming](skills/brainstorming/SKILL.md) |
| Loop & evolution | [autonomous-loop](skills/autonomous-loop/SKILL.md) · [pre-run-upgrade](skills/pre-run-upgrade/SKILL.md) · [post-run-evolution](skills/post-run-evolution/SKILL.md) · [darwin-evolution](skills/darwin-evolution/SKILL.md) · [multi-agent-orchestration](skills/multi-agent-orchestration/SKILL.md) |
| Memory & context | [memory-pipeline](skills/memory-pipeline/SKILL.md) · [context-compressor](skills/context-compressor/SKILL.md) · [context-management](skills/context-management/SKILL.md) · [cerebrum](skills/cerebrum/SKILL.md) · [anatomy-scanner](skills/anatomy-scanner/SKILL.md) · [token-tracker](skills/token-tracker/SKILL.md) · [buglog](skills/buglog/SKILL.md) |
| Build | [api-patterns](skills/api-patterns/SKILL.md) · [data-patterns](skills/data-patterns/SKILL.md) · [state-management](skills/state-management/SKILL.md) · [real-time-websockets](skills/real-time-websockets/SKILL.md) · [code-transformation](skills/code-transformation/SKILL.md) · [file-storage](skills/file-storage/SKILL.md) · [search-indexing](skills/search-indexing/SKILL.md) · [feature-flags](skills/feature-flags/SKILL.md) · [internationalization-i18n](skills/internationalization-i18n/SKILL.md) |
| Quality | [testing-automation](skills/testing-automation/SKILL.md) · [security-scanning](skills/security-scanning/SKILL.md) · [accessibility-a11y](skills/accessibility-a11y/SKILL.md) · [design-qc](skills/design-qc/SKILL.md) · [performance-optimization](skills/performance-optimization/SKILL.md) · [error-recovery](skills/error-recovery/SKILL.md) |
| Delivery & ops | [cicd-automation](skills/cicd-automation/SKILL.md) · [auto-git-create](skills/auto-git-create/SKILL.md) · [monitoring-observability](skills/monitoring-observability/SKILL.md) · [automated-documentation](skills/automated-documentation/SKILL.md) · [clash-proxy](skills/clash-proxy/SKILL.md) |
| Tools & docs | [get-api-docs](skills/get-api-docs/SKILL.md) · [mcp-integration](skills/mcp-integration/SKILL.md) · [find-skills](skills/find-skills/SKILL.md) · [prompt-engineering](skills/prompt-engineering/SKILL.md) |

Full V4 integration matrix: [skills-matrix](references/skills-matrix.md).

## Reference Files

| File | Purpose |
|---|---|
| [references/v5-engine.md](references/v5-engine.md) | V5 engine reference — state machine, gate check types, hooks contract, task graph, loop guard, budget, evolver, evals, portability |
| [references/skill-v4-full.md](references/skill-v4-full.md) | Verbatim V4.1.16 SKILL.md (all prose doctrine, preserved) |
| [references/phases.md](references/phases.md) | Human-readable detail for every phase |
| [references/dev-constitution.md](references/dev-constitution.md) | 开发宪法 V2.1 — C0 + C1–C16 + R1–R12; companions [weaipo-constitution](references/weaipo-constitution.md) · [pai-station-doctrine](references/pai-station-doctrine.md) |
| [references/cc-command-playbook.md](references/cc-command-playbook.md) | CC 指挥手册 — 批准制模板 · ralph-loop 预算 · 无人值守三句式 |
| [references/best-practices-2026.md](references/best-practices-2026.md) | AI-assisted engineering patterns |
| [references/trending-standards.md](references/trending-standards.md) | 2026 ecosystem standards (LangGraph/AutoGen/CrewAI/MCP) |
| [references/ai-mastery.md](references/ai-mastery.md) | Boris Cherny's 7 disciplines |
| [references/audit-loop-case-study.md](references/audit-loop-case-study.md) | Run-log-driven audit loop (We-AIPO) |
| [references/mattpocock-skills.md](references/mattpocock-skills.md) | mattpocock/skills integration map |
| [references/renxin-ai-product-methodology.md](references/renxin-ai-product-methodology.md) | 任鑫 AI 产品方法论 — 三筛选品 · JTBD · 第一天变现 · 新能力十问 |
| [references/stitching-monster.md](references/stitching-monster.md) | 缝合怪工程教义 — 三缝合律 · 瓶颈优先 |
| [references/hundun-arsenal.md](references/hundun-arsenal.md) | 混沌武器库 — 六场景作战地图 · 13 技能卡 |
| [references/ai-native-coordination.md](references/ai-native-coordination.md) | AI 原生协调层 — 对齐/推进/闭环 · 检查四层 · FDE |
| [references/research-methodology.md](references/research-methodology.md) | 调研方法论双源 — 思维密集度 · 五本书梯度 · 报告五步 |
| [references/yitang-agent-forge.md](references/yitang-agent-forge.md) | 训虾派 · AI 角色配置工程 |
| [references/judgment-layer.md](references/judgment-layer.md) | 判断层 (Jev×TypeSafe) — Noul/Choice/Score |
| [references/ideaforge.md](references/ideaforge.md) | Idea Factory method + algorithms |
| [references/skills-matrix.md](references/skills-matrix.md) | Sub-skill integration mapping |
| [EVOLUTION.md](EVOLUTION.md) · [evolver/README.md](evolver/README.md) | GEP protocol + V5 evolver |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Version

**V5.1.2** - 2026-10-01 - nightly self-update moved to **22:00 Beijing time** (Task Scheduler trigger pinned to UTC+8, DST-proof, never fires on registration); an OS-held pipeline lock (released by the OS even if a run is killed) so the daily and weekly pipelines (both 22:00 on Sundays) never overlap; interrupted runs are recovered by stashing their provable leftovers; reverts never destroy human edits; read-only GitHub for the distill model; `api_push` refuses to overwrite unknown remote content. Existing installs: re-run `python automation/schedule_daily.py` once.

**V5.1.0** - 2026-10-01 - **每日自更新 (nightly self-update)**: 23:00 Beijing radar (GitHub search + watchlist releases + Hacker News) → headless distill into a staging area → whitelist apply (verifier untouchable) → full check suite or revert → commit → reinstall → push. See `automation/README.md`.

**V5.0.0** - 2026-09-30 - **从说明书到发动机 (prose → executable engine)**: 204-repo research (5 tracks) distilled into an executable core — `phases.json` contracts (17 phases, 17 check types) + `ss.py` state machine (init/next/gate/advance/goto/approve/wait/resume); 8 working hooks (the V4 settings schema never fired); PreToolUse guard (destructive/force-push/secrets/state-tamper/budget/playbook); Stop phase gate with anti-loop; EARS + REQ traceability; dependency task graph; `ss-planner/worker/judge/researcher/spec-reviewer` subagents with worktree isolation; circuit-breaker Ralph driver; cost/budget meter; ACE playbook + FTS5 memory + skill router; clean-room DGM/GEPA evolver; offline bench + plugin evals; portable installer/doctor; plugin + marketplace manifests; CI on 3 OSes. Fixed: 7 SKILL.md frontmatters that failed YAML parsing (including this one). Details: [CHANGELOG.md](CHANGELOG.md).

<!-- daily-self-update -->
**Latest daily self-update:** V5.1.4 — 2026-10-07 — 堵住第三方 skill 安装前审查的漏洞：可执行文件、编译产物、无法检查的压缩包和指向技能目录外的符号链接不再被静默判为 CLEAN；Judge 新增 Worker 没见过的额外检查（HOLDOUT），防止只针对自己的测试凑通过。 — [digest](references/radar/2026-10-07.md) · [all](references/radar/README.md)
<!-- /daily-self-update -->

**V4.1.16** - 2026-09-22 - 判断层 (Jev × TypeSafe) — see [skill-v4-full](references/skill-v4-full.md) for V3.21–V4.1.16 history.

---

*Super-Skill V5.1.4: executable Idea→Product Factory — phase contracts + state machine + working hooks (guard / stop gate / hand-off) + EARS traceability + task graph + Planner-Worker-Judge subagents + circuit-breaker Ralph loop + budgets + ACE playbook + FTS5 memory + DGM/GEPA evolver + offline bench & plugin evals + portable installer; all V4 doctrine preserved (开发宪法 V2.1 · 缝合怪 · 任鑫方法论 · 混沌武器库 · 协调层 · 调研方法论 · 训虾派 · 判断层)*
