---
name: super-skill
description: AI-Native 14-phase development orchestrator with GEP Protocol self-evolution. TRIGGER when users request full-stack development, complex products, systematic execution, or comprehensive project delivery. Capabilities: (1) Visionary requirement elevation (Phase 0), (2) Autonomous 14-phase lifecycle, (3) GEP Protocol self-evolution, (4) Multi-agent orchestration (LangGraph/AutoGen/CrewAI), (5) MCP Protocol integration, (6) Context Hub curated docs, (7) Pre-run upgrade and best practices search, (8) Post-run review and self-evolution, (9) 6 cognitive modes (gstack), (10) High-agency execution methodology, (11) AI-assisted engineering patterns (Addy Osmani 2026), (12) 32+ integrated skills. Core workflow: Pre-Run Upgrade → Vision → Feasibility → GitHub Discovery → Skills Discovery → Knowledge Base → Requirements → Design → WBS → Development → QA → Ralph Loop → Deployment → Post-Run Evolution. Integrates 2026 GitHub trending standards from LangChain (122K★), AutoGen (52K★), CrewAI (30K★), MCP Protocol, Context Hub (Andrew Ng), gstack (Garry Tan/YC), and Anthropic Skills best practices.
---

# Super-Skill V3.13: AI-Native Development Orchestrator

## Core Philosophy

**"Think First, Code Later"** - Maximize upfront thinking, minimize rework.

**Three Interaction Points**: Initial input → Requirement confirmation → Plan approval. After Phase 4: Zero user interaction required.

## 2026 AI-Assisted Engineering Standards

Super-Skill V3.13 integrates best practices from industry leaders:

| Source | Author | Integration |
|--------|--------|-------------|
| [LLM Coding Workflow 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e) | Addy Osmani | AI-assisted engineering patterns |
| [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Anthropic | Skill creation guidelines |
| [LangChain](https://github.com/langchain-ai/langchain) | 122K+ | Chain-based workflows |
| [AutoGen](https://github.com/microsoft/autogen) | 52K+ | Multi-agent conversations |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 24K+ | Graph-based orchestration |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 30K+ | Role-based task delegation |
| [Context Hub](https://github.com/andrewyng/context-hub) | Andrew Ng | Curated API docs |
| [MCP Protocol](https://github.com/modelcontextprotocol) | Official | Tool integration standard |
| [Anthropic Skills](https://github.com/anthropics/skills) | Official | Skill building guidelines |

**See**: [references/trending-standards.md](references/trending-standards.md) for complete integration patterns.

## 14-Phase Workflow

### Phase 0: Visionary Elevation
Transform requirements into AI-native vision through breakthrough thinking.
- 7-step visionary process
- Two-dimensional output (AI-Enhanced vs AI-Native)
- Output: `VISION.md`, `AI_NATIVE_OPTIONS.md`
- **See**: [darwin-evolution/SKILL.md](skills/darwin-evolution/SKILL.md) for GEP Protocol

### Phase 1: Feasibility Analysis
Evaluate technical, economic, operational, and scheduling feasibility.
- CC-FPS scoring framework (≥0.7 to proceed)
- Output: `FEASIBILITY_REPORT.md`, `RISK_REGISTER.md`
- **Skill**: `feasibility-check`

### Phase 2: GitHub Discovery
Find existing open-source solutions before building.
- Score ≥80%: Clone and adapt
- Score <60%: Build from scratch
- Output: `GITHUB_DISCOVERY_REPORT.md`
- **Skill**: `github-discovery`
- **See**: [references/phases.md](references/phases.md) for decision matrix

### Phase 2b: Skills Discovery
Automatically discover and install skills from ecosystem.
- Auto-install skills with ≥80% relevance
- **Skill**: `find-skills`
- **See**: [skills/find-skills/SKILL.md](skills/find-skills/SKILL.md)

### Phase 3: Knowledge Base
Build comprehensive domain knowledge.
- Domain, technical, and context knowledge
- Output: `KNOWLEDGE_BASE/`, `SCHEMAS.md`
- **Skill**: `continuous-learning-v2`

### Phase 4: Requirements Engineering
Define detailed, actionable requirements.
- Functional + Non-functional + Acceptance Criteria
- Output: `REQUIREMENTS.md`
- **Skill**: `brainstorming`
- **Gate**: User approval required before proceeding

### Phase 5-5b: Architecture & Design
Design system architecture and components.
- Phase 5: System architecture, tech stack, service boundaries
- Phase 5b: Component design, API contracts, database schemas
- Output: `ARCHITECTURE.md`, `API_DESIGN.md`
- **Skills**: `api-patterns`, `data-patterns`, `security-scanning`
- **See**: [references/phases.md](references/phases.md) for detailed design process

### Phase 6: WBS
Break project into executable tasks.
- Epic → Story → Task hierarchy
- Output: `WBS.md`, `TASK_BACKLOG.md`
- **See**: [references/phases.md](references/phases.md) for WBS structure

### Phase 7: Project Initialization
Set up project infrastructure.
- Directory structure, package manager, linting, testing, git, CI/CD
- **Skills**: `auto-git-create`, `cicd-automation`

### Phase 8: Autonomous Development
Execute development with zero user interaction.
- TDD-first, small commits, continuous integration
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
- **Skills**: `testing-automation`, `security-scanning`, `accessibility-a11y`

### Phase 10: Ralph Loop
10-iteration optimization cycle.
- Analyze → Improve → Validate → Document → Check convergence
- **See**: [references/phases.md](references/phases.md) for convergence criteria

### Phase 11: Deployment
Deploy to production.
- Pre-deployment checklist, environment config, migrations, monitoring
- **Skills**: `cicd-automation`, `monitoring-observability`

### Phase 12: Evolution
Capture learnings and evolve Super-Skill.
- Post-Run Review → Signal Extraction → Evolution Decision → Mutation → Capsule Packaging
- **Skills**: `post-run-evolution`, `darwin-evolution`, `capability-evolver`
- **See**: [skills/post-run-evolution/SKILL.md](skills/post-run-evolution/SKILL.md) for post-run evolution
- **See**: [EVOLUTION.md](EVOLUTION.md) for GEP Protocol details

## Skill Integration Matrix

Super-Skill integrates 32+ specialized skills. See [references/skills-matrix.md](references/skills-matrix.md) for complete mapping.

### Core Skills (Always Available)
| Skill | Purpose |
|-------|---------|
| `pre-run-upgrade` | Sub-skill upgrade + best practices search |
| `post-run-evolution` | Review + self-evolution after completion |
| `darwin-evolution` | GEP Protocol self-evolution |
| `multi-agent-orchestration` | LangGraph/AutoGen/CrewAI |
| `advanced-reasoning` | CoT/ToT/GoT reasoning |
| `brainstorming` | Systematic exploration |
| `systematic-debugging` | 4-phase debugging |
| `get-api-docs` | Context Hub curated docs |
| `high-agency` | Iron rules + pressure escalation |
| `cognitive-modes` | 6 development perspectives (gstack) |

### Phase-Specific Skills
- **Phase 5-8**: `api-patterns`, `data-patterns`, `state-management`, `real-time-websockets`
- **Phase 7-11**: `cicd-automation`, `auto-git-create`, `monitoring-observability`
- **Phase 8-9**: `testing-automation`, `security-scanning`, `accessibility-a11y`
- **Phase 12**: `darwin-evolution`, `capability-evolver`

## Startup Sequence

```
STEP -1: Pre-Run Upgrade → Upgrade sub-skills + search best practices
STEP 0: Auto-Update → Self-update Super-Skill and all dependent skills
STEP 1: Version Check → python scripts/auto_update.py
STEP 2: Evolver Check → python scripts/check_evolver.py
STEP 3: Memory Start → npm run worker:start (claude-mem)
STEP 4: Retrieve Memories → Automatic context injection
STEP 5: Inject Context → Session context ready
```

### Pre-Run Upgrade (STEP -1)

Executes before each session to ensure maximum capability readiness:

```bash
# Pre-run upgrade sequence
1. Version Check → Check all sub-skills for updates
2. Sub-Skill Upgrade → Upgrade outdated skills via npx skills
3. Best Practices Search → Search GitHub trending for new patterns
4. Pattern Integration → Integrate discovered best practices
5. Context Hub Sync → Update Context Hub registry
6. Evolution Sync → Sync learnings from previous sessions
```

**See**: [skills/pre-run-upgrade/SKILL.md](skills/pre-run-upgrade/SKILL.md) for full documentation.

### Auto-Update Mechanism (V3.10)

Super-Skill automatically updates before each development session:

```bash
# Auto-update sequence
1. Check Super-Skill version from GitHub
2. If update available → Pull latest changes
3. Check all dependent skills for updates
4. Update skills with: npx skills update <skill-name>
5. Refresh Context Hub registry: chub update
6. Log update status to ~/.claude/logs/super-skill-updates.log
```

**Configuration**:
```bash
SUPER_SKILL_AUTO_UPDATE=true       # Enable auto-update (default: true)
SUPER_SKILL_UPDATE_CHECK=true      # Check for updates (default: true)
SUPER_SKILL_SKILLS_UPDATE=true     # Update dependent skills (default: true)
CHUB_AUTO_UPDATE=true              # Update Context Hub registry (default: true)
```

## Context Hub Integration

[Context Hub](https://github.com/andrewyng/context-hub) by Andrew Ng provides curated, versioned API documentation.

### Quick Commands
```bash
chub search "react hooks"          # Search for docs
chub get <doc-id> --lang ts        # Fetch with language preference
chub annotate <doc-id> "note"      # Add persistent local notes
chub feedback <doc-id> up|down     # Rate doc quality
chub update                        # Refresh cached registry
```

### Phase Integration
| Phase | Context Hub Usage |
|-------|-------------------|
| Phase 3 | Fetch library docs for knowledge base |
| Phase 5 | Get API patterns and architecture docs |
| Phase 8 | Quick reference during development |

### Self-Improving Loop
```
Search → Get → Apply → Annotate → Feedback
         ↑_________________________|
         Annotations persist across sessions
```

**See**: [skills/get-api-docs/SKILL.md](skills/get-api-docs/SKILL.md) for full Context Hub integration.

## Phase Transition Rules

| From | To | Gate Condition |
|------|-----|----------------|
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
```
assets/gep/
├── genes.json      # 5 default genes
├── capsules.json   # Success archive
└── events.jsonl    # Evolution log
```

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
| Strategy | Repair | Optimize | Innovate |
|----------|--------|----------|----------|
| balanced | Medium | Medium | Medium |
| innovate | Low | Low | High |
| harden | High | Medium | Low |
| repair-only | High | Low | None |

## Reference Files

| File | Purpose |
|------|---------|
| [references/best-practices-2026.md](references/best-practices-2026.md) | AI-assisted engineering patterns (Addy Osmani, Anthropic) |
| [references/phases.md](references/phases.md) | Complete 14-phase workflow details |
| [references/skills-matrix.md](references/skills-matrix.md) | 27+ skills integration mapping |
| [references/trending-standards.md](references/trending-standards.md) | 2026 GitHub trending standards (LangChain/AutoGen/CrewAI/MCP) |
| [EVOLUTION.md](EVOLUTION.md) | GEP Protocol documentation |
| [MEMORY.md](MEMORY.md) | Knowledge persistence |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Sub-Skills

32 specialized skills in `skills/` directory. Key sub-skills:

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

## Quick Start

```
User: "Build me a task management app"

Phase 0: Vision → AI-native task app with voice-first interface
Phase 1: Feasibility → Score 0.85, proceed
Phase 2: GitHub → Found Todoist clone (65%), build from scratch
Phase 2b: Skills → Install real-time-websockets, search-indexing
Phase 3: Knowledge → Task domain, calendar integrations
Phase 4: Requirements → User approves
Phase 5: Architecture → React + Node + PostgreSQL
Phase 6: WBS → 3 epics, 12 stories
Phase 7: Init → Project structure, CI/CD
Phase 8: Development → Autonomous implementation
Phase 9: QA → 85% coverage, security clean
Phase 10: Ralph Loop → 10 iterations optimization
Phase 11: Deploy → Production deployment
Phase 12: Evolution → Learn and improve
```

## Version

**V3.13.0** - 2026-03-19
- **AI-Assisted Engineering Best Practices** (from Addy Osmani 2026):
  - 10 core principles for LLM coding workflow
  - "Waterfall in 15 minutes" planning pattern
  - Context packing checklist
  - Iterative chunks pattern
  - Human-in-the-loop verification
  - Version control as safety net
  - Customization with rules and examples
  - Automation as force multiplier
- **Anthropic Skill Authoring Best Practices**:
  - Concise is key principle
  - Degrees of freedom matching
  - Progressive disclosure patterns
  - Validation loops
  - Evaluation-driven development
- **New Reference Files**:
  - `references/best-practices-2026.md` - Comprehensive best practices
  - Updated `references/trending-standards.md` - Latest 2026 standards
- Total: 32 integrated skills

**V3.12.0** - 2026-03-14
- **Pre-Run Upgrade System**:
  - Sub-skill version checking and auto-upgrade
  - GitHub trending best practices search
  - Pattern integration workflow
  - Context Hub registry sync
  - Evolution learnings sync from previous sessions
  - New sub-skill: `pre-run-upgrade`
- **Post-Run Evolution System**:
  - 7-step evolution sequence after project completion
  - Signal extraction (defensive, opportunity, stagnation)
  - Quality dimension scoring
  - Mutation build and apply with safety constraints
  - Capsule packaging of successful patterns
  - Cross-session learning sync
  - New sub-skill: `post-run-evolution`
- Total: 32 integrated skills

**V3.11.0** - 2026-03-14
- **High-Agency Methodology** (from pua/tanweai):
  - Three Iron Rules: Exhaust options, Act before asking, Take initiative
  - Four-level pressure escalation (L1-L4)
  - Five-step debugging: Smell → Elevate → Mirror → Execute → Retrospective
  - Proactivity Matrix (3.25-4.0 scale)
  - Recovery Protocol and Quality Compass
  - Benchmark: +36% fix count, +65% verification, +50% tool calls
- **Cognitive Modes** (from gstack/Garry Tan/YC):
  - CEO Mode: 10-star product vision
  - Eng Manager Mode: Architecture, edge cases
  - Paranoid Reviewer Mode: Production bug hunting
  - Release Engineer Mode: Deploy automation
  - QA Engineer Mode: Browser automation (Playwright)
  - Engineering Manager Mode: Retrospectives
- New sub-skills: `high-agency`, `cognitive-modes`
- Total: 30 integrated skills

**V3.10.0** - 2026-03-14
- **Context Hub Integration** (Andrew Ng):
  - Curated, versioned API documentation
  - `chub search/get/annotate/feedback` workflow
  - Self-improving documentation loop
  - New sub-skill: `get-api-docs`
- **Auto-Update Mechanism**:
  - Self-update before each development session
  - Automatic dependent skills updates
  - Context Hub registry refresh
  - Update logging and configuration
- Total: 28 integrated skills

**V3.9.0** - 2026-03-14
- **GitHub Trending Standards Integration**:
  - LangChain (122K★) chain-based workflow patterns
  - AutoGen (52K★) multi-agent conversation patterns
  - LangGraph (24K★) graph-based orchestration
  - CrewAI (30K★) role-based task delegation
  - MCP Protocol 2026 Roadmap integration
  - Anthropic Skills best practices (15-30 min build)
- New reference file: `references/trending-standards.md`
- Enhanced multi-agent orchestration with production patterns
- MCP tool discovery and invocation patterns
- OpenTelemetry observability integration

**V3.8.1** - 2026-03-11
- skill-creator best practices refactor (82% token reduction)
- Progressive disclosure pattern implementation
- SKILL.md reduced from 2000+ to 256 lines

**V3.8.0** - 2026-03-03
- GEP Protocol integration from autogame-17/evolver
- Enhanced darwin-evolution skill V2.0
- 5 default genes, signal extraction, personality evolution

---

*Super-Skill V3.13: AI-Native Development Orchestrator with AI-Assisted Engineering Best Practices*
