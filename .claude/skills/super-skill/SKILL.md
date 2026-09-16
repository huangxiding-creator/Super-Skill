---
name: super-skill
description: V4.1 idea→product factory + AI-mastery-7 (Boris Cherny): raw idea → 10× proposal → approval gate → 14-phase autonomous dev. GEP self-evolution, hooks, 48 skills.
---

# Super-Skill V4.1: Idea→Product Factory

## Core Philosophy

**"Think First, Code Later"** - Maximize upfront thinking, minimize rework.

**Four Interaction Points** (V4.0): Idea → Hybrid Clarification (only if ambiguous) → **Proposal Approval Gate** → Plan approval. After the gate: Zero user interaction required.

**Variance Inequality**: When improvement stalls, strengthen the verifier, not the generator.

**复利原则 (Compounding, constitution C0)**: what separates teams is not how much AI does today, but whether today's corrections, judgments, and failures make tomorrow better — 把一次成功变成可重复的方法，把一次失败变成不会再犯的约束，把一次纠正变成所有人可复用的判断；最顶级模式 = 通过迭代循环实现螺旋上升.

**缝合怪原则 (Stitching-Monster, 任鑫《AI原生组织转型》)**: 单环节世界最优 ≠ 生产级产品——成败在**缝合处**：用世界最好零件 (C4) × **显式交接契约** (上游 DoD 产出+验收+实测 → 下游准入闸门；单位/格式/语义显式——火星气候轨道器死于隐式单位制) × **整机生产级跑通** (C10/C12)。瓶颈在协调不在任务：优化非瓶颈 = 零贡献 (阿姆达尔定律——"所有的贡献都会被瓶颈吃掉")；"理想的交接是没有交接"——同一中央对象自动传导 — [references/stitching-monster.md](references/stitching-monster.md)

**Index Not Dump**: MEMORY.md is a concise index. Never store code-state facts that can drift.

**开发宪法** (Development Constitution, V2.1): **C0 复利元则** (above) + C1–C16 — proposal targets the **hardest problem** with a **world-best** plan; research **stands on giants' shoulders**; ten× plan **approved before code** (C7); after approval **full autonomy, no skipped steps** (C8); **run-ledger beats documents** (C10); fixes ship **before→after deltas** (C11); **golden-standard verification** (C12); **no fabricated data** (C14); red lines **R1–R12** (proxy 用完即关, no silent failure, 账号安全, 只增不删, 日预算硬顶, 密钥外置…) are never crossed. Non-negotiable — [references/dev-constitution.md](references/dev-constitution.md); copy-paste templates: [references/cc-command-playbook.md](references/cc-command-playbook.md).

## 2026 AI-Assisted Engineering Standards

Super-Skill integrates best practices from industry leaders:

| Source | Author | Integration |
|--------|--------|-------------|
| [Autoresearch](https://github.com/karpathy/autoresearch) | Andrej Karpathy | Autonomous experiment loop |
| [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills) | LearnPrompt | Verification gates, memory pipeline, context compression |
| [PUA](https://github.com/tanweai/pua) | tanweai | High-agency V2: methodology router, anti-rationalization, iceberg rule |
| [LLM Coding Workflow 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e) | Addy Osmani | AI-assisted engineering patterns |
| [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Anthropic | Skill creation guidelines |
| [LangChain](https://github.com/langchain-ai/langchain) | 122K+ | Chain-based workflows |
| [AutoGen](https://github.com/microsoft/autogen) | 52K+ | Multi-agent conversations |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 24K+ | Graph-based orchestration |
| [CrewAI](https://github.com/crewAIInc/crewai) | 30K+ | Role-based task delegation |
| [Context Hub](https://github.com/andrewyng/context-hub) | Andrew Ng | Curated API docs |
| [MCP Protocol](https://github.com/modelcontextprotocol) | Official | Tool integration standard |
| [Anthropic Skills](https://github.com/anthropics/skills) | Official | Skill building guidelines |
| [OpenWolf](https://github.com/cytostack/openwolf) | cytostack | 6-hook lifecycle, anatomy indexing, cerebrum learning, token tracking, buglog, design QC |
| [AI-Mastery 7 Disciplines](skills/ai-mastery-7/SKILL.md) | Boris Cherny | 7 disciplines: plan-first, verifier>generator, KB onboarding, rationale mining, weekly retro, long-term memory |
| [We-AIPO (自媒永动机)](references/audit-loop-case-study.md) | case study | Run-log-driven audit loop: 5 reusable patterns from a 290-commit / 78-optimization / 11-of-11-unattended build |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock | Real-engineering flows: grilling, CONTEXT.md+ADR ubiquitous language, tracer-bullet tickets, human-only-step wizards, red-first diagnosis |

**See**: [references/trending-standards.md](references/trending-standards.md) for complete integration patterns.

## Autonomous Experiment Loop (karpathy/autoresearch)

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) (58K+ stars). Enables 24-hour unattended autonomous development.

### Core Principle: Human Programs the Process, AI Executes

```
┌─────────────────────────────────────────────────────────────┐
│  Human edits: SKILL.md / program.md (instructions)          │
│  AI modifies: implementation code                           │
│  Infrastructure: tests, CI/CD, lint (read-only ground truth)│
└─────────────────────────────────────────────────────────────┘
```

### The Infinite Loop (runs until human interrupts)

```
1. READ    → Analyze current git state and codebase
2. MODIFY  → Implement experimental improvement
3. COMMIT  → Git commit with experiment description
4. TEST    → Run tests, capture output
5. EVALUATE → Parse results against acceptance criteria
6. DECIDE  → KEEP (improved) or DISCARD (worse/equal)
7. LOG     → Record to experiments.tsv
8. NEXT    → Advance to next experiment idea
```

### Decision Rules

| Outcome | Action | Criteria |
|---------|--------|----------|
| **KEEP** | Advance branch | Tests pass + metric improved + complexity justified |
| **DISCARD** | `git reset` | Tests fail OR metric regressed OR unnecessary complexity |
| **CRASH** | Fix or skip | Timeout/OOM/NaN → log error → next idea |

### Simplicity Criterion

Small improvement + ugly complexity = NOT worth it · small gain from **deleting code** = keep · equal perf + simpler = keep · ~0 gain + much simpler = keep.

### NEVER STOP Protocol

Do not pause between experiments (the human may be asleep). Out of ideas → re-read code, combine approaches, search best practices.

### Budget Constraints

`TIME_BUDGET_PER_EXPERIMENT=300` · `MAX_EXPERIMENTS_PER_SESSION=100` · `AUTONOMOUS_BRANCH_PREFIX="autoresearch"`.

**See**: [skills/autonomous-loop/SKILL.md](skills/autonomous-loop/SKILL.md) for full documentation.

## Context Engineering

Context engineering > prompt engineering. Ensure the agent sees the right information at the right time.

### Three Patterns
1. **Just-in-Time Context**: Load data at runtime via tools (grep, Read), not pre-embedded RAG
2. **Progressive Disclosure**: SKILL.md < 500 lines, references loaded on demand, never nest deeper than 2 levels
3. **Compaction Survival**: CLAUDE.md documents accumulated learnings; every mistake becomes a rule

### Token Budget Discipline
- SKILL.md frontmatter: < 200 chars (loaded every session)
- SKILL.md body: < 500 lines (loaded on trigger)
- Reference files: loaded on demand only
- Each paragraph in SKILL.md must earn its tokens: "Does Claude really need this?"

## AI Mastery Protocol (V4.1) — the 7 disciplines that multiply AI output

Distilled from Boris Cherny (creator of Claude Code). Core thesis: **don't treat AI as a tool — it's an autonomous agent; give it context + tools, then let it run the whole workflow.** Most users extract <1% of their AI's capability. Super-Skill implements these 7 disciplines as named mechanisms so they're discoverable as one curriculum:

| # | Discipline | Mechanism |
|---|-----------|-----------|
| 1 | Let AI teach you how to use itself | `ai-mastery-7` onboarding dialog → persist boundary to CLAUDE.md |
| 2 | Domain onboarding via KB Q&A | Phase 3 `KNOWLEDGE_BASE/` + `continuous-learning-v2` |
| 3 | Understand history → understand "why" | `ai-mastery-7` **`rationale_mining.py`** (new) |
| 4 | Weekly retrospective from work logs | `ai-mastery-7` **`weekly_retrospective.py`** (new) |
| 5 | Plan before code | Phase 4 approval gate + `brainstorming` |
| 6 | Feedback tools → self-iteration | `verification-gate` + Phase 10 Ralph Loop — **verifier > generator** |
| 7 | Long-term memory / CLAUDE.md | `memory-pipeline` + `cerebrum` + MEMORY.md (keep CLAUDE.md short!) |

**Invoke** `ai-mastery-7` when the user asks how to use Super-Skill well, wants a weekly retrospective, asks "why does this code exist", or is about to say "just build X" (enforce D5).

> Full mapping + deeper protocols (onboarding dialog, plan-first guardrail, feedback-loop harness, anti-patterns): [references/ai-mastery.md](references/ai-mastery.md)

## Idea Factory (V4.0 front-end) — from a raw idea to a 10× proposal

When the user gives an **undeveloped idea** (text/attachment/transcript) instead of a spec, run the Idea Factory *before* Phase 0. Purely additive — clear specs still skip straight to Phase 0.

```
raw idea → [1] idea-intake → [2] research-orchestrator → [3] proposal-forge → ✋ Approval Gate → Phase 0
```

1. **[idea-intake](skills/idea-intake/SKILL.md)** — ambiguity-score; **Hybrid Clarification Gate** (autonomous unless score 4–7, then ≤3 Qs once) → `IDEA_SEED.md`
2. **[research-orchestrator](skills/research-orchestrator/SKILL.md)** — 9 channels (GitHub/Sogou WeChat/HN/npm/PyPI/App Store/Reddit/ProductHunt/competitor-site) + gap analysis + dedup + quality gate + checkpoint. Ports ResearchFactory-Eng architecture. → `RESEARCH_DOCKET/`, `RESEARCH_DIGEST.md`, `GAP_REPORT.md`; 检索后怎么读怎么判怎么写（思维密集度选源 / 五本书梯度 / 报告五步）— [research-methodology](references/research-methodology.md)
3. **[proposal-forge](skills/proposal-forge/SKILL.md)** — maturity index + **ten× delta index** (falsifiable 10× gate) + **任鑫选品五法** (三圈交集 + 离钱近·有套路·不严谨三筛 + 第一天变现 + **新能力→产品十问** — [renxin-ai-product-methodology](references/renxin-ai-product-methodology.md)) + blue/red-ocean + data-driven pricing (per-seat / per-value / **per-outcome** — 服务预算 6× 软件预算、"模型越强你越便宜") → 4-dim scorecard → `PROPOSAL.md`, `BUSINESS_MODEL.md`, `SCORECARD.json`; 全生命周期武器组合见 [hundun-arsenal](references/hundun-arsenal.md) 六场景地图 (场景一/二在此阶段)；Build-vs-Wait 判据 "下一代模型更强，会让我更值钱还是更没用？" — [ai-native-coordination](references/ai-native-coordination.md)

**Proposal Approval Gate** ✋: scorecard verdict = `proceed` → present proposal, ask approve/revise/reject **once** → on approve, auto-populate VISION/REQUIREMENTS/ARCHITECTURE and continue to Phase 0. Only new human touchpoint.

> Method + algorithms: [references/ideaforge.md](references/ideaforge.md)

## 14-Phase Workflow

### Phase 0: Visionary Elevation
Transform requirements into AI-native vision — constitution **C2**: boldness is legal, the proposal must not be pre-shrunk (C1 hardest problem · C3 world-best-and-landable). Output: `VISION.md`, `AI_NATIVE_OPTIONS.md`
- **See**: [darwin-evolution/SKILL.md](skills/darwin-evolution/SKILL.md) for GEP Protocol

### Phase 1: Feasibility Analysis
Evaluate technical, economic, operational, and scheduling feasibility.
- CC-FPS scoring framework (≥0.7 to proceed)
- **任鑫三筛** (AI 产品类项目): 离钱近 · 有套路 · 不严谨 + 第一天变现闭环 — [references/renxin-ai-product-methodology.md](references/renxin-ai-product-methodology.md)
- Output: `FEASIBILITY_REPORT.md`, `RISK_REGISTER.md`
- **Skill**: `feasibility-check`

### Phase 2: GitHub Discovery
Find existing open-source solutions before building.
- Score ≥80%: Clone and adapt — constitution **C4** 站在巨人肩膀上 (from-scratch requires a documented miss) — **缝合怪律一**: 零件必须各自世界级，缝合怪≠拼凑怪
- Score <60%: Build from scratch
- Output: `GITHUB_DISCOVERY_REPORT.md`
- **Skill**: `github-discovery`
- **Note (V4.0)**: if Idea Factory's research-orchestrator already ran its `github` channel, this phase is **subsumed** — reuse `RESEARCH_DOCKET/github/_all.json` instead of re-searching.
- **See**: [references/phases.md](references/phases.md) for decision matrix

### Phase 2b: Skills Discovery
Automatically discover and install skills from ecosystem.
- Auto-install skills with ≥80% relevance
- **Skill**: `find-skills`
- **See**: [skills/find-skills/SKILL.md](skills/find-skills/SKILL.md)

### Phase 3: Knowledge Base
Build comprehensive domain knowledge.
- Domain, technical, and context knowledge; **修路** (coordination doctrine): 业务过程留痕 ("没有被记录的业务对 AI 来说不存在") + 本体 **5 分钟版** (MD 口喷、缺什么补什么) — [ai-native-coordination](references/ai-native-coordination.md)
- Output: `KNOWLEDGE_BASE/`, `SCHEMAS.md`, plus a `CONTEXT.md` **ubiquitous-language glossary** (terms + banned synonyms; lint via `context_lint.py`)
- **Skill**: `continuous-learning-v2`

### Phase 4: Requirements Engineering
Define detailed, actionable requirements.
- Functional + Non-functional + Acceptance Criteria
- **JTBD 用户任务三步法**: 功能/情感/场景任务——交付"执行方法论的机器人"而非方法论 · **新能力转化透镜** (纸笔残留审计 / 锤子找钉子 / 版权两问) — [references/renxin-ai-product-methodology.md](references/renxin-ai-product-methodology.md)
- Output: `REQUIREMENTS.md`
- **Skill**: `brainstorming`; deep path = **grilling** (design-tree interview; quick path = Hybrid Clarification Gate) — [real-engineering](skills/real-engineering/SKILL.md)
- **Gate**: User approval required before proceeding

### Phase 5-5b: Architecture & Design
Design system architecture and components.
- Phase 5: System architecture, tech stack, service boundaries — constitution **C5**: the optimal solution under actual constraints, recorded as ADRs
- Phase 5b: Component design, API contracts, database schemas
- Output: `ARCHITECTURE.md`, `API_DESIGN.md`
- **Skills**: `api-patterns`, `data-patterns`, `security-scanning`
- **See**: [references/phases.md](references/phases.md) for detailed design process

### Phase 6: WBS
Break project into executable tasks.
- Epic → Story → Task hierarchy; prefer **tracer-bullet vertical slices with blocking edges**; wide refactors → expand–contract ([real-engineering](skills/real-engineering/SKILL.md))
- Output: `WBS.md`, `TASK_BACKLOG.md`
- **See**: [references/phases.md](references/phases.md) for WBS structure

### Phase 7: Project Initialization
Set up project infrastructure.
- Directory structure, package manager, linting, testing, git, CI/CD
- **Skills**: `auto-git-create`, `cicd-automation`

### Phase 8: Autonomous Development
Execute development with zero user interaction using hierarchical orchestration.

**Hierarchical Orchestration** (Planner-Worker-Judge pattern):
- **Planner** (Phase 6/7 output): Continuously explores codebase, creates tasks, assigns priorities
- **Worker** (Autonomous Loop): Executes assigned tasks in isolated git worktrees
- **Judge** (Phase 9/10): Evaluates results, decides keep/discard, triggers rollback

```
Planner → assigns task → Worker (worktree isolation)
                         ↓ modify → test → evaluate
Judge ← evaluates result ← Worker
  ↓ keep: merge to branch
  ↓ discard: git reset, next task
```

- **Autonomous Loop**: Modify → Test → Evaluate → Keep/Discard × N experiments; **检查四层**: 自动门禁 · 对抗性检查 (检查者与干活者上下文隔离——防 AI mock 数据骗过绿灯) · 人类抽检按带宽排 · 兜底回滚 — [ai-native-coordination](references/ai-native-coordination.md)
- **Agent 角色配置 (训虾派)**: 配置文档=角色能力上限——新 agent/subagent 用系统工程式批量配置上岗（口喷 10%→最佳实践底座补全 90%），不做碎片磨合；六维段位评估 + 有/无配置 A/B 验收 — [yitang-agent-forge](references/yitang-agent-forge.md)
- **Iceberg Rule**: Fix one bug → scan for pattern across codebase. One problem in, one category out
- **Anti-Rationalization**: Never accept "I can't" without evidence of exhausting all options
- TDD-first, small commits, continuous integration
- Git-as-experiment-tracker: branch advances only on improvements
- Simplicity criterion: prefer deleting code over adding complexity
- NEVER STOP protocol: continue until human interrupts
- **Freedom Level by Task**:
  - High freedom: Code reviews, refactoring (multiple valid approaches)
  - Medium freedom: Feature implementation (preferred pattern, acceptable variation)
  - Low freedom: Database migrations, deployments (exact scripts required)
- **Skills by Task**:
  - Testing: `testing-automation`
  - APIs: `api-patterns`
  - Database: `data-patterns`
  - Real-time: `real-time-websockets`
  - Debugging: `systematic-debugging`
- **See**: [references/skills-matrix.md](references/skills-matrix.md) for full skill mapping

### Phase 9: QA
Comprehensive quality assurance.
- Unit (≥80% coverage) + Integration + E2E tests
- Security scan, performance benchmarks, a11y compliance
- **Two-axis review** before commit: Standards (conventions + smell baseline) ∥ Spec (faithful to the issue) — [real-engineering](skills/real-engineering/SKILL.md)
- **Skills**: `testing-automation`, `security-scanning`, `accessibility-a11y`

### Phase 10: Ralph Loop
10-iteration optimization cycle.
- Analyze (**瓶颈优先** — 阿姆达尔定律: 每轮先定位最慢环节/最长等待，非瓶颈优化零贡献 — [stitching-monster](references/stitching-monster.md)) → Improve → Validate → Document → Check convergence
- **Run-log-driven audit + 三线复盘** (coordination doctrine): each round opens with a reconstructed run timeline + waste calc → root-cause → numbered fixes (S1-SN) → impl table; 每个问题跑三条线——解决当下 · 修系统让下次不再出现 · **回头验证** (改完指标回来没有？没涨=根因找错，闭"归因方式") — [references/audit-loop-case-study.md](references/audit-loop-case-study.md) · [ai-native-coordination](references/ai-native-coordination.md)
- **See**: [references/phases.md](references/phases.md) for convergence criteria

### Phase 11: Deployment
Deploy to production.
- Pre-deployment checklist, environment config, migrations, monitoring
- **Wizard**: for human-only steps (credentials, dashboards, CI secrets) generate an interactive bash script from `wizard_template.sh` — [real-engineering](skills/real-engineering/SKILL.md)
- **Skills**: `cicd-automation`, `monitoring-observability`

### Phase 12: Evolution
Capture learnings and evolve Super-Skill.
- Post-Run Review → Signal Extraction → Evolution Decision → Mutation → Capsule Packaging — **C0**: 一次成功→可重复方法 · 一次失败→不会再犯的约束 · 一次纠正→可复用判断 (spiral ascent)
- **Skills**: `post-run-evolution`, `darwin-evolution`, `capability-evolver`
- **See**: [skills/post-run-evolution/SKILL.md](skills/post-run-evolution/SKILL.md) for post-run evolution · [EVOLUTION.md](EVOLUTION.md) for GEP Protocol details

## Skill Integration Matrix

Super-Skill integrates 48 specialized skills. See [references/skills-matrix.md](references/skills-matrix.md) for complete mapping.

### Core Skills (Always Available)
| Skill | Purpose |
|-------|---------|
| `verification-gate` | Read-only challenge pass (cc-harness-skills) |
| `memory-pipeline` | Extract + consolidate memories (cc-harness-skills) |
| `context-compressor` | 9-part session handoff (cc-harness-skills) |
| `autonomous-loop` | Infinite experiment loop (karpathy/autoresearch) |
| `pre-run-upgrade` | Sub-skill upgrade + best practices search |
| `post-run-evolution` | Review + self-evolution after completion |
| `darwin-evolution` | GEP Protocol self-evolution |
| `multi-agent-orchestration` | LangGraph/AutoGen/CrewAI |
| `advanced-reasoning` | CoT/ToT/GoT reasoning |
| `brainstorming` | Systematic exploration |
| `systematic-debugging` | 4-phase debugging |
| `get-api-docs` | Context Hub curated docs |
| `high-agency` | Iron rules + methodology router + anti-rationalization (PUA V2) |
| `ai-mastery-7` | 7 AI-mastery disciplines: plan-first, KB onboarding, rationale mining, weekly retrospective, verifier>generator (Boris Cherny) |
| `cognitive-modes` | 6 development perspectives (gstack) |
| `anatomy-scanner` | Project file indexing with token estimates (OpenWolf) |
| `cerebrum` | Cross-session learning with Do-Not-Repeat (OpenWolf) |
| `token-tracker` | Session token tracking + waste detection (OpenWolf) |
| `buglog` | Auto bug detection + Jaccard similarity matching (OpenWolf) |
| `design-qc` | Visual regression with sectioned screenshots (OpenWolf) |

### Phase-Specific Skills
- **Phase 5-8**: `api-patterns`, `data-patterns`, `state-management`, `real-time-websockets`
- **Phase 7-11**: `cicd-automation`, `auto-git-create`, `monitoring-observability`
- **Phase 8-9**: `testing-automation`, `security-scanning`, `accessibility-a11y`
- **Phase 12**: `darwin-evolution`, `capability-evolver`

## Hooks System (6-Lifecycle Architecture)

Automatic execution via Claude Code hooks. Inspired by [OpenWolf](https://github.com/cytostack/openwolf) 6-hook lifecycle pattern.

### Hooks Configuration

| Hook | Trigger | Action | Source |
|------|---------|--------|--------|
| **Notification** | Session start | Pre-Run Upgrade + Anatomy refresh + Cerebrum freshness | Super-Skill |
| **PreToolUse** | Before Read/Write | Repeated-read blocking, Do-Not-Repeat check, Buglog matching | OpenWolf |
| **PostToolUse** | After Read/Write | Token estimation, Anatomy update, Bug detection, Edit summaries | OpenWolf |
| **PostToolUse** | After Bash/Write | Logging and tracking | Super-Skill |
| **Stop** | Session end | Post-Run Evolution + Token waste report + Buglog summary | Super-Skill + OpenWolf |
| **SubagentStop** | Subagent completion | Agent activity logging | Super-Skill |

### Automatic Execution Flow

```
NOTIFICATION (session start: Pre-Run Upgrade + Anatomy Refresh + Cerebrum Freshness) → PRE-TOOL-USE (before Read/Write) → MAIN EXECUTION (14-Phase Workflow, Phase 0-12) → POST-TOOL-USE (after Read/Write) → STOP (session end: Post-Run Evolution + Token Report + Buglog Summary)
```

### Configuration File

Configured in `.claude/settings.json`. See the file for full hook definitions and env vars.

## Startup Sequence

```
STEP -1: Pre-Run Upgrade → Upgrade sub-skills + search best practices (HOOK)
STEP 0: Auto-Update → Self-update Super-Skill and all dependent skills
STEP 1: Version Check → python scripts/auto_update.py
STEP 2: Evolver Check → python scripts/check_evolver.py
STEP 3: Memory Start → npm run worker:start (claude-mem)
STEP 4: Retrieve Memories → Automatic context injection
STEP 5: Inject Context → Session context ready
```

### Pre-Run Upgrade (STEP -1)

Before each session (max capability readiness): version check → sub-skill upgrade (`npx skills`) → GitHub-trending best-practices search → pattern integration → Context Hub sync → evolution sync. Full detail: [skills/pre-run-upgrade/SKILL.md](skills/pre-run-upgrade/SKILL.md). Auto-update is configured via env vars in `.claude/settings.json`.

## Context Hub Integration

[Context Hub](https://github.com/andrewyng/context-hub) by Andrew Ng provides curated API docs.

### Phase Integration
| Phase | Usage |
|-------|-------|
| Phase 3 | Fetch library docs for knowledge base |
| Phase 5 | Get API patterns and architecture docs |
| Phase 8 | Quick reference during development |

**See**: [skills/get-api-docs/SKILL.md](skills/get-api-docs/SKILL.md) for full integration.

## Phase Transition Rules

| From | To | Gate Condition |
|------|-----|----------------|
| idea | intake | ambiguity score ≥ auto OR ≤3 clarification Qs answered |
| intake | research | `IDEA_SEED.md` emitted |
| research | proposal | quality gate passed (gap report notes weak dims) |
| proposal | 0 (Vision) | **Proposal Approval Gate — user approves** ✋ |
| 0 | 1 | Vision confirmed |
| 1 | 2 | Feasibility ≥0.7 |
| 2 | 3 | Build decision made |
| 3 | 4 | Knowledge base complete |
| 4 | 5 | **User approval** |
| 5 | 6 | Architecture approved |
| 6 | 7 | WBS complete |
| 7 | 8 | Infrastructure ready |
| 8 | 9 | Development complete |
| 9 | 10 | QA passed |
| 10 | 11 | Convergence achieved |
| 11 | 12 | Deployment successful |

**缝合契约 (Stitching Contract, 律二)**: 每个闸门必须显式写两半——上游 **DoD**（产出物+验收标准+实测数据）与下游**准入条件**；隐式假设 = 缝合缺陷（火星气候轨道器：双方各自完美，公制/英制未显式 → 坠毁）。更高形态："理想的交接是没有交接"——环节操作同一中央对象自动传导（福特传送带）。推进四件事（发现/分配/传导/检查工作）= 环节间调度/协同的工程化 — [references/stitching-monster.md](references/stitching-monster.md)

**Rollback**:
- Critical test failure → Phase 8
- Security vulnerability → Phase 5
- Performance failure → Phase 10

## GEP Protocol (Phase 12)

Super-Skill uses GEP Protocol from autogame-17/evolver for self-evolution.

### 5 GEP Objects
1. **Mutation** - Trigger for genetic modification
2. **PersonalityState** - Behavioral parameters (rigor, creativity, risk_tolerance)
3. **EvolutionEvent** - Record of evolution attempt
4. **Gene** - Atomic evolution unit (repair/optimize/innovate)
5. **Capsule** - Packaged successful evolution

### Evolution Triggers
1. Project completion (auto)
2. Critical learning event (auto)
3. User feedback (manual)
4. Periodic review (every 5 projects / 7 days)

### Asset Files
`assets/gep/` → `genes.json` (5 default genes) · `capsules.json` (success archive) · `events.jsonl` (evolution log).

**See**: [skills/darwin-evolution/SKILL.md](skills/darwin-evolution/SKILL.md) for full GEP Protocol documentation.

## Configuration

### Environment Variables
```bash
SUPER_SKILL_AUTO_UPDATE=true       # Auto-check updates
EVOLVE_STRATEGY=balanced           # balanced|innovate|harden|repair-only
EVOLVE_AUTO_APPLY=true             # Auto-apply improvements
GEP_PROMPT_MAX_CHARS=50000         # Max prompt size
```

### Strategy Presets
`balanced` (all Medium) · `innovative` (Low/Low/High) · `harden` (High/Med/Low) · `repair-only` (High/Low/None) — Repair/Optimize/Innovate columns; full table in [EVOLUTION.md](EVOLUTION.md).

## Reference Files

| File | Purpose |
|------|---------|
| [references/best-practices-2026.md](references/best-practices-2026.md) | AI-assisted engineering patterns (Addy Osmani, Anthropic) |
| [references/phases.md](references/phases.md) | Complete 14-phase workflow details |
| [references/skills-matrix.md](references/skills-matrix.md) | 27+ skills integration mapping |
| [references/trending-standards.md](references/trending-standards.md) | 2026 GitHub trending standards (LangChain/AutoGen/CrewAI/MCP) |
| [references/ai-mastery.md](references/ai-mastery.md) | AI-Mastery Protocol — Boris Cherny's 7 disciplines mapping + protocols |
| [references/audit-loop-case-study.md](references/audit-loop-case-study.md) | Run-log-driven audit loop — 5 reusable patterns + template, from We-AIPO |
| [references/mattpocock-skills.md](references/mattpocock-skills.md) | mattpocock/skills integration map — all 25 source skills → Super-Skill bindings |
| [references/dev-constitution.md](references/dev-constitution.md) | 开发宪法 V2.1 — **C0 复利元则** + articles C1–C16 + red lines R1–R12 + enforcement map + ~40-project evidence; companions: [weaipo-constitution](references/weaipo-constitution.md) (unattended-runtime 12+12) · [pai-station-doctrine](references/pai-station-doctrine.md) (value/methodology) |
| [references/cc-command-playbook.md](references/cc-command-playbook.md) | CC 指挥手册 — 六步元链 · 批准制模板 · ralph-loop 预算 · 无人值守三句式 · 节奏参数表 · 实测工具矩阵 |
| [references/renxin-ai-product-methodology.md](references/renxin-ai-product-methodology.md) | 任鑫 AI 产品方法论 — 三圈交集+三筛选品 · JTBD 三步法 · 第一天变现/按价值定价 · 老板模式人机分工（混沌 14 课蒸馏，应用层选品裁决）· 新能力→产品转化（十问扫描/纸笔残留/锤子找钉子/版权两问——第 100 课补给） |
| [references/stitching-monster.md](references/stitching-monster.md) | 缝合怪工程教义 — 三缝合律（世界最好零件 × 显式交接契约 × 整机生产级跑通）· 阿姆达尔瓶颈优先 · 推进四件事 · 缝合处=数据回流点（任鑫《AI原生组织转型》） |
| [references/hundun-arsenal.md](references/hundun-arsenal.md) | 混沌武器库 — 六场景作战地图（机会洞察/战略定位/MVP/技术底座/增长变现/组织协作，647 门课 3031 万字频次验证）· 使用心法三句话 · 13 技能卡（业务留档五步/GEO 四卡/组织五卡）· 外部语料挖掘流水线 |
| [references/ai-native-coordination.md](references/ai-native-coordination.md) | AI 原生协调层作战手册 — 对齐（N²→N 唯一事实源/纪要的终点是改掉那个对象/规范写进环境）· 推进四件事+检查四层 · 闭环三线复盘（"问题的终点是变成一条检查项"）· 落地三动作（修路/点火/分圈）· 12 槽位工程实证（Anthropic 80% 合并代码/Flox 50×/Town 三原则/beads 账本）· 反方边界（95% 试点零 P&L/J-Curve）· 投资人创业者视角（per-outcome 定价/套壳三问/8 wedge/FDE 交付范式）· 落地参谋检索纪律 |
| [references/research-methodology.md](references/research-methodology.md) | 调研方法论双源 — 万维钢桌研（思维密集度选源 · 五本书梯度 · 强力研读"读两遍只读两遍+笔记取代原书" · 调研式五步法"读书→采访专家→交叉点前沿→形成观点→费曼检验+专家审稿" · 想法立项+素材互链）× 何晓斌田野（六步程序 5W1H · 解剖麻雀/望远镜混合设计 · 访谈关系六原则 · 报告五步+用资料三原则"精准新"） |
| [references/yitang-agent-forge.md](references/yitang-agent-forge.md) | 训虾派·AI 角色配置工程 — 三流派诊断（做事/养虾/训虾——养=给唯一分身攒复利，训=批量复制新角色）· IPO+文档=能力上限 · 双三角（人守审美/体系/创造力）· 口喷输入法 10%→90% · 演戏法喂文档 · 六维段位评估+配置 A/B · 民主集中会议 |
| [EVOLUTION.md](EVOLUTION.md) | GEP Protocol documentation |
| [MEMORY.md](MEMORY.md) | Knowledge persistence |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Sub-Skills

48 specialized skills in `skills/` directory. Key sub-skills:

**Idea Factory (V4.0 front-end):**
- **[idea-intake](skills/idea-intake/SKILL.md)** - Ambiguity scoring + Hybrid Clarification Gate
- **[research-orchestrator](skills/research-orchestrator/SKILL.md)** - 9-channel research + gap analysis + dedup + quality gate
- **[proposal-forge](skills/proposal-forge/SKILL.md)** - Maturity/ten×/pricing/scorecard + Proposal Approval Gate

**AI Mastery (V4.1):**
- **[ai-mastery-7](skills/ai-mastery-7/SKILL.md)** - 7 disciplines (Boris Cherny): plan-first, KB onboarding, rationale mining, weekly retrospective, verifier>generator; ships `weekly_retrospective.py` + `rationale_mining.py`

**Real Engineering (V4.1.4):**
- **[real-engineering](skills/real-engineering/SKILL.md)** - Grilling + CONTEXT.md/ADR ubiquitous language + tracer-bullet tickets + wizard + red-first diagnosis (mattpocock/skills); ships `wizard_template.sh` + `context_lint.py`

- **[verification-gate](skills/verification-gate/SKILL.md)** - Read-only challenge pass (cc-harness-skills)
- **[memory-pipeline](skills/memory-pipeline/SKILL.md)** - Extract + consolidate memories (cc-harness-skills)
- **[context-compressor](skills/context-compressor/SKILL.md)** - 9-part session handoff (cc-harness-skills)
- **[autonomous-loop](skills/autonomous-loop/SKILL.md)** - Infinite experiment loop (karpathy/autoresearch)
- **[pre-run-upgrade](skills/pre-run-upgrade/SKILL.md)** - Sub-skill upgrade + best practices search
- **[post-run-evolution](skills/post-run-evolution/SKILL.md)** - Review + self-evolution after completion
- **[darwin-evolution](skills/darwin-evolution/SKILL.md)** - GEP Protocol engine
- **[multi-agent-orchestration](skills/multi-agent-orchestration/SKILL.md)** - Agent coordination
- **[advanced-reasoning](skills/advanced-reasoning/SKILL.md)** - CoT/ToT/GoT
- **[get-api-docs](skills/get-api-docs/SKILL.md)** - Context Hub curated docs
- **[high-agency](skills/high-agency/SKILL.md)** - Iron rules + pressure escalation (PUA methodology)
- **[cognitive-modes](skills/cognitive-modes/SKILL.md)** - 6 development perspectives (gstack)
- **[testing-automation](skills/testing-automation/SKILL.md)** - TDD/E2E/Mutation
- **[security-scanning](skills/security-scanning/SKILL.md)** - SAST/SCA/Secrets
- **[api-patterns](skills/api-patterns/SKILL.md)** - REST/GraphQL
- **[data-patterns](skills/data-patterns/SKILL.md)** - SQL/NoSQL
- **[anatomy-scanner](skills/anatomy-scanner/SKILL.md)** - Project file indexing with token estimates (OpenWolf)
- **[cerebrum](skills/cerebrum/SKILL.md)** - Cross-session learning with Do-Not-Repeat (OpenWolf)
- **[token-tracker](skills/token-tracker/SKILL.md)** - Session token tracking + waste detection (OpenWolf)
- **[buglog](skills/buglog/SKILL.md)** - Auto bug detection + similarity matching (OpenWolf)
- **[design-qc](skills/design-qc/SKILL.md)** - Visual regression with sectioned screenshots (OpenWolf)
- **[clash-proxy](skills/clash-proxy/SKILL.md)** - Clash proxy manager for GitHub/foreign-network ops: **Clash REST API layer** (mode switch, node pin, DNS-residue cleanup — We-AIPO provenance) + one-command `push` recipe (commit → proxy → push → direct-fallback → 用完即关)

## Quick Start

Say "Build me a task management app" → Super-Skill auto-runs Phase 0–12 with zero further interaction (worked example in `README.md`; per-phase outputs under "## 14-Phase Workflow" above).

## Version

**V4.1.15** - 2026-09-16 - **调研方法论双源 + 训虾派角色配置工程 + FDE 交付范式 (外部智慧自学习第六跑·周度 W38)**: 04 智库五渠道新材料 6 份（1 份采集失败 skip）。新建 [research-methodology](references/research-methodology.md)——万维钢桌研（**思维密集度**=准备时间÷阅读时间 · **五本书梯度**畅销→热门→专家→硬书→前沿 · **强力研读**读两遍只读两遍+笔记写到取代原书 · **调研式五步法**读书→采访专家"你的问题你负责"→前沿=交叉点→观点允许反转→费曼检验+专家审稿 · 想法立项+素材互链外部存储）× 何晓斌田野（**六步程序 5W1H** · 解剖麻雀/望远镜混合 · **访谈关系六原则** · **报告五步**立意-定题-思路-架子-资料+用资料三原则"精准新"）。新建 [yitang-agent-forge](references/yitang-agent-forge.md)——训虾派：**配置文档=角色能力上限**（做事/养虾/训虾三流派——养=给唯一分身攒复利，训=用养出的体系批量复制）· IPO 模型 · 双三角（人守审美/体系/创造力）· **口喷输入法** 10%→90%（前提最佳实践底座）· 演戏法喂文档 · 六维段位评估+六个训练触发器+有/无配置 A/B · 民主集中会议。[ai-native-coordination](references/ai-native-coordination.md) §七补 **FDE 前沿部署交付范式**（Palantir 首创：以客户系统实际运行为交付终点 · 不是人力外包是产品研发入口 · Echo+Delta 双团队回流 · AI 压低定制成本→规模化）。wired: Idea Factory 调研读判写 · Phase 8 Agent 角色配置 · reference 表 +2 行。

**V3.21.0–V4.1.14** - 2026-05/09 - OpenWolf (5 sub-skills + 6-hook lifecycle) → IdeaForge front-end (Approval Gate, ten× delta index) → AI-Mastery-7 → We-AIPO GEP Capsule → `clash-proxy` + `real-engineering` (47→48) → **开发宪法 V1→V2.1** ([dev-constitution](references/dev-constitution.md): **C0 复利元则** + C1–C16 + R1–R12 + enforcement map + ~40-project evidence; companions weaipo/pai + [cc-command-playbook](references/cc-command-playbook.md)) → **智库→Super-Skill 自学习一~五跑**: V4.1.10 任鑫产品方法论 ([renxin-ai-product-methodology](references/renxin-ai-product-methodology.md): 三圈交集+三筛/JTBD/第一天变现) · V4.1.11 缝合怪 ([stitching-monster](references/stitching-monster.md): 三缝合律/阿姆达尔瓶颈/推进四件事) · V4.1.12 混沌武器库 ([hundun-arsenal](references/hundun-arsenal.md): 六场景作战地图/13 技能卡, 647 课 3031 万字频次验证) · V4.1.13 AI 原生协调层手册 (对齐/推进/闭环 + 落地三动作 + 检查四层 + 三线复盘 + 12 槽位实证) · V4.1.14 任鑫第 100 课补蒸馏 (新能力→产品转化七条: 纸笔残留/锤子找钉子/十问扫描/视觉少样本/数字人交互/可汗式引导/版权两问)。Details: [CHANGELOG.md](CHANGELOG.md).

---

*Super-Skill V4.1.15: Idea→Product Factory — 开发宪法 V2.1 (C0 复利元则 + C1–C16 / R1–R12 + CC 指挥手册) + AI 原生协调层手册 (对齐/推进/闭环 + 三落地动作 + 检查四层 + 三线复盘 + FDE 交付范式) + 缝合怪工程教义 (三缝合律/瓶颈优先) + 任鑫 AI 产品方法论 (三筛选品/JTBD/第一天变现/新能力十问) + 混沌武器库 (六场景作战地图/13 技能卡) + 调研方法论双源 (思维密集度/五本书梯度/报告五步) + 训虾派角色配置工程 (文档=上限/口喷输入法/段位评估) + AI-Mastery + Self-Consistency + We-AIPO Capsule + clash-proxy (API push) + real-engineering*
