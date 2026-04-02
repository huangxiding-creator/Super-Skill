# Changelog

All notable changes to Super-Skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.19.0] - 2026-04-02

### Added - cc-harness-skills Integration (from LearnPrompt/cc-harness-skills)

Integrated 3 core skills and 6 key patterns from [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills).

#### New Sub-Skills

##### verification-gate
Read-only challenge pass after implementation. Distinguishes "verified" from merely "claimed done."
- Three-state verdict: VERIFIED / UNVERIFIED / FAILED
- Checks: does change match request? did validation actually run? any regressions?
- Rules: read-only by default, findings before summary, never overstate
- Integration: wire as post-implementation gate before marking tasks complete

##### memory-pipeline
Dual-phase memory system combining dream-memory + memory-extractor from cc-harness-skills.
- Phase A (Extract): 4 typed categories — user, feedback, project, reference
- Phase B (Consolidate): dedup, prune stale entries, reindex MEMORY.md
- Rules: MEMORY.md is an INDEX (never content dump, cap 200 lines / 25KB)
- Rules: never store code-state facts that can drift (file paths, function names)
- Rules: organize by topic not chronology, update existing before creating new

##### context-compressor
9-part structured continuation summary for long sessions and handoffs.
- Sections: Request → Concepts → Files → Errors → Problem Solving → User Messages → Pending → Current → Next Step
- Critical rule: preserve ALL user messages — corrections changed direction of work
- Integration: use before agent-to-agent handoffs, context window pressure, session pause/resume

#### Key Patterns Adopted

| Pattern | Source Skill | Application |
|---------|-------------|-------------|
| **Index Not Dump** | dream-memory | MEMORY.md stays concise index, never content dump |
| **Durable vs Ephemeral** | memory-extractor | Never store code-state facts that can drift |
| **Three-State Verdict** | verification-gate | verified/unverified/failed, not just pass/fail |
| **Research-Synthesis-Implementation-Verification** | swarm-coordinator | 4-phase pipeline prevents premature implementation |
| **9-Part Handoff** | context-compressor | Structured session continuation artifact |
| **Proactive with Expiry** | kairos-lite | Background tasks expire after 7 days default |

#### Added to Core Philosophy
- **Index Not Dump**: MEMORY.md is a concise index. Never store code-state facts that can drift.

### Changed
- Core Skills table: 11 → 14 entries (added verification-gate, memory-pipeline, context-compressor)
- Total skills count: 33 → 36
- Standards table: added cc-harness-skills (LearnPrompt)
- Frontmatter description updated with new capabilities
- Updated header to V3.19

### Research Sources
- [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills) - LearnPrompt
- 6 skills: dream-memory, memory-extractor, verification-gate, swarm-coordinator, structured-context-compressor, kairos-lite
- Key patterns: prompt+script separation, structured output contracts, read-only by default, durable vs ephemeral

### Migration Guide
- **No breaking changes** - fully backward compatible
- 3 new sub-skills available immediately
- Verification gate can be wired as a post-implementation hook
- Memory pipeline enhances existing memory management
- Context compressor useful for long sessions

## [3.18.0] - 2026-04-02

### Changed - Self-Iteration: Simplicity Criterion Applied to Itself

Applied the autoresearch simplicity criterion to Super-Skill's own SKILL.md.

#### Diagnosed Issues
| # | Issue | Type | Severity |
|---|-------|------|----------|
| 1 | Stale "V3.15" reference in standards header | Outdated | HIGH |
| 2 | Stale "V3.14" reference in hooks header | Outdated | HIGH |
| 3 | Stale "V3.10" reference in auto-update header | Outdated | MEDIUM |
| 4 | Redundant JSON config block (already in settings.json) | Duplication | HIGH |
| 5 | Redundant Context Hub commands (already in sub-skill) | Duplication | MEDIUM |
| 6 | Redundant auto-update env vars (already in settings.json) | Duplication | MEDIUM |
| 7 | Frontmatter 355 chars (recommended <200) | Bloat | MEDIUM |

#### Changes Applied
| Change | Lines Saved | Rationale |
|--------|------------|-----------|
| Fixed 3 stale version refs | 0 (correctness) | Accuracy |
| Removed JSON config block | -13 | Lives in settings.json |
| Removed Context Hub commands | -12 | Lives in sub-skill |
| Removed auto-update config | -10 | Lives in settings.json |
| Trimmed frontmatter | -158 chars (44%) | Token budget |

#### Metrics
- SKILL.md: 505 → 459 lines (**9% reduction**)
- Frontmatter: 355 → 197 chars (**44% reduction**)
- Zero functionality lost (simplicity criterion: equal capability, simpler file)

### Migration Guide
- **No breaking changes** - fully backward compatible
- All removed content preserved in settings.json or sub-skill files
- SKILL.md is leaner and faster to load

## [3.17.0] - 2026-04-01

### Added - Research-Driven Self-Iteration

Applied 5 insights from latest AI agent research (March-April 2026):

#### 1. Hierarchical Orchestration (Planner-Worker-Judge)
Evidence: Flat multi-agent architectures fail (Cursor tried 20 equal-status agents → throughput of 2-3). Success requires three roles:
- **Planner**: Explores codebase, creates tasks, assigns priorities
- **Worker**: Executes tasks in git worktree isolation
- **Judge**: Evaluates results, decides keep/discard/rollback

Applied to Phase 8 (Autonomous Development).

#### 2. Context Engineering > Prompt Engineering
The key discipline shift: ensure the agent sees the right information at the right time.
- **Just-in-Time Context**: Load data at runtime via tools, not pre-embedded
- **Progressive Disclosure**: SKILL.md < 500 lines, references loaded on demand
- **Compaction Survival**: CLAUDE.md documents accumulated learnings
- **Token Budget Discipline**: Every paragraph must earn its tokens

Added new "Context Engineering" section.

#### 3. Freedom Levels (Anthropic Official)
Match freedom level to task fragility:
- **High freedom**: Code reviews, refactoring (multiple valid approaches)
- **Medium freedom**: Feature implementation (preferred pattern, acceptable variation)
- **Low freedom**: Database migrations, deployments (exact scripts required)

Applied to Phase 8 task assignments.

#### 4. Variance Inequality (Meta-Insight)
When self-improvement stalls, strengthen the verifier, not the generator.
A weaker generator + strong verifier > strong generator + weak verifier.
Invest more tokens and logic in validation than generation.

Added to Core Philosophy section.

#### 5. Hooks as Deterministic Orchestration
Convert behavioral instructions that MUST always happen from SKILL.md to hooks.
LLM compliance is probabilistic; hook execution is guaranteed.
PostToolUse hooks for auto-logging already in place.

### Changed
- Phase 8 enhanced with Planner-Worker-Judge hierarchical orchestration
- Added Context Engineering section with token budget discipline
- Added Freedom Levels to Phase 8 task assignments
- Added Variance Inequality to Core Philosophy
- Updated description with "hierarchical multi-agent orchestration"
- Updated header to V3.17

### Research Sources
- [AI Coding Agents 2026: Coherence Through Orchestration](https://mikemason.ca/writing/ai-coding-agents-jan-2026/) - Planner-Worker-Judge pattern
- [Anthropic Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Freedom levels, progressive disclosure
- [Self-Improving AI Agents: The 2026 Guide](https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide) - Variance inequality
- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide) - Deterministic orchestration

### Migration Guide
- **No breaking changes** - fully backward compatible
- Phase 8 automatically uses hierarchical orchestration
- Context engineering patterns apply to all phases
- Freedom levels guide task assignment granularity

## [3.16.0] - 2026-04-01

### Changed - Self-Iteration Upgrade (Simplicity Criterion)

Applied the autoresearch simplicity criterion to Super-Skill itself.

#### Diagnosed Issues
1. **Duplicate section**: "2026 AI-Assisted Engineering Standards" table appeared twice (lines 14-31 and 88-104)
2. **Stale version in duplicate**: Duplicate section header said V3.13 instead of V3.15
3. **File bloat**: SKILL.md at 603 lines (recommended <500 lines per skill-creator)
4. **Overlong description**: Frontmatter description was 600+ chars (recommended <200)
5. **Version history bloat**: 120+ lines of version history in SKILL.md (belongs in CHANGELOG.md)
6. **Skill count inconsistency**: Said "32+" in some places, 33 in others

#### Changes Applied (KEEP decisions)
| Change | Lines | Rationale |
|--------|-------|-----------|
| Removed duplicate standards table | -17 | Identical information, stale version |
| Trimmed frontmatter description | -400 chars | 70% shorter, same information density |
| Moved version history to CHANGELOG | -100 | Single source of truth |
| Fixed skill count to 33+ | Consistency | All references now match |
| Updated to V3.16 | Versioning | Current version |

#### Metrics
- SKILL.md: 603 → ~420 lines (30% reduction)
- Frontmatter description: 600+ → ~200 chars (70% reduction)
- Zero functionality lost (simplicity criterion: equal capability, simpler file)

### Migration Guide
- **No breaking changes** - fully backward compatible
- All version history preserved in CHANGELOG.md
- SKILL.md is leaner and faster to load

## [3.15.0] - 2026-03-29

### Added - Autonomous Experiment Loop (from karpathy/autoresearch)

**MAJOR FEATURE**: Integrated autonomous experiment loop from Andrej Karpathy's autoresearch (58K+ stars)

#### Source
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) - Fully autonomous AI-driven research
- 58,226 stars, 8,074 forks, MIT License
- Core idea: AI agent runs unsupervised overnight, modifying code, running experiments, evaluating results

#### Core Philosophy: Human Programs the Process, AI Executes
- Human edits instructions (SKILL.md / program.md)
- AI modifies implementation code
- Infrastructure (tests, CI/CD, lint) is read-only ground truth

#### The Infinite Experiment Loop
```
1. READ    → Analyze current git state and codebase
2. MODIFY  → Implement experimental improvement
3. COMMIT  → Git commit with experiment description
4. TEST    → Run tests, capture output (NOT streamed)
5. EVALUATE → Parse results against acceptance criteria
6. DECIDE  → KEEP (improved) or DISCARD (worse/equal)
7. LOG     → Record to experiments.tsv
8. NEXT    → Advance to next experiment idea
```

#### Decision Rules
| Outcome | Action | Criteria |
|---------|--------|----------|
| KEEP | Advance branch | Tests pass + metric improved + complexity justified |
| DISCARD | git reset | Tests fail OR metric regressed OR unnecessary complexity |
| CRASH | Fix or skip | Timeout/OOM/NaN → log error → next idea |

#### Simplicity Criterion (from autoresearch)
- Small improvement + ugly complexity = NOT worth it
- Small improvement from **deleting code** = definitely keep
- Equal performance + simpler code = keep
- ~0 improvement + much simpler code = keep

#### NEVER STOP Protocol
- Do NOT pause to ask the human between experiments
- The human might be asleep
- If out of ideas: re-read code, combine approaches, try radical changes

#### Git-as-Experiment-Tracker
- Branch-per-session isolation (`autoresearch/session-N`)
- Branch advances only on improvements
- Failed experiments reverted via `git reset`
- Experiment log in `experiments.tsv` (NOT git-tracked)

#### Budget Constraints
```bash
TIME_BUDGET_PER_EXPERIMENT=300    # 5 min per experiment
MAX_EXPERIMENTS_PER_SESSION=100   # ~100 experiments overnight
MEMORY_BUDGET_MB=4096             # Max memory per experiment
```

#### New Sub-Skill: autonomous-loop
- Created `skills/autonomous-loop/SKILL.md`
- Infinite experiment loop with keep/discard cycles
- Git-as-experiment-tracker pattern
- Simplicity criterion and NEVER STOP protocol
- Budget constraints and failure handling
- Integration with Super-Skill Phase 8, 10, 12

### Changed
- Updated title to "Autonomous Development Orchestrator"
- Enhanced description with autoresearch integration
- Phase 8 now uses autonomous experiment loop
- Phase 10 (Ralph Loop) enhanced as autonomous loop instance
- Added autoresearch to 2026 AI-Assisted Engineering Standards table
- Core Skills table now includes `autonomous-loop`
- Total skills count: 32 → 33
- Settings.json env expanded with autonomous loop configuration
- Notification hook enhanced with experiment log review
- Stop hook enhanced with experiment log update and simplicity assessment

### Technical
- New sub-skill: `skills/autonomous-loop/SKILL.md`
- Updated `.claude/settings.json` with autonomous loop env vars
- SKILL.md updated with Autonomous Experiment Loop section
- Updated description and header to V3.15

### Research Sources
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) - 58K+ stars
- Three-file design: prepare.py (infrastructure), train.py (agent-modifiable), program.md (instructions)
- Key patterns: keep/discard loop, git-as-experiment-tracker, fixed budget single metric, simplicity criterion

### Migration Guide
- **No breaking changes** - fully backward compatible
- New `autonomous-loop` skill available as sub-skill
- Phase 8 automatically uses experiment loop when enabled
- Configure via environment variables as needed
- Set `AUTONOMOUS_LOOP_ENABLED=true` to enable

## [3.14.0] - 2026-03-26

### Added - Hooks-Based Auto-Execution System

**MAJOR FEATURE**: Automatic execution via Claude Code hooks configuration

#### Problem Solved
Super-Skill V3.13 had three critical issues:
1. Auto-update not running at startup
2. Not strictly executing all development steps
3. No automatic retrospective after task completion

#### Solution: Hooks Configuration

| Hook | Trigger | Action |
|------|---------|--------|
| **Notification** | Session start | Pre-Run Upgrade sequence |
| **Stop** | Session end | Post-Run Evolution sequence |
| **PostToolUse** | After tool execution | Logging and tracking |
| **SubagentStop** | Subagent completion | Agent activity logging |

#### New Files
- `.claude/settings.json` - Complete hooks configuration
- `scripts/phase-tracker.sh` - Phase tracking utility

#### Hooks Configuration
```json
{
  "hooks": {
    "Notification": {
      "handler": {
        "type": "prompt",
        "prompt": "Pre-Run Upgrade: 6-step sequence..."
      }
    },
    "Stop": {
      "handler": {
        "type": "prompt",
        "prompt": "Post-Run Evolution: 7-step sequence..."
      }
    },
    "PostToolUse": [...],
    "SubagentStop": {...}
  }
}
```

#### Automatic Execution Flow
```
NOTIFICATION HOOK (Session Start)
└→ Pre-Run Upgrade: Version Check → Upgrade → Best Practices → Sync

MAIN EXECUTION (14-Phase Workflow)
└→ Phase 0-12: Vision → ... → Deployment

STOP HOOK (Session End)
└→ Post-Run Evolution: Retrospective → Signal Extraction → Evolution
```

#### Environment Variables
```bash
SUPER_SKILL_AUTO_UPDATE=true
POST_RUN_EVOLUTION=true
PRE_RUN_UPGRADE=true
EVOLUTION_SIGNAL_THRESHOLD=12
```

### Changed
- Updated description with hooks-based auto-execution capability
- Enhanced startup sequence documentation with hooks integration
- Updated version to V3.14

### Technical
- New file: `.claude/settings.json` - Hooks configuration
- New file: `scripts/phase-tracker.sh` - Phase tracking utility
- SKILL.md updated with Hooks System section
- Full automatic workflow enforcement

### Migration Guide
- **No breaking changes** - fully backward compatible
- Hooks configuration in `.claude/settings.json` is automatically loaded
- Pre-run upgrade now executes via Notification hook at session start
- Post-run evolution now executes via Stop hook at session end
- All tool executions are logged for workflow tracking

## [3.13.0] - 2026-03-19

### Added - AI-Assisted Engineering Best Practices

**MAJOR FEATURE**: Comprehensive integration of industry-leading AI development patterns

#### Sources Integrated
| Source | Author | Focus |
|--------|--------|-------|
| [LLM Coding Workflow 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e) | Addy Osmani | AI-assisted engineering |
| [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Anthropic | Skill creation |
| [AI Agent Frameworks 2026](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) | OpenAgents | Framework comparison |

#### 10 Core Principles (Addy Osmani 2026)

1. **Specs Before Code** - "Waterfall in 15 minutes" planning pattern
2. **Iterative Chunks** - Manageable tasks, not whole codebase
3. **Context Packing** - Show relevant code, docs, constraints
4. **Model Selection** - Right tool for each task
5. **Human in Loop** - Verify, test, review everything
6. **Commit Often** - Version control as safety net
7. **Customize with Rules** - CLAUDE.md, style guides, examples
8. **Automation Force Multiplier** - CI/CD, linters, review bots
9. **Continuous Learning** - AI amplifies existing skills
10. **Accountable Engineer** - Human remains the director

#### Key Patterns Added

- **Waterfall-in-15-Minutes**: Rapid structured planning before coding
- **Context Packing Checklist**: High-level goals, examples, warnings, constraints
- **Never Commit Code You Can't Explain**: Understanding requirement
- **Progressive Disclosure**: Keep SKILL.md under 500 lines
- **Validation Loops**: Run validator → fix errors → repeat
- **Evaluation-Driven Development**: Create evaluations BEFORE documentation

### Changed
- Updated description with AI-assisted engineering patterns
- Added `references/best-practices-2026.md` for comprehensive patterns
- Updated `references/trending-standards.md` with Addy Osmani patterns
- Updated header to V3.13

### Technical
- New reference file: `references/best-practices-2026.md`
- Updated `references/trending-standards.md` with Section 0 for AI-Assisted Engineering
- SKILL.md updated with V3.13 capabilities

## [3.12.0] - 2026-03-14

### Added - Pre-Run Upgrade System

**MAJOR FEATURE**: Automated pre-session upgrade and best practices discovery

#### Pre-Run Upgrade Sequence (STEP -1)
Executes before every Super-Skill session:
1. **Version Check** - Check all sub-skills for available updates
2. **Sub-Skill Upgrade** - Upgrade outdated skills via `npx skills update`
3. **Best Practices Search** - Search GitHub trending for new patterns
4. **Pattern Integration** - Integrate discovered best practices
5. **Context Hub Sync** - Update Context Hub registry
6. **Evolution Sync** - Sync learnings from previous sessions

#### Best Practices Sources
- GitHub trending AI agent repositories
- LangChain/AutoGen/CrewAI patterns
- MCP Protocol latest standards
- Anthropic Skills best practices

#### Configuration
```bash
PRE_RUN_UPGRADE=true                    # Enable pre-run upgrade
PRE_RUN_BEST_PRACTICES_SEARCH=true      # Search for best practices
PRE_RUN_SEARCH_LIMIT=10                 # Max repos to search
```

#### New Sub-Skill: pre-run-upgrade
- Created `skills/pre-run-upgrade/SKILL.md`
- 6-step upgrade sequence
- Pre-run report generation
- Integration with startup sequence

### Added - Post-Run Evolution System

**MAJOR FEATURE**: Comprehensive post-project review and self-evolution

#### Post-Run Evolution Sequence (After Phase 12)
7-step evolution process after project completion:
1. **Project Retrospective** - Comprehensive project analysis
2. **Signal Extraction** - Defensive, opportunity, stagnation signals
3. **Quality Scoring** - 5-dimension quality analysis
4. **Evolution Decision** - Matrix-based evolution triggering
5. **Mutation Build & Apply** - Safe mutation with rollback
6. **Capsule Packaging** - Package successful patterns
7. **Cross-Session Learning Sync** - Persist learnings

#### Signal Types
| Type | Trigger | Priority |
|------|---------|----------|
| Defensive | Errors, failures, blockers | High |
| Opportunity | New patterns, optimizations | Medium |
| Stagnation | Repeated patterns, no improvement | Low |

#### Quality Dimensions
| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Correctness | 40% | Does it work? Bug count |
| Reliability | 25% | Will it keep working? |
| Maintainability | 20% | Can others understand it? |
| Performance | 10% | Is it fast enough? |
| Elegance | 5% | Is it clean? |

#### Evolution Types
- **REPAIR**: Fix identified issues
- **OPTIMIZE**: Improve existing capabilities
- **INNOVATE**: Add new capabilities

#### Configuration
```bash
POST_RUN_EVOLUTION=true                  # Enable post-run evolution
POST_RUN_RETROSPECTIVE=true              # Enable retrospective
POST_RUN_AUTO_EVOLVE=true                # Auto-apply evolutions
EVOLUTION_SIGNAL_THRESHOLD=12            # Minimum score for auto-evolution
```

#### New Sub-Skill: post-run-evolution
- Created `skills/post-run-evolution/SKILL.md`
- 7-step evolution sequence
- Signal extraction and scoring
- Mutation safety system
- Capsule packaging
- Cross-session learning sync

### Changed
- Updated description with pre-run upgrade and post-run evolution
- Added `pre-run-upgrade` and `post-run-evolution` to Core Skills
- Startup sequence now includes STEP -1: Pre-Run Upgrade
- Phase 12 now includes post-run evolution workflow
- Total skills count: 30 → 32

### Technical
- New sub-skill: `skills/pre-run-upgrade/SKILL.md`
- New sub-skill: `skills/post-run-evolution/SKILL.md`
- SKILL.md updated with V3.12 capabilities
- Enhanced startup sequence documentation

### Migration Guide
- **No breaking changes** - fully backward compatible
- Both new skills available as sub-skills immediately
- Pre-run upgrade executes automatically before Phase 0
- Post-run evolution executes automatically after Phase 12
- Configure with environment variables as needed

## [3.11.0] - 2026-03-14

### Added - High-Agency Execution Methodology (from pua/tanweai)

**MAJOR FEATURE**: Integrated high-agency execution methodology from PUA skill

#### Three Iron Rules
1. **Exhaust All Options** - Forbidden from saying "I can't solve this"
2. **Act Before Asking** - Use tools first, questions must include diagnostic results
3. **Take Initiative** - Deliver results end-to-end, don't wait to be pushed

#### Pressure Escalation System
- **L1** (2nd failure) → Switch to fundamentally different approach
- **L2** (3rd failure) → WebSearch + read source code + external docs
- **L3** (4th failure) → Complete 7-point checklist
- **L4** (5th+ failure) → Desperation mode - all resources deployed

#### Five-Step Debugging Methodology
- **Smell** → Pattern recognition (similar issues?)
- **Elevate** → Scope expansion (right layer?)
- **Mirror** → Reproduction (minimal test case?)
- **Execute** → Systematic fix (one at a time)
- **Retrospective** → Learning (prevent recurrence)

#### Proactivity Matrix
| Score | Behavior |
|-------|----------|
| 3.25 | Passive - Waits for instructions |
| 3.5 | Reactive - Responds to issues |
| 3.75 | Proactive - Anticipates problems (target) |
| 4.0 | Super-Proactive - Prevents problems |

#### Benchmark Results (from research)
- +36% fix count
- +65% verification
- +50% tool calls
- +50% hidden issue discovery

#### New Sub-Skill: high-agency
- Created `skills/high-agency/SKILL.md`
- Phase 8 integration for development debugging
- Phase 9 integration for QA issue investigation
- Recovery Protocol and Quality Compass

### Added - Cognitive Modes (from gstack/Garry Tan/YC)

**MAJOR FEATURE**: Six cognitive modes for AI development from Y Combinator CEO

#### Mode Overview
| Mode | Trigger | Focus |
|------|---------|-------|
| **CEO** | `/plan-ceo-review` | 10-star product vision |
| **Eng Manager** | `/plan-eng-review` | Architecture, edge cases |
| **Paranoid Reviewer** | `/review` | Production bug hunting |
| **Release Engineer** | `/ship` | Deploy automation |
| **QA Engineer** | `/browse` | Browser automation (Playwright) |
| **Eng Manager (Retro)** | `/retro` | Retrospectives |

#### Mode Integration with Super-Skill Phases
- **CEO Mode** → Phase 0 (Vision), Phase 4 (Requirements)
- **Eng Manager Mode** → Phase 5 (Architecture), Phase 5b (Design)
- **Paranoid Reviewer Mode** → Phase 8 (Development), Phase 9 (QA)
- **Release Engineer Mode** → Phase 7 (Init), Phase 11 (Deployment)
- **QA Engineer Mode** → Phase 9 (QA)
- **Eng Manager Retro Mode** → Phase 12 (Evolution)

#### New Sub-Skill: cognitive-modes
- Created `skills/cognitive-modes/SKILL.md`
- Mode-specific prompts and checklists
- Phase integration mapping
- Mode combination patterns

### Changed
- Updated description with 6 cognitive modes and high-agency methodology
- Added `high-agency` and `cognitive-modes` to Core Skills
- Total skills count: 28 → 30
- Enhanced phase integration with cognitive mode recommendations

### Technical
- New sub-skill: `skills/high-agency/SKILL.md`
- New sub-skill: `skills/cognitive-modes/SKILL.md`
- SKILL.md updated with V3.11 capabilities

### Research Sources
- [pua (tanweai)](https://github.com/tanweai/pua) - High-agency AI methodology
- [gstack (Garry Tan)](https://github.com/garrytan/gstack) - 6 cognitive modes for AI development

### Migration Guide
- **No breaking changes** - fully backward compatible
- Both new skills available as sub-skills immediately
- High-agency methodology applies automatically in Phase 8/9
- Cognitive modes can be invoked via trigger commands

## [3.10.0] - 2026-03-14

### Added - Context Hub Integration (Andrew Ng)

**MAJOR FEATURE**: Integrated Context Hub for curated, versioned API documentation

#### Context Hub (chub) Integration
- **Search** curated API docs with `chub search <query>`
- **Get** versioned docs with `chub get <id> --lang <language>`
- **Annotate** docs with persistent local notes
- **Feedback** loop to improve documentation quality
- **Self-improving** annotation system across sessions

#### New Sub-Skill: get-api-docs
- Created `skills/get-api-docs/SKILL.md`
- Phase 3 integration for knowledge base building
- Phase 8 integration for quick development reference
- Annotation persistence for learning across sessions

### Added - Auto-Update Mechanism

**MAJOR FEATURE**: Super-Skill now auto-updates before each development session

#### Auto-Update Sequence
```
STEP 0: Auto-Update → Self-update Super-Skill and all dependent skills
STEP 1: Version Check → python scripts/auto_update.py
STEP 2: Evolver Check → python scripts/check_evolver.py
...
```

#### Update Capabilities
- Check Super-Skill version from GitHub
- Pull latest changes if update available
- Check all dependent skills for updates
- Update skills with: `npx skills update <skill-name>`
- Refresh Context Hub registry: `chub update`

#### New Environment Variables
```bash
SUPER_SKILL_AUTO_UPDATE=true       # Enable auto-update (default: true)
SUPER_SKILL_UPDATE_CHECK=true      # Check for updates (default: true)
SUPER_SKILL_SKILLS_UPDATE=true     # Update dependent skills (default: true)
CHUB_AUTO_UPDATE=true              # Update Context Hub registry (default: true)
```

### Changed
- Updated 2026 GitHub Trending Standards table to include Context Hub
- Added `get-api-docs` to Core Skills (Always Available)
- Total skills count: 27 → 28
- Updated startup sequence to include STEP 0: Auto-Update

### Technical
- New sub-skill: `skills/get-api-docs/SKILL.md`
- Context Hub CLI integration (`pip install chub`)
- Annotation persistence in `~/.chub/cache/`

### Research Sources
- [Context Hub](https://github.com/andrewyng/context-hub) - Andrew Ng's curated API documentation

### Migration Guide
- **No breaking changes** - fully backward compatible
- Install Context Hub CLI: `pip install chub`
- Auto-update is enabled by default
- Configure with environment variables as needed

## [3.9.0] - 2026-03-14

### Added - GitHub Trending Standards Integration

**MAJOR FEATURE**: Integrated best practices from top GitHub trending projects

#### AI Agent Framework Patterns
- **LangChain (122K★)** - Chain-based workflow patterns
- **LangGraph (24K+★)** - Graph-based orchestration with state persistence
- **AutoGen (52K+★)** - Multi-agent conversation patterns
- **CrewAI (30K+★)** - Role-based task delegation patterns

#### MCP Protocol 2026 Integration
- MCP Server configuration patterns
- Tool discovery and invocation patterns
- Resource access patterns
- 2026 MCP Roadmap alignment

#### Anthropic Skills Best Practices
- 15-30 minute skill build methodology
- Progressive disclosure patterns
- Hook integration patterns
- Metadata formatting standards

#### Production Deployment Patterns
- OpenTelemetry observability integration
- Health check endpoints (liveness/readiness)
- Metrics collection with Prometheus
- Distributed tracing with Jaeger

### Added
- `references/trending-standards.md` - Complete GitHub trending standards reference
- LangGraph graph-based phase orchestration patterns
- AutoGen multi-agent conversation patterns
- CrewAI role-based task delegation patterns
- MCP tool discovery and invocation code patterns
- Token budget management patterns
- Memory persistence with ChromaDB patterns
- OpenTelemetry integration patterns
- Health check endpoint patterns

### Changed
- Updated description with 2026 GitHub trending standards
- Enhanced multi-agent orchestration with production patterns
- Added MCP Protocol integration to core capabilities

### Technical
- New reference file: `references/trending-standards.md` (comprehensive 2026 standards)
- Integration matrix expanded with framework comparisons
- Code examples for LangGraph, AutoGen, CrewAI, MCP

### Research Sources
- [LangChain](https://github.com/langchain-ai/langchain) - 122K+ stars
- [AutoGen](https://github.com/microsoft/autogen) - 52K+ stars
- [LangGraph](https://github.com/langchain-ai/langgraph) - 24K+ stars
- [CrewAI](https://github.com/crewAIInc/crewAI) - 30K+ stars
- [MCP Protocol](https://github.com/modelcontextprotocol) - Official Anthropic
- [Anthropic Skills Guide](https://resources.anthropic.com/) - 33-page official guide

### Migration Guide
- **No breaking changes** - fully backward compatible
- All new patterns available in `references/trending-standards.md`
- Existing workflows continue unchanged
- Optional: Adopt new framework patterns as needed

## [3.8.1] - 2026-03-11

### Changed - skill-creator Best Practices Refactor

**MAJOR REFACTOR**: Optimized Super-Skill following skill-creator guidelines

#### SKILL.md Optimization
- **Reduced from ~70KB to ~12KB** (82% token reduction)
- Implemented **progressive disclosure** pattern
- Streamlined description for better triggering
- Moved detailed phase content to `references/phases.md`
- Moved skill integration details to `references/skills-matrix.md`
- Under 500 lines as recommended by skill-creator

#### Progressive Disclosure Structure
```
SKILL.md (core workflow)
├── references/phases.md (detailed phase specs)
├── references/skills-matrix.md (27+ skill mapping)
├── EVOLUTION.md (GEP Protocol)
└── skills/ (27 sub-skills)
```

#### Description Optimization
- Before: 600+ characters, exhaustive feature list
- After: ~200 characters, focused triggering keywords
- Better signal-to-noise ratio for skill selection

### Added
- `references/phases.md` - Complete 14-phase workflow reference
- `references/skills-matrix.md` - Full skills integration matrix

### Technical
- SKILL.md: 70KB → 12KB (82% reduction)
- Lines: 2000+ → ~400 (80% reduction)
- Token efficiency: Significant improvement for context loading
- Follows skill-creator best practices for skill design

### Migration Guide
- **No breaking changes** - fully backward compatible
- All functionality preserved in reference files
- Sub-skills unchanged
- Phase workflow identical

## [3.8.0] - 2026-03-03

### Added
- **GEP Protocol Integration from autogame-17/evolver**
  - Integrated GEP (Genome Evolution Protocol) from autogame-17/evolver
  - Signal extraction with de-duplication (signals.js)
  - Gene/Capsule selection with drift intensity (selector.js)
  - Mutation building with safety constraints (mutation.js)
  - Personality state evolution (personality.js)
  - Evolution archive (events.jsonl)
  - Strategy presets: balanced, innovate, harden, repair-only, early-stabilize, steady-state, auto

- **Enhanced darwin-evolution Skill (V2.0)**
  - Upgraded from V1.0 to V2.0 with full GEP Protocol implementation
  - 5 GEP Protocol Objects: Mutation, PersonalityState, EvolutionEvent, Gene, Capsule
  - Comprehensive signal detection system (defensive, opportunity, stagnation)
  - Population-dependent drift intensity for exploration
  - Safety mechanisms: constitutional constraints, blast radius control
  - Integration with Super-Skill Phase 12 evolution workflow

- **GEP Asset Files**
  - `assets/gep/genes.json` - Default gene definitions (5 genes)
  - `assets/gep/capsules.json` - Success capsule archive
  - `assets/gep/events.jsonl` - Append-only evolution event log

- **Evolution Support Modules**
  - `skills/darwin-evolution/signals.js` - Signal extraction and analysis
  - `skills/darwin-evolution/selector.js` - Gene/Capsule selection with drift
  - Lifecycle management, self-repair, skills monitor from evolver ops module

### Changed
- Updated main SKILL.md description with GEP Protocol self-evolution emphasis
- Enhanced EVOLUTION.md with full GEP Protocol documentation
- Updated description to reflect 27+ specialized skills (was 25+)

### Technical
- Enhanced integration with autogame-17/evolver (MIT License)
- Strategy presets configurable via EVOLVE_STRATEGY environment variable
- Blast radius policy: 60 files / 20000 lines hard cap
- Validation command safety with prefix whitelist

### Research Sources
- [autogame-17/evolver](https://github.com/autogame-17/evolver) - GEP Protocol implementation
- [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) - Self-evolution theory
- [EvoMap Network](https://evomap.ai) - Evolution ecosystem

### Migration Guide
- **No breaking changes** - fully backward compatible
- darwin-evolution V2.0 replaces V1.0 seamlessly
- GEP assets auto-initialized on first evolution run
- Existing evolution workflows continue to work

## [3.7.0] - 2026-03-02

### Added - Comprehensive Production-Grade Skills Expansion

This release adds 15 new specialized skills covering all aspects of production-grade development, from MCP integration to accessibility, security, and real-time communication.

#### Infrastructure & Integration Skills

- **MCP Integration Skill**
  - Model Context Protocol (MCP) integration patterns
  - Tool discovery and invocation via JSON-RPC 2.0
  - Transport modes: stdio, HTTP, SSE
  - OAuth authentication flows
  - Scope-based configuration (local, project, user)
  - Security best practices and input sanitization

- **CI/CD Automation Skill**
  - GitHub Actions workflow patterns
  - Modular reusable workflows
  - Smart triggering conditions
  - Performance optimization with caching
  - Matrix builds for cross-platform testing
  - OIDC authentication for cloud services
  - Blue-green and canary deployment strategies

- **Security Scanning Skill**
  - SAST (Static Application Security Testing)
  - SCA (Software Composition Analysis)
  - Secret scanning with GitLeaks/TruffleHog
  - OWASP Top 10 coverage
  - Container security with Trivy
  - AI-powered vulnerability analysis

#### Development & Quality Skills

- **Testing Automation Skill**
  - TDD (Test-Driven Development) workflow
  - Unit testing with Jest
  - Integration testing patterns
  - E2E testing with Playwright
  - Mutation testing with Stryker
  - Coverage analysis (80%+ target)

- **Code Transformation Skill**
  - TypeScript Compiler API patterns
  - Babel plugin development
  - jscodeshift codemods
  - AST-based refactoring
  - Automated migration scripts

- **Automated Documentation Skill**
  - AI-powered docstring generation
  - Python docstrings (Google, NumPy, Sphinx)
  - JavaScript/TypeScript JSDoc/TSDoc
  - OpenAPI/Swagger generation
  - README/CHANGELOG templates

#### Architecture & Patterns Skills

- **Data Patterns Skill**
  - SQL and NoSQL schema design
  - Prisma schema patterns
  - Repository pattern implementation
  - Unit of Work pattern
  - CQRS pattern
  - Migration strategies

- **API Patterns Skill**
  - REST API design principles
  - GraphQL schema patterns
  - Pagination (cursor/offset)
  - Filtering and sorting
  - Authentication (JWT/API Key)
  - Rate limiting

- **State Management Skill**
  - React Query for server state
  - Zustand for client state
  - React Context patterns
  - URL state synchronization
  - Form state with React Hook Form

#### Performance & Reliability Skills

- **Performance Optimization Skill**
  - Frontend: Bundle optimization, virtualization, image optimization
  - Backend: Caching, connection pooling, async operations
  - Database: Indexing, query optimization, N+1 prevention
  - Profiling and monitoring

- **Error Recovery Skill**
  - Retry strategies with exponential backoff
  - Circuit breaker pattern
  - Fallback chains
  - Bulkhead isolation
  - Error classification and self-healing

- **Context Management Skill**
  - Token budget management
  - Priority-based content retention
  - Intelligent compression
  - Memory persistence
  - Checkpoint and restore

#### Operations & Observability Skills

- **Monitoring & Observability Skill**
  - Structured logging (pino)
  - Metrics collection (Prometheus)
  - Distributed tracing (OpenTelemetry)
  - Health checks (liveness, readiness)
  - Alerting rules and runbooks

#### User Experience Skills

- **Accessibility (A11y) Skill**
  - WCAG 2.1 compliance patterns
  - Semantic HTML structure
  - ARIA patterns for custom components
  - Keyboard navigation
  - Screen reader support
  - Automated a11y testing

- **Internationalization (i18n) Skill**
  - i18next integration
  - Translation file management
  - Pluralization patterns
  - Date/number/currency formatting (Intl API)
  - RTL support with CSS logical properties

#### Specialized Feature Skills

- **Real-Time WebSockets Skill**
  - Socket.io server/client patterns
  - Server-Sent Events (SSE)
  - Connection management
  - Real-time data synchronization
  - Optimistic updates and conflict resolution

- **Search & Indexing Skill**
  - Elasticsearch integration
  - Vector search with pgvector
  - Meilisearch/Typesense patterns
  - Faceted search
  - Autocomplete implementation
  - Hybrid search (BM25 + vectors)

- **Prompt Engineering Skill**
  - Zero-shot and few-shot patterns
  - Chain-of-Thought (CoT)
  - Self-Consistency
  - Least-to-Most decomposition
  - Structured output prompts
  - Iterative optimization

### Changed
- Updated title to "Comprehensive AI-Native Development Orchestrator"
- Enhanced description with 24 core capabilities
- All 21 sub-skills now integrated with phase-specific workflows

### Technical
- Added 15 new skill files in skills/ directory
- All skills follow consistent SKILL.md format
- Integrated with phase-specific action mappings

### Research Sources
- [Anthropic MCP Documentation](https://docs.anthropic.com/claude-code/mcp)
- [GitHub Actions Best Practices](https://docs.github.com/actions)
- [OWASP Security Guidelines](https://owasp.org/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/)
- [OpenTelemetry](https://opentelemetry.io/)
- [i18next](https://www.i18next.com/)
- [Socket.io](https://socket.io/)
- [Elasticsearch](https://www.elastic.co/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

### Migration Guide
- **No breaking changes** - fully backward compatible
- All new skills available as sub-skills immediately
- Phase integration automatic for relevant phases
- Manual skill invocation available via skill system

## [3.6.0] - 2026-03-02

### Added
- **Multi-Agent Orchestration Skill**
  - New `multi-agent-orchestration` sub-skill
  - Combines LangGraph (graph-based workflows), AutoGen (conversation-driven), and CrewAI (role-based) patterns
  - Support for DAG workflows with checkpointing
  - Conversation-driven multi-agent collaboration
  - Role-based team coordination (Crew-Role-Task paradigm)
  - Parallel agent execution for independent tasks
  - Integrated into all development phases (Phase 8 for development crews)

- **Advanced Reasoning Skill**
  - New `advanced-reasoning` sub-skill
  - Chain-of-Thought (CoT) - Linear step-by-step reasoning
  - Tree-of-Thought (ToT) - Branching exploration with backtracking
  - Graph-of-Thought (GoT) - Arbitrary graph structure for complex problems
  - Self-consistency with multiple reasoning paths
  - Automatic pattern selection based on problem complexity
  - Phase-specific reasoning pattern recommendations

- **Darwin Evolution Skill**
  - New `darwin-evolution` sub-skill inspired by Darwin Gödel Machine
  - Iterative self-modification and improvement
  - Benchmark-driven optimization (SWE-bench, Polyglot, HumanEval)
  - Archive-based evolution with diverse mutation exploration
  - Constitutional constraints for safe evolution
  - Sandbox execution for mutation testing
  - Rollback capability for failed mutations

- **Enhanced Core Capabilities**
  - 13th core capability: Multi-agent orchestration
  - 14th core capability: Advanced reasoning patterns
  - 15th core capability: Darwin Gödel Machine self-evolution

- **GitHub Best Practices Integration**
  - LangGraph patterns for production-grade workflow orchestration
  - AutoGen patterns for conversation-driven collaboration
  - CrewAI patterns for role-based team coordination
  - CoT/ToT/GoT reasoning from dair-ai/Prompt-Engineering-Guide
  - Darwin Gödel Machine self-evolution from arXiv:2505.22954

### Changed
- Updated title to "Multi-Agent & Advanced Reasoning Orchestrator"
- Enhanced description with 13 core capabilities
- Skill Integration Matrix expanded with new skills for all phases
- Cross-Cutting skills now include multi-agent-orchestration, advanced-reasoning, and darwin-evolution

### Technical
- Added `skills/multi-agent-orchestration/SKILL.md` - Multi-agent coordination
- Added `skills/advanced-reasoning/SKILL.md` - CoT/ToT/GoT reasoning patterns
- Added `skills/darwin-evolution/SKILL.md` - Self-evolution engine
- SKILL.md description enhanced with 13 core capabilities

### Research Sources
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based agent orchestration
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent conversation framework
- [CrewAI](https://github.com/crewAIInc/crewAI) - Role-based agent teams
- [Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954)

### Migration Guide
- **No breaking changes** - fully backward compatible
- All three new skills included as sub-skills
- Automatically available in relevant phases
- Advanced reasoning can be triggered manually for complex decisions

## [3.5.0] - 2026-03-01

### Added
- **Auto Git Create Skill Integration**
  - New `auto-git-create` sub-skill from sagar-datta/auto-git-create
  - Automated GitHub repository creation from terminal
  - Shell function implementation for Bash/Zsh
  - PowerShell variant for Windows users
  - GitHub CLI and API integration
  - Integrated into Phase 7 (Project Initialization)
  - Integrated into Phase 11 (Deployment)

- **Repository Automation Features**
  - Create directory and navigate into it
  - Prompt for repository description
  - Create GitHub repository via API
  - Generate README.md, .gitignore, LICENSE files
  - Initialize git, commit, add remote, and push
  - Open VS Code (optional)
  - Support for public/private repository visibility
  - Project template support (React, Next.js, etc.)

- **Enhanced Skill Integration Matrix**
  - Phase 7 now includes auto-git-create for repository setup
  - Phase 11 now includes auto-git-create for deployment workflow

### Changed
- Updated title to "Git Automation-Enabled Development Orchestrator"
- Enhanced description with automated git workflow capabilities
- Added 10th core capability: Automated GitHub repository creation
- Skill integration matrix expanded with git automation skills

### Technical
- Added `skills/auto-git-create/SKILL.md` - Repository automation skill
- SKILL.md description enhanced with 10 core capabilities
- Source: https://github.com/sagar-datta/auto-git-create

### Migration Guide
- **No breaking changes** - fully backward compatible
- auto-git-create included as a sub-skill
- Requires GitHub CLI (`gh`) or personal access token
- Automatically available in Phase 7/11

## [3.4.0] - 2026-03-01

### Added
- **Brainstorming Skill Integration**
  - New `brainstorming` sub-skill from Obra Superpowers
  - 6-step systematic exploration process
  - "One question at a time" methodology
  - YAGNI principle enforcement
  - Design Decision Record (DDR) generation
  - Integrated into Phase 0 (Visionary Elevation) and Phase 4 (Requirements)
  - Design exploration support in Phase 5-5b (Architecture & Design)

- **Systematic Debugging Skill Integration**
  - New `systematic-debugging` sub-skill from Obra Superpowers
  - Four-phase debugging methodology:
    1. Root Cause Investigation
    2. Pattern Analysis
    3. Hypothesis and Testing
    4. Implementation
  - "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST" principle
  - Integrated into Phase 8 (Autonomous Development) and Phase 9 (QA)
  - Debugging anti-patterns prevention
  - Comprehensive debugging checklists

- **Enhanced Skill Integration Matrix**
  - Phase 0 now includes brainstorming for design exploration
  - Phase 4 now includes brainstorming for requirement clarification
  - Phase 5-5b now includes brainstorming for architecture decisions
  - Phase 8 now includes systematic-debugging for bug resolution
  - Phase 9 now includes systematic-debugging for QA bug investigation

### Changed
- Updated title to "Brainstorming & Debugging-Enabled Development Orchestrator"
- Enhanced description with brainstorming and debugging capabilities
- Skill integration matrix expanded with new skills
- Startup sequence now includes brainstorming and debugging skills check

### Technical
- Added `skills/brainstorming/SKILL.md` - 6-step brainstorming process
- Added `skills/systematic-debugging/SKILL.md` - 4-phase debugging methodology
- SKILL.md description enhanced with 9 core capabilities
- Source: https://github.com/obra/superpowers

### Migration Guide
- **No breaking changes** - fully backward compatible
- Both skills are included as sub-skills
- Brainstorming automatically available in Phase 0/4/5
- Systematic debugging automatically available in Phase 8/9

## [3.3.0] - 2026-03-01

### Added
- **Skills Discovery Integration (Phase 2b)**
  - New Phase 2b: Skills Discovery for automatic capability extension
  - Integration with Vercel Labs find-skills skill
  - Search and install skills from open agent skills ecosystem
  - Auto-install high-relevance skills (≥80% score)
  - Dynamic capability extension during project planning

- **find-skills Sub-Skill**
  - `skills/find-skills/SKILL.md` - Standalone find-skills skill
  - Automated skills ecosystem search
  - Skills evaluation and scoring framework
  - Auto-installation with `npx skills add`
  - Integration with Super-Skill Phase 2b workflow

- **Enhanced Workflow**
  - 12-Phase → 14-Phase Autonomous Workflow
  - Phase 2b triggers after GitHub Discovery finds no suitable project
  - SKILLS_DISCOVERY_REPORT.md generation
  - Gap analysis for missing capabilities

### Changed
- Updated title to "Skills-Discovery-Enabled Development Orchestrator"
- Enhanced description with skills discovery capabilities
- Core principle now includes Phase 2b (Skills Discovery)
- Startup sequence includes find-skills version check
- Skill integration matrix updated with find-skills

### Technical
- SKILL.md size: 68KB (enhanced with Phase 2b)
- Package includes find-skills sub-skill
- Compatible with Skills CLI (`npx skills`)
- Source: https://github.com/vercel-labs/skills/tree/main/skills/find-skills

### Migration Guide
- **No breaking changes** - fully backward compatible
- find-skills is included as a sub-skill
- Phase 2b automatically triggers when needed
- Install Skills CLI: `npm install -g @vercel-labs/skills-cli`

## [3.2.0] - 2026-02-24

### Added
- **Claude-Mem Persistent Memory Integration**
  - Cross-session memory retention (no more "goldfish memory")
  - 90% token savings through intelligent context compression
  - SQLite + ChromaDB hybrid storage (semantic + keyword search)
  - Automatic memory capture across all 13 phases
  - Smart context injection at session startup
  - Web interface at http://localhost:37777

- **Enhanced Startup Sequence**
  - STEP 3: Start Claude-Mem Worker (auto-start)
  - STEP 4: Retrieve Relevant Memories (automatic)
  - STEP 5: Inject Context into Session (automatic)
  - Historical decisions and patterns available from start

- **Memory Integration Scripts**
  - `setup_claude_mem.py` - Installation and verification
  - `CLAUDE_MEM.md` - Comprehensive integration documentation (20KB)

- **Memory Types Supported**
  - Conversation Memory (requirements, decisions)
  - Code Memory (patterns, solutions, debugging)
  - Project Memory (structure, dependencies, deployment)
  - Evolution Memory (lessons, patterns, improvements)

### Changed
- Updated title to "Memory-Preserving Development Orchestrator"
- Enhanced description with persistent memory capabilities
- All 13 phases now capture memories automatically
- Startup sequence expanded from 4 to 7 steps

### Performance
- Token Savings: Up to 90% (95% in Endless Mode)
- Session Length: Extended by ~20x
- Storage: 100-500 MB per year (local only)
- Privacy: 100% local, no cloud sync

### Migration Guide
- **No breaking changes** - fully backward compatible
- Install Claude-Mem:
  ```bash
  cd C:\Users\91216\.claude\skills
  git clone https://github.com/thedotmack/claude-mem.git
  cd claude-mem && npm install && npm run build
  npm run worker:start
  ```
- Verify integration: `python scripts/setup_claude_mem.py verify`

## [3.1.0] - 2026-02-22

### Added
- **Deep Capability-Evolver Integration**
  - Phase 12 enhanced with two-step evolution workflow
  - Automatic evolution trigger after project completion
  - GEP (Genome Evolution Protocol) support
  - Evolution safety mechanisms (backup, rollback, validation)

- **Evolution Configuration Files**
  - `.env.super-skill` - Super-Skill specific evolution config
  - `check_evolver.py` - Evolver installation verification
  - `trigger_evolution.py` - Automatic evolution trigger
  - `EVOLUTION.md` - Comprehensive evolution documentation

- **Enhanced Startup Sequence**
  - STEP 2: Verify Capability-Evolver installation
  - Automatic evolver health check
  - Configuration validation

- **Evolution Workflow**
  - Post-project automatic analysis
  - Signal detection (memory_missing, pattern_gap, etc.)
  - Automatic improvements and updates
  - Version tracking and rollback capability

- **GEP Protocol Objects**
  - Mutation: Genetic modifications to skill behavior
  - PersonalityState: Adaptive/Conservative/Experimental
  - EvolutionEvent: Optimization types and priorities
  - Gene: Atomic evolution units (workflow, decision, quality, knowledge)
  - Capsule: Packaged evolution with backup and version control

### Changed
- Updated title to "Self-Evolving Development Orchestrator"
- Enhanced description with evolution capabilities
- Phase 12 gate checks now include evolution validation
- Skill integration matrix updated with capability-evolver

### Technical
- SKILL.md size: 51KB (enhanced with evolution workflow)
- EVOLUTION.md: 11KB (comprehensive evolution guide)
- Package size: 42KB (includes evolution scripts and docs)
- Evolution triggers: 4 types (project complete, learning event, user feedback, periodic)
- Safety mechanisms: Backup before evolution, critical path protection, rollback capability

### Migration Guide
- **No breaking changes** - fully backward compatible
- Install capability-evolver if not present
- Review EVOLUTION.md for new capabilities
- Evolution triggers automatically after Phase 12

## [3.0.0] - 2026-02-22

### Added
- **Phase 0: AI Native Visionary Requirement Elevation**
  - 7-step visionary process for requirement elevation
  - Two-dimensional solution output (AI-Enhanced vs AI-Native)
  - Five-dimensional assessment framework
  - Extreme constraint breakthrough (4 types)
  - Anti-consensus design methodology
  - AI Native Requirements specification

- **Capability-Evolver Integration**
  - Integrated capability-evolver skill for self-improvement
  - MEMORY.md for knowledge persistence
  - Evolution tracking and rollback capability

- **Enhanced Documentation**
  - README_V3.md with comprehensive usage guide
  - MAD_DOG_MODE.md for evolver configuration
  - CHANGELOG.md for version tracking

- **Auto-Update System**
  - Startup version checking for all nested skills
  - Automatic download and installation of updates
  - Version change logging

- **Version Control & Snapshots**
  - Snapshot creation before each phase
  - Version comparison tools
  - One-click rollback capability

### Changed
- Renamed from "8-phase workflow" to "13-phase workflow"
- Updated core philosophy from "Think First, Code Later" to "AI-Native Visionary Driven"
- Enhanced description with AI-native focus
- Improved phase transition logic

### Fixed
- Phase numbering and transitions
- Integration with ai-native-vision skill
- Documentation clarity and completeness

### Technical
- SKILL.md size: 28KB (comprehensive guidance)
- Package size: 27.5 KB
- Dependencies: 10+ integrated skills
- Compatible with Claude Code latest version

## [2.0.0] - 2026-02-12

### Added
- **12-Phase Autonomous Workflow**
  - Phase 1: Feasibility Check (CC-FPS) - Highest Priority
  - Phase 2: GitHub Discovery - Second Priority
  - Phase 3: Knowledge Base - Third Priority
  - Phase 4: Requirements Engineering
  - Phase 5-5b: Architecture & Design
  - Phase 6: WBS (Work Breakdown Structure)
  - Phase 7: Project Initialization
  - Phase 8: Autonomous Development - Zero User Interaction
  - Phase 9: QA (Quality Assurance)
  - Phase 10: Ralph Loop Optimization - 10 Iterations
  - Phase 11: Deployment
  - Phase 12: Project Summary

- **Three Interaction Points Model**
  - Initial requirement input
  - Requirement confirmation (Phase 4)
  - Complete development plan confirmation

- **GitHub Discovery Integration**
  - Automated search for existing open-source solutions
  - Clone and adapt strategy
  - Decision matrix for build vs. buy

- **Auto-Update & Version Control**
  - Automatic skill version checking
  - Snapshot creation and rollback
  - Version metadata tracking

- **Self-Evolution Capability**
  - Integration with self-evolving-skill
  - Pattern learning from projects
  - Continuous workflow optimization

- **Helper Scripts**
  - auto_update.py - Version management
  - init_project.py - Project initialization
  - package_skill.py - Skill packaging

### Changed
- Complete rewrite from V1.0
- New description: "AI-Native 13-phase development orchestrator"
- Enhanced integration with specialized skills
- Improved autonomous execution model

### Technical
- Package size: 23.4 KB
- 10 integrated skills
- Full TDD workflow support
- Production-grade delivery

## [1.0.0] - 2026-02-12

### Added
- **Initial Release**
  - 8-phase development workflow
  - Basic project structure
  - Template documentation
  - Manual execution model

### Features
- Phase 0-7: Basic development phases
- Manual progress tracking
- Basic documentation templates

### Technical
- SKILL.md: ~8KB
- Package size: ~15 KB
- Minimal dependencies

---

## Version Naming Convention

- **Major (X.0.0)**: Breaking changes, new features, paradigm shifts
- **Minor (x.X.0)**: New features, enhancements, backward compatible
- **Patch (x.x.X)**: Bug fixes, documentation, small improvements

---

## Migration Guide

### From V2.0 to V3.0

**Breaking Changes**: None - backward compatible

**New Features**:
- Add Phase 0 before starting any project
- Use AI-native vision framework for requirement analysis
- Evaluate solutions using 5-dimensional framework

**Recommended Actions**:
1. Update auto_update.py to include capability-evolver
2. Review Phase 0 documentation
3. Run capability-evolver in mad-dog mode for continuous improvement
4. Create MEMORY.md for each project

### From V1.0 to V2.0

**Breaking Changes**: Phase numbering changed

**New Features**:
- Phase 1-3 renumbered (was 0-2)
- New Phase 1: Feasibility Check
- New Phase 2: GitHub Discovery
- Autonomous execution after Phase 4

**Migration**: Use new phase numbers, same core philosophy

---

## Future Roadmap

### V3.1 (Planned)
- Enhanced Phase 0 with more breakthrough patterns
- Multi-project support
- Real-time metrics dashboard

### V4.0 (Exploring)
- Multi-user collaboration workflows
- Automated cloud deployment
- Advanced analytics and reporting

---

## Contributors

- **Claude Code & User** - Core development and evolution
- **capability-evolver** - Self-improvement engine

---

## License

MIT License - See LICENSE file for details

---

## Archive

### [Unreleased]
- No changes yet
