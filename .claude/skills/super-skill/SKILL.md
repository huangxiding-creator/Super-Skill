---
name: super-skill
description: AI-Native 14-phase development orchestrator with comprehensive production-grade capabilities. Use when users request full-stack development, complex products, or systematic execution: (1) AI-native requirement transformation and breakthrough thinking, (2) Autonomous 14-phase lifecycle from visionary elevation to delivery, (3) Zero-UI/Zero-Click paradigm with AI-first architecture, (4) Self-updating and version-controlled ecosystem, (5) Multi-agent orchestration (LangGraph/AutoGen/CrewAI), (6) Advanced reasoning (CoT/ToT/GoT), (7) Darwin Gödel Machine self-evolution, (8) MCP protocol integration, (9) CI/CD automation with GitHub Actions, (10) Security scanning (SAST/SCA), (11) Performance optimization patterns, (12) Error recovery & resilience, (13) Context management & memory, (14) REST/GraphQL API patterns, (15) Testing automation (TDD/E2E/Mutation), (16) Database & data patterns, (17) State management, (18) Monitoring & observability, (19) Accessibility (WCAG), (20) Code transformation (AST/codemods), (21) Real-time WebSockets, (22) Internationalization (i18n), (23) Prompt engineering, (24) Search & indexing. Core principle: Visionary Elevation (Phase 0) → Feasibility Analysis (Phase 1) → GitHub Discovery (Phase 2) → Skills Discovery (Phase 2b) → Knowledge Base (Phase 3) → Requirements (Phase 4) → Design (Phase 5-5b) → WBS (Phase 6) → Autonomous Development (Phase 8) → QA (Phase 9) → Ralph Loop 10x (Phase 10) → Deployment (Phase 11) → Summary & Evolution (Phase 12). Integrates 25+ specialized skills for production-grade AI-native delivery.
---

# Super-Skill V3.7: Comprehensive AI-Native Development Orchestrator

## Core Philosophy: "Think First, Code Later"

**Principle**: Maximize upfront thinking, minimize rework and iterations.

**Execution Model**: Three user interaction points only:
1. **Initial Requirement Input** - User provides what they want
2. **Requirement Confirmation** - User validates refined requirements
3. **Complete Development Plan Confirmation** - User approves autonomous execution plan

**After Confirmation**: Zero user interaction. Claude Code executes all 12 phases autonomously using best practices, GitHub discoveries, and intelligent decision-making.

---

## Auto-Update & Version Control

### Startup Sequence

每次 Super-Skill 启动时自动执行：

```
STEP 1: Check for Updates
Execute: python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py check

This checks:
- Super-Skill version
- All nested skills versions:
   * capability-evolver (CRITICAL - must be installed)
   * claude-mem (CRITICAL - must be installed for persistent memory)
   * find-skills (CRITICAL - must be installed for skills discovery)
   * feasibility-check
   * github-discovery
   * continuous-learning-v2
   * skill-version-manager
   * self-evolving-skill
   * ai-native-vision
   * tdd-workflow
   * security-review
   * code-review
   * refactor-clean
   * And all other referenced skills
- If updates available: Auto-download and install
- Log version changes

STEP 2: Verify Capability-Evolver
Execute: python C:\Users\91216\.claude\skills\super-skill\scripts\check_evolver.py

This verifies:
- Capability-Evolver is installed at C:\Users\91216\.claude\skills\capability-evolver
- Evolver is functional
- Required dependencies available
- Configuration files present (.env, .env.mad-dog)
- If missing: Prompt user to install evolver

STEP 3: Start Claude-Mem Worker (NEW)
Execute: Auto-start if CLAUDE_MEM_AUTO_START=true

This does:
- Start Claude-Mem worker service
- Verify memory database is accessible
- Enable persistent memory across sessions
- If missing: Prompt user to install claude-mem

STEP 4: Retrieve Relevant Memories (NEW)
Execute: Automatic via Claude-Mem

This retrieves:
- Past project decisions and rationale
- Successful patterns from previous projects
- Lessons learned and mistakes to avoid
- Technical preferences and conventions
- Context-aware memory injection

STEP 5: Inject Context into Session (NEW)
Execute: Automatic via Claude-Mem

This injects:
- Relevant historical context
- Project-specific memories
- Architecture decisions from similar projects
- Code patterns that worked well
- Optimizations that failed (and why)

STEP 6: Create Version Snapshot
Execute: python C:\Users\91216\.claude\skills\super-skill\scripts\auto_update.py snapshot <project-dir>

This creates:
- Snapshot with timestamp
- All skill versions captured
- Enables rollback capability
- Stored in .snapshots/ directory

STEP 7: Start Workflow
- Proceed with Phase 0 (AI Native Visionary)
- All versions logged for reference
- Historical context available from Claude-Mem
- Rollback available if needed
```

### Version Management

使用 `skill-version-manager` 进行：
- 快照创建（每个phase开始前）
- 版本对比
- 一键回撤到任意版本点
- 版本元数据记录（时间、原因、结果）

### Self-Evolution

使用 `self-evolving-skill` 实现：
- 每次项目执行后自动学习
- 提取成功模式和失败教训
- 更新技能知识库
- 进化决策逻辑
- 持续优化工作流

---

## 14-Phase Autonomous Workflow

### Phase Interaction Model

```
User Input → Phase 1-3 (Planning) → User Confirmation →
Phase 4-12 (Autonomous Execution) → Delivery
```

**关键规则**：
- Phase 1-3: 需求分析和可行性检查阶段，可以询问用户
- Phase 4开始后：零用户交互，完全自主决策和执行
- 所有决策基于：最佳实践、GitHub发现、技术可行性、质量标准

---

## Phase 0: AI Native Visionary Requirement Elevation - **PRE-PHASE ZERO**

### Core Concept

**扮演AI原生产品架构师，将用户初步需求升维为AI原生需求**

在进入传统可行性检查之前，先进行"大胆想象"和"需求升维"，识别AI原生机会，突破传统产品范式约束。

### Objectives

- 分析项目涉及的AI技术（LLM/Agent/RAG/多模态）最新能力边界
- 识别传统解决方案的"AI改造点"和"AI原生重构点"
- 提出AI增强版和AI原生版两维度方案
- 通过双维度深度追问挖掘技术决策点和体验创新点
- 针对极端约束设计突破性方案
- 质疑行业常识，提出突破性路径
- 输出《AI原生需求规格书》

### Process

#### Step 1: Worldview Establishment (世界观建立)

```
Analysis Framework:
1. AI Technology Boundaries:
   - LLM Capabilities:
     * Context window limits
     * Reasoning capabilities
     * Tool use capabilities
     * Multi-modal abilities (vision, audio, code)
   - Agent Capabilities:
     * Autonomous execution
     * Multi-agent orchestration
     * Tool integration
     * Memory and state management
   - RAG Capabilities:
     * Knowledge base size
     * Retrieval accuracy
     * Update frequency
   - Multi-modal Capabilities:
     * Image understanding
     * Voice interaction
     * Real-time processing

2. Traditional "AI Retrofit Points":
   - Traditional features that can be AI-enhanced:
     * Rule-based systems → LLM reasoning
     * Static menus → Dynamic AI-driven UI
     * Manual workflows → Autonomous agent loops
     * Passive responses → Proactive AI assistance
     * Batch operations → Real-time AI processing

3. AI Native Refactoring Points:
   - Opportunities for complete AI-first redesign:
     * Remove UI entirely (AI conversation interface)
     * Agent-based autonomous execution
     * Predictive vs reactive approaches
     * Multi-agent collaboration
     * Self-learning and adaptation
```

#### Step 2: Two-Dimensional Solution Output (两维度方案输出)

```
Dimension 1: AI-Enhanced Version (AI增强版)
Approach:
- Keep familiar user patterns
- Add AI intelligence layer
- Traditional UI + AI backend
- Gradual AI enhancement

Technical Feasibility: 9/10 (High - relies on existing patterns)
Sharpness Score: 6/10 (Moderate - keeps familiarity)
Example:
- Traditional task management app
- Add AI-powered smart suggestions
- Keep familiar list/table interface
- Add LLM-based task prioritization
- AI helps fill forms, suggests next actions

Dimension 2: AI-Native Version (AI原生版)
Approach:
- Zero-UI / Pure conversation interface
- Full agent autonomy
- RAG + LLM + Multi-agent
- Break all traditional assumptions

Technical Feasibility: 7/10 (Medium - high technical risk)
Sharpness Score: 10/10 (Revolutionary - completely new paradigm)
Example:
- "Talk to your AI to manage tasks"
- No UI, just voice/text conversation
- AI agents proactively manage tasks
- Learns user patterns over time
- Predicts needs before user asks
```

#### Step 3: Dual-Dimension Deep Inquiry (双维度深度追问)

```
Technical Dimension (Identify All Manual Decision Points):
For each ambiguous area:
1. Question: "What are the technical implementation options?"
2. Question: "What are the trade-offs of each option?"
3. Question: "Can AI agents make this decision autonomously?"
4. Question: "What data would inform this decision?"
5. Question: "Are there monitoring points for validating this choice?"

Goal: Transform manual decisions into autonomous AI decisions

Experience Dimension (Explore "Zero UI" & "Conversation Interface"):
1. "Aha Moment" Design (3 seconds):
   - User realizes something they want
   - AI already suggested/provided it
   - Delight through anticipation

2. Zero-Learning-Cost Interaction:
   - Remove all traditional "sign up", "configure", "setup" flows
   - AI learns from first interaction
   - User states intent, AI executes immediately
   - Example: "I need to report expenses" → AI: "Done. Added to report. Next?"

3. "Invisible Assistant" Active Service:
   - Background AI agents working proactively
   - User doesn't trigger, AI acts
   - Examples:
     * Calendar: AI proposes meetings before conflicts
     * Email: AI drafts responses, asks to send
     * Tasks: AI completes tasks when it detects user is blocked

Target: Replace explicit user actions with invisible AI proactivity
```

#### Step 4: Extreme Constraint Breakthrough (极端约束突破)

```
Constraint Breakthrough Framework:

1. Zero-Click / Pure Voice or Text:
   Breakthrough: Remove ALL manual navigation
   Implementation: Voice-first interface (text-to-speech + speech-to-text)
   AI Interpretation: Infers intent from natural language
   Fallback: Text input for noisy environments
   Technical Feasibility: 8/10 (Challenging - voice UI precision)
   Sharpness: 9/10 (Very High - paradigm shift)

2. One-Second First Feedback:
   Breakthrough: Real-time AI adaptation
   Implementation: AI observes behavior, adjusts <1s
   User correction shapes next action immediately
   No "submit" buttons - continuous AI listening
   Technical Feasibility: 6/10 (Medium - real-time ML challenge)
   Sharpness: 10/10 (Maximum - breaks interaction model)

3. Zero-Config / Self-Learning System:
   Breakthrough: Remove ALL configuration screens
   Implementation: AI learns preferences from first interaction
   Discovers optimal setup automatically
   Adapts over time without user intervention
   Technical Feasibility: 5/10 (Low - high ML complexity)
   Sharpness: 9/10 (Very High - eliminates onboarding)

4. Eliminate Traditional Concepts:
   Breakthrough: Remove "save", "submit", "confirm" paradigms
   Implementation: AI commits when confident, asks when uncertain
   Continuous AI evaluation and auto-commit
   Technical Feasibility: 7/10 (Medium - conceptual change)
   Sharpness: 8/10 (High - significant UX shift)
```

#### Step 5: Anti-Consensus Design (反共识设计)

```
Industry Common Dogmas to Question:

1. "Users need clear visual hierarchy"
   Challenge: AI conversation can provide hierarchy through context
   Alternative: Dynamic importance based on user intent and AI inference

2. "Navigation must be consistent and visible"
   Challenge: AI can infer context and provide relevant next actions
   Alternative: Intent-driven dynamic interface

3. "Feedback must be explicit and user-initiated"
   Challenge: AI can infer satisfaction from behavior and patterns
   Alternative: Proactive satisfaction detection and adjustment

4. "Complex systems need step-by-step wizards"
   Challenge: Multi-agent AI can handle complexity autonomously
   Alternative: Agent collaboration with user oversight only on request

5. "Error messages must be user-friendly"
   Challenge: AI can explain and auto-fix in natural language
   Alternative: Autonomous resolution with transparent explanation

Breakthrough Paths:
- Question each "industry standard"
- Identify when it doesn't apply to AI-native context
- Propose AI-first alternative
- Document突破性 rationale
```

#### Step 6: AI Native Assessment (AI原生评估)

```
Five-Dimensional Scoring Framework (评估最终方案):

Dimension 1: Autonomy (自主性) - 0-10
- 0: Fully manual (user decides everything)
- 3: Mostly manual (some AI suggestions)
- 5: Hybrid (user + AI collaboration)
- 7: Mostly autonomous (AI acts, user approves)
- 9: Fully autonomous (AI decides, user only intervenes on exceptions)

Dimension 2: Intelligence (智能性) - 0-10
- 0: Rule-based
- 3: Pattern matching
- 5: LLM reasoning
- 7: Multi-agent reasoning
- 9: Self-learning AI
- 10: AGI-level intelligence

Dimension 3: Progressiveness (先进性) - 0-10
- 0: Conservative (proven tech only)
- 3: Moderate (some new elements)
- 5: Advanced (significant innovation)
- 7: Very advanced (cutting-edge)
- 9: Revolutionary (paradigm shift)
- 10: Science-fiction-like (theoretical breakthrough)

Dimension 4: Integration (融合度) - 0-10
- 0: Standalone (no integration)
- 3: Point integrations
- 5: Platform integration
- 7: Multi-platform ecosystem
- 9: Universal integration layer

Dimension 5: Simplicity (简洁性) - 0-10
- 0: Complex (many steps, many decisions)
- 3: Moderate (standard complexity)
- 5: Simple (minimal user input)
- 7: Very simple (near-zero steps)
- 9: Zero-step (AI handles everything)

Scoring Method:
For each solution, rate 0-10 on all 5 dimensions
Calculate: (Autonomy + Intelligence + Progressiveness + Integration + Simplicity) / 5
Target: Score ≥ 7/10 (AI-Native threshold)
Report scores with justification
```

#### Step 7: Output AI Native Specification (输出AI原生需求规格书)

```
Create AI_NATIVE_REQUIREMENTS.md:

Section 1: User Intent Prediction Layer (用户意图预测层)
- User's stated goals
- Inferred unmet needs
- Predicted future needs
- Pattern recognition for user behavior

Section 2: Autonomous Decision Engine (自主决策引擎)
- Decision points identified for AI autonomy
- Data sources for each decision
- Fallback strategies
- Human escalation triggers

Section 3: Adaptive Interface Layer (自适应界面层)
- Zero-UI / Conversation-primary approach
- Dynamic interface generation based on context
- Multi-modal interaction (voice, text, vision)
- Implicit preference learning

Section 4: Magic Moment Design (魔法时刻设计)
- Points of delight in user journey
- "Aha moments" - AI anticipates needs
- Surprise and delight mechanisms
- Serendipitous assistance

Section 5: Technical Architecture Requirements
- LLM choice and integration
- Agent architecture and orchestration
- RAG system and knowledge base
- Multi-modal capabilities
- Performance requirements
```

### Interaction Design

```
After presenting AI Native Visionary analysis:

Ask user: "是否需要再激进一点？推进到AI原生方案？
Options:
1. 保守：选择AI增强版（保持传统界面+AI增强）
2. 激进：选择AI原生版（零UI/纯对话/多Agent）

或者让用户提出自己的想法，然后进入Phase 1传统可行性检查。
```

### Deliverables

- `AI_NATIVE_REQUIREMENTS.md` - AI原生需求规格书
- Technical feasibility assessment for both solution dimensions
- Sharpness scoring and recommendations
- Breakthrough opportunity identification

### Next Phase Trigger

**After user decision on approach**:
- If AI-Native chosen: Skip to Phase 7 (Project Init) with AI-native architecture
- If traditional approach: Proceed to Phase 1 (Feasibility Check) for detailed analysis

**Integration Note**:
This phase uses `ai-native-vision` skill for visionary analysis and breakthrough thinking.

---

## Phase 1: Feasibility Check (CC-FPS) - **HIGHEST PRIORITY** (Traditional Path)

### Trigger
用户提出任何开发需求时立即启动。

### Objectives
- 评估技术可行性
- 评估经济可行性
- 评估运营可行性
- 评估时间可行性
- 识别关键风险和阻塞因素

### Process

#### 1.1 Execute Feasibility Analysis
```
Use feasibility-check skill:
- Technical feasibility: Can it be built with current tech?
- Economic feasibility: Cost-benefit analysis
- Operational feasibility: Can it be maintained/operated?
- Scheduling feasibility: Timeline realistic?
- Risk assessment: What could go wrong?
```

#### 1.2 Generate Feasibility Report
```
Create FEASIBILITY_REPORT.md:

Executive Summary:
- Overall feasibility score (0-100)
- Go/No-Go recommendation

Technical Analysis:
- Required technologies and availability
- Technical risks and mitigation
- Complexity assessment
- Resource requirements

Economic Analysis:
- Cost estimates (development, maintenance, infrastructure)
- ROI projection
- Break-even analysis
- Cost-benefit ratio

Operational Analysis:
- Maintenance requirements
- Operational complexity
- Support needs
- Training requirements

Scheduling Analysis:
- Realistic timeline estimation
- Critical path identification
- Milestone projections
- Buffer requirements

Risk Assessment:
- High/Medium/Low risk items
- Probability × Impact scoring
- Mitigation strategies for each risk
- Contingency plans

Recommendation:
- Go / No-Go / Conditional-Go
- Required conditions (if conditional)
- Critical success factors
```

### Gate Checks
- [ ] Feasibility score ≥ 60/100 (or user explicitly accepts risk)
- [ ] All critical risks identified with mitigation plans
- [ ] Technical feasibility confirmed
- [ ] Economic viability established
- [ ] Timeline is realistic

### Deliverables
- `FEASIBILITY_REPORT.md`
- Risk register with mitigation strategies
- Go/No-Go decision

### Next Phase Trigger
**IF** feasibility score < 60:
- Stop and present findings to user
- Request user decision on how to proceed

**IF** feasibility score ≥ 60:
- Auto-proceed to Phase 2 (GitHub Discovery)

---

## Phase 2: GitHub Discovery - **SECOND PRIORITY**

### Objectives
- 搜索现有开源解决方案
- 评估最佳实践
- 克隆并适配现有项目（如适用）
- 决定：复制 vs 从头开发

### Process

#### 2.1 Search GitHub
```
Use github-discovery skill:
1. Search for projects matching user requirements
2. Analyze top candidates:
   - Stars, forks, recent activity
   - Code quality
   - Technology stack match
   - License compatibility
   - Community support
3. Clone top 3 candidates for detailed analysis
```

#### 2.2 Evaluation Framework
```
For each candidate, evaluate:

Fit Analysis:
- Feature coverage (% of requirements met)
- Customization effort required
- Integration complexity
- Learning curve

Quality Analysis:
- Code quality (linting, patterns)
- Test coverage
- Documentation quality
- Security practices
- Performance characteristics

Adaptation Analysis:
- License allows modification?
- Architecture compatible?
- Dependencies acceptable?
- Maintenance burden?
```

#### 2.3 Decision Matrix
```
Create GITHUB_DISCOVERY_REPORT.md:

Option A: Clone & Adapt [Project Name]
- Feasibility: 0-100 score
- Coverage: X% of requirements
- Adaptation effort: [Low/Med/High]
- Recommendation: [Accept/Reject]

Option B: Hybrid Approach
- Base: [Project Name]
- Custom features: [List]
- Integration complexity: [Low/Med/High]
- Recommendation: [Accept/Reject]

Option C: Build from Scratch
- Rationale: [Why no suitable project found]
- Technology stack: [Selected]
- Estimated effort: [Time/Complexity]
- Recommendation: [Accept/Reject]

DECISION: [Selected Option]
Justification: [Detailed reasoning]
```

### Gate Checks
- [ ] GitHub search completed with adequate coverage
- [ ] Top candidates analyzed in detail
- [ ] Decision matrix created with clear recommendation
- [ ] License compatibility verified (if cloning)
- [ ] Adaptation effort is reasonable

### Deliverables
- `GITHUB_DISCOVERY_REPORT.md`
- Cloned repositories (if applicable)
- Decision record with rationale

### Next Phase Trigger
**IF** suitable GitHub project found (≥80% requirements coverage):
- Clone and setup base project
- Auto-proceed to Phase 4 (Requirements - with base context)

**IF** no suitable project found:
- Auto-proceed to Phase 2b (Skills Discovery)

---

## Phase 2b: Skills Discovery - **CAPABILITY EXTENSION**

### Objectives
- 搜索开放技能生态系统中的现有技能
- 识别可扩展Agent能力的专业技能
- 自动安装高相关性技能
- 决定：使用现有技能 vs 自行开发

### Trigger
- Phase 2 (GitHub Discovery) 未找到合适项目
- 项目需要特定领域专业知识
- 用户请求扩展Agent能力

### Process

#### 2b.1 Identify Required Capabilities
```
Analyze project requirements:
1. Review FEASIBILITY_REPORT.md from Phase 1
2. List required technical domains:
   - Frontend frameworks (React, Vue, Angular)
   - Backend technologies (Node.js, Python, Go)
   - Databases (PostgreSQL, MongoDB, Redis)
   - DevOps (Docker, Kubernetes, CI/CD)
   - Testing (Jest, Playwright, Cypress)
   - Security (Authentication, Encryption)
   - Documentation (API docs, README)
   - Design (UI/UX, Accessibility)
3. Map domains to potential skills
4. Prioritize by project criticality
```

#### 2b.2 Search Skills Ecosystem
```
Use find-skills skill:

For each required domain:
1. Execute: npx skills find <domain> <task>
2. Collect and analyze results
3. Score each candidate:
   - Relevance: 0-100 (matches requirements)
   - Quality: 0-100 (documentation, tests)
   - Maintenance: 0-100 (recent updates, issues)
   - License: Compatible? (MIT, Apache, etc.)
   - Integration: Easy/Medium/Hard

Example searches:
- "react performance" → vercel-react-best-practices
- "testing e2e" → playwright-testing
- "security review" → security-review
- "api documentation" → api-docs-generator
```

#### 2b.3 Evaluate and Select Skills
```
For each candidate skill:

Evaluation Criteria:
- Feature Coverage: % of domain requirements met
- Installation Complexity: npm/npx/golang/etc.
- Documentation Quality: README, examples, API docs
- Community Support: stars, forks, issues
- Last Update: Within 6 months?
- License: Permissive enough?

Scoring:
Total Score = (Relevance × 0.4) + (Quality × 0.3) + (Maintenance × 0.2) + (Integration × 0.1)

Decision:
- Score ≥ 80: Auto-install
- Score 60-79: Present to user for approval
- Score < 60: Skip, document gap
```

#### 2b.4 Install Selected Skills
```
Auto-install high-scoring skills:

For skills with Score ≥ 80:
1. Execute: npx skills add <skill-ref> -g -y
2. Verify installation
3. Update project context
4. Log to SKILLS_DISCOVERY_REPORT.md

Example:
npx skills add vercel-labs/agent-skills@vercel-react-best-practices -g -y
npx skills add anthropics/skills@security-review -g -y
```

#### 2b.5 Generate Skills Discovery Report
```
Create SKILLS_DISCOVERY_REPORT.md:

Executive Summary:
- Total skills searched: X
- Skills found: Y
- Skills installed: Z
- Coverage improvement: +N%

Installed Skills:
| Skill Name | Source | Score | Purpose |
|------------|--------|-------|---------|
| vercel-react-best-practices | vercel-labs | 92 | React performance |
| security-review | anthropics | 88 | Security scanning |

Pending Skills (User Review):
| Skill Name | Score | Reason |
|------------|-------|--------|
| advanced-testing | 72 | Complex setup |

Gaps Identified:
- No suitable skill found for: [domain]
- Recommendation: Build custom or create new skill

Integration Notes:
- [Skill A] requires configuration: [details]
- [Skill B] conflicts with: [details]
```

### Gate Checks
- [ ] Skills ecosystem searched for all required domains
- [ ] Candidate skills evaluated and scored
- [ ] Critical skills (≥80% relevance) auto-installed
- [ ] SKILLS_DISCOVERY_REPORT.md generated
- [ ] Integration recommendations documented
- [ ] Version snapshot created before skill installations

### Deliverables
- `SKILLS_DISCOVERY_REPORT.md` - Comprehensive skills analysis
- Installed skills ready for use
- Updated project context with new capabilities
- Gap analysis for missing capabilities

### Next Phase Trigger
**IF** skills installed successfully:
- Update project capabilities
- Auto-proceed to Phase 3 (Knowledge Base)

**IF** critical gaps remain:
- Document gaps in SKILLS_DISCOVERY_REPORT.md
- Flag for potential skill creation in Phase 12
- Auto-proceed to Phase 3 (Knowledge Base)

**Integration Note**:
This phase uses `find-skills` skill (integrated from Vercel Labs) for skills ecosystem discovery and installation.

---

## Phase 3: Knowledge Base - **THIRD PRIORITY**

### Objectives
- 建立项目领域知识库
- 收集最佳实践和模式
- 记录技术决策和依据
- 准备开发环境

### Process

#### 3.1 Use Continuous Learning
```
Invoke continuous-learning-v2 skill:
- Scan project domain for patterns
- Collect best practices from multiple sources
- Build domain-specific knowledge base
- Create reusable instincts and patterns
```

#### 3.2 Establish Knowledge Base
```
Create KNOWLEDGE_BASE.md:

Domain Understanding:
- Core concepts and terminology
- Business rules and constraints
- Domain-specific patterns
- Common pitfalls and solutions

Technology Decisions:
- Selected stack with rationale
- Alternative technologies considered
- Trade-offs and justifications
- Version selections

Best Practices:
- Architecture patterns for this domain
- Security requirements
- Performance considerations
- Testing strategies
- Deployment patterns

Reference Resources:
- Official documentation links
- Best practice guides
- Community resources
- Example implementations
```

#### 3.3 Environment Preparation
```
Setup development environment:
- Install required tools and dependencies
- Configure development databases/services
- Setup linting, formatting, testing infrastructure
- Create project skeleton (if starting from scratch)
```

### Gate Checks
- [ ] Domain knowledge base established
- [ ] Technology stack decisions documented
- [ ] Best practices collected and organized
- [ ] Development environment configured and tested
- [ ] All tools and dependencies installed

### Deliverables
- `KNOWLEDGE_BASE.md`
- Configured development environment
- Project skeleton (if starting from scratch)
- Tool configuration files

### Next Phase Trigger
Auto-proceed to Phase 4 (Requirements Engineering).

---

## Phase 4: Requirements Engineering

### Objectives
- 将用户需求转化为精确规格
- 定义验收标准
- 识别所有边界情况
- 建立可追溯性

### Interaction Point 2: **REQUIREMENT CONFIRMATION**

这是用户三个交互点中的第二个。需要用户确认需求。

### Process

#### 4.1 Elicit Requirements (Interactive)
```
Engage user for requirement refinement:
- Ask clarifying questions
- Present use case scenarios
- Validate understanding
- Identify edge cases
- Document constraints
```

#### 4.2 Structure Requirements
```
Create REQUIREMENTS.md:

User Personas:
- Roles and goals
- Pain points and needs
- Skill levels and context

Functional Requirements:
- Prioritized features (MoSCoW: Must/Should/Could/Won't)
- User stories with acceptance criteria
- Feature descriptions and specifications
- Edge cases and error scenarios

Non-Functional Requirements:
- Performance (response times, throughput)
- Security (authentication, authorization, data protection)
- Scalability (user load, data volume)
- Usability (accessibility, responsiveness)
- Reliability (uptime, error rates)
- Maintainability (code quality, documentation)

Constraints:
- Technical constraints (platform, compatibility)
- Business constraints (budget, timeline, resources)
- Regulatory constraints (compliance, standards)
- Team constraints (skills, availability)

Acceptance Criteria:
- Specific, measurable criteria for each feature
- Definition of Done for each user story
- Test scenarios for validation
```

#### 4.3 Requirements Review
```
Present to user for confirmation:
- Complete requirements specification
- All features listed with priorities
- All constraints documented
- Estimated timeline and effort
```

### Gate Checks
- [ ] User requirements fully captured
- [ ] All requirements are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- [ ] Acceptance criteria defined for each feature
- [ ] Edge cases and constraints identified
- [ ] Requirements prioritized (MoSCoW)
- [ ] **User explicitly confirms requirements**

### Deliverables
- `REQUIREMENTS.md`
- User story map
- Requirements traceability matrix template
- **User confirmation received**

### Next Phase Trigger
**AFTER USER CONFIRMS REQUIREMENTS**:
- Auto-proceed to Phase 5 (Architecture & Design)

---

## Phase 5: Architecture Design

### Objectives
- 设计系统架构
- 选择技术栈
- 定义接口和数据模型
- 确保可扩展性和性能

### Process

#### 5.1 Architecture Decision Making
```
Use architect agent and skill-from-masters:
- Analyze requirements for architectural drivers
- Select appropriate architectural patterns
- Choose technology stack
- Define component structure
- Design integration approaches
```

#### 5.2 Create Architecture Artifacts
```
Generate design documentation:

ARCHITECTURE.md:
- System context and boundaries
- Component architecture
- Data flow diagrams
- Sequence diagrams for key flows
- Technology stack with rationale
- Quality attribute scenarios (performance, security, scalability)
- Deployment architecture

API_DESIGN.md (if applicable):
- REST/GraphQL endpoint specifications
- Request/response schemas
- Authentication/authorization design
- Error handling strategy
- Rate limiting approach
- Versioning strategy

DATABASE_SCHEMA.md (if applicable):
- Entity-relationship diagram
- Table definitions with types/constraints
- Indexes for performance
- Migration strategy
- Data retention policies
```

#### 5.3 Design Validation
```
Self-review architecture:
- Satisfies all functional requirements
- Meets non-functional requirements
- Security best practices applied
- Performance characteristics modeled
- Scalability path clear
- Operational concerns addressed (logging, monitoring, alerting)
```

### Gate Checks
- [ ] Architecture documented completely
- [ ] Technology stack selected and justified
- [ ] All functional requirements addressed
- [ ] All non-functional requirements addressed
- [ ] Security and compliance requirements met
- [ ] Performance path validated
- [ ] Architecture is self-consistent

### Deliverables
- `ARCHITECTURE.md`
- `API_DESIGN.md` (if applicable)
- `DATABASE_SCHEMA.md` (if applicable)
- Architecture decision records

### Next Phase Trigger
Auto-proceed to Phase 5b (Detailed Design).

---

## Phase 5b: Detailed Design

### Objectives
- 细化组件设计
- 定义类/函数接口
- 设计数据结构
- 规划实现细节

### Process

#### 5b.1 Component Design
```
Create detailed design for each component:
- Class/interface signatures
- Method signatures with parameters and returns
- Data structures and models
- Error handling approach
- Logging and monitoring points
```

#### 5b.2 Integration Design
```
Define integration approach:
- Internal component communication
- External service integration
- Data flow between components
- State management strategy
- Caching strategy
```

### Gate Checks
- [ ] All components designed with clear interfaces
- [ ] Data structures defined
- [ ] Integration approach clear
- [ ] Implementation details sufficient for coding

### Deliverables
- Detailed design specifications for each component
- Integration flow diagrams
- Data structure definitions

### Next Phase Trigger
Auto-proceed to Phase 6 (WBS - Work Breakdown Structure).

---

## Phase 6: WBS (Work Breakdown Structure)

### Objectives
- 创建详细工作分解
- 识别任务依赖关系
- 估算工作量
- 规划里程碑

### Process

#### 6.1 Create WBS
```
Use planner agent:
Break down project into:
- Phases and major deliverables
- Features and components
- Tasks (4-16 hours each)
- Subtasks (if needed for clarity)

For each task:
- Description and acceptance criteria
- Dependencies (prerequisite tasks)
- Estimated effort (hours)
- Assigned skill/agent (for autonomous execution)
- Deliverables
```

#### 6.2 Dependency Analysis
```
Create task dependency graph:
- Critical path identification
- Parallelizable tasks
- Blockers and risks
- Sequencing requirements
```

#### 6.3 Scheduling
```
Create schedule:
- Task sequence with dependencies
- Milestone definitions
- Buffer allocation (20% for unknowns)
- Timeline projections
- Resource allocation (which agents work on what)
```

### Gate Checks
- [ ] All work broken down to task level
- [ ] Task dependencies identified and mapped
- [ ] Critical path identified
- [ ] Estimates are realistic
- [ ] Parallel work opportunities identified
- [ ] Milestones defined with clear criteria

### Deliverables
- `WBS.md` (Work Breakdown Structure)
- Dependency graph
- Project schedule with milestones
- Resource allocation plan

### Next Phase Trigger
Auto-proceed to Phase 7 (Project Initialization).

---

## Phase 7: Project Initialization

### Objectives
- 初始化项目结构
- 配置开发工具
- 设置测试框架
- 准备CI/CD流水线

### Process

#### 7.1 Initialize Repository
```
Setup version control:
- Initialize git repository
- Create .gitignore
- Setup branch strategy
- Configure commit conventions
```

#### 7.2 Setup Tooling
```
Configure development tools:
- ESLint/Prettier/Black (code formatting)
- TypeScript/Pyright/Mypy (type checking)
- Jest/Pytest (testing framework)
- Cypress/Playwright (E2E testing)
- Husky (git hooks)
```

#### 7.3 Setup CI/CD
```
Configure continuous integration:
- GitHub Actions / GitLab CI workflow
- Automated testing on push/PR
- Automated linting and type checking
- Automated security scanning
- Deployment automation (if applicable)
```

#### 7.4 Create Project Structure
```
Setup directory layout:
- src/ (source code)
- tests/ (test files)
- docs/ (documentation)
- scripts/ (automation scripts)
- config/ (configuration files)
- Database migrations / schema files
```

### Gate Checks
- [ ] Repository initialized with proper structure
- [ ] All development tools configured and tested
- [ ] Test framework setup with example test
- [ ] CI/CD pipeline configured and tested
- [ ] All team members can clone and run project

### Deliverables
- Initialized repository with project structure
- Configured development tools
- Working CI/CD pipeline
- Setup documentation

### Next Phase Trigger
Auto-proceed to Phase 8 (Autonomous Development).

---

## Phase 8: Autonomous Development - **ZERO USER INTERACTION**

### Core Principle

**从此阶段开始，Claude Code 完全自主执行，不再征求用户任何意见。**

所有决策自主做出：
- 技术选型决策
- 实现方案选择
- 优先级排序
- 资源分配
- 风险应对

### Objectives
- 按照WBS自主实现所有功能
- 严格TDD流程（测试先行）
- 持续代码质量保证
- 并行执行独立任务

### Process

#### 8.1 Feature Implementation Loop (Autonomous)

对于每个功能模块，完全自主执行：

```
STEP 1: WRITE TESTS FIRST (RED)
- Create test file
- Write test cases covering:
  * Happy path scenarios
  * Edge cases
  * Error scenarios
  * Boundary conditions
- Run tests → Verify ALL FAIL

STEP 2: IMPLEMENT MINIMAL CODE (GREEN)
- Write minimal code to pass tests
- No extra features
- No optimizations yet
- Just make tests pass

STEP 3: RUN TESTS (GREEN STATE)
- Execute full test suite
- Verify all new tests pass
- Verify no regressions
- If tests fail, fix until pass

STEP 4: REFACTOR (IMPROVE)
- Improve code structure
- Extract reusable components
- Improve readability
- Optimize performance (if needed)
- Ensure tests still pass

STEP 5: SECURITY REVIEW
- Use security-review skill
- Check for:
  * SQL injection
  * XSS vulnerabilities
  * CSRF protection
  * Input validation
  * Authentication/authorization
  * Secrets management
- Fix any issues found

STEP 6: CODE REVIEW
- Use code-review skill
- Check coding standards
- Verify error handling
- Check resource management
- Verify naming conventions
- Fix any issues found

STEP 7: COMMIT CODE
- Write conventional commit message
- Include: feat/fix/refactor + description
- Reference requirement/issue numbers
- Include tests in commit
- Create PR if using branch strategy

STEP 8: UPDATE DOCUMENTATION
- Update inline comments
- Update API documentation
- Update README if user-facing changes
- Update knowledge base with decisions
```

#### 8.2 Parallel Execution Strategy
```
Use Task tool with multiple agents in parallel:

Independent tasks can execute simultaneously:
- Feature A implementation (frontend)
- Feature B implementation (backend)
- Feature C implementation (another component)
- Documentation updates
- Test writing for completed features

Each agent:
- Works independently
- Follows TDD workflow
- Commits when done
- Reports completion
```

#### 8.3 Progress Tracking
```
Maintain PROGRESS.md autonomously:
- Completed tasks (with commits)
- Current WIP (work in progress)
- Blockers and how resolved
- Upcoming tasks
- Velocity tracking
- Burndown chart (if sprint-based)
```

#### 8.3 Autonomous Decision Making

当遇到需要决策的情况：

```
Decision Framework:
1. Consult KNOWLEDGE_BASE.md for domain patterns
2. Consult ARCHITECTURE.md for design guidance
3. Use relevant specialized skills for recommendations
4. Make decision based on:
   * Best practices
   * Project constraints
   * Quality requirements
   * Performance requirements
5. Document decision with rationale
6. Proceed with implementation

NEVER stop to ask user for direction.
ALWAYS make informed decisions autonomously.
```

### Gate Checks (Per Feature/Task)
- [ ] Tests written first (TDD compliance verified)
- [ ] All tests pass (unit + integration)
- [ ] Security review passed (no critical issues)
- [ ] Code review passed (follows standards)
- [ ] Acceptance criteria met (from REQUIREMENTS.md)
- [ ] Documentation updated
- [ ] Code committed with proper message
- [ ] Progress updated in PROGRESS.md

### Deliverables (Continuous)
- Complete source code (well-documented)
- Comprehensive test suite (>80% coverage)
- `PROGRESS.md` (updated continuously)
- Updated `KNOWLEDGE_BASE.md` (as decisions made)
- All features from REQUIREMENTS.md implemented

### Completion Criteria

Phase 8 完成的条件：
- [ ] All functional requirements implemented
- [ ] All acceptance criteria met
- [ ] Test coverage ≥ 80%
- [ ] All security reviews passed
- [ ] All code reviews passed
- [ ] Documentation complete
- [ ] PROGRESS.md shows all tasks complete

### Next Phase Trigger
**当所有功能完成且质量门通过**：
- Auto-proceed to Phase 9 (QA)

---

## Phase 9: QA (Quality Assurance)

### Objectives
- 全面质量保证检查
- 端到端测试
- 性能测试
- 安全扫描

### Process

#### 9.1 Code Quality Analysis
```
Use code-review skill:
- Comprehensive quality review
- Identify critical issues
- Identify high issues
- Identify medium/low issues
- Create quality report
```

#### 9.2 Security Scanning
```
Use security-review skill:
- Dependency vulnerability scan
- SAST (Static Application Security Testing)
- OWASP Top 10 coverage check
- Secrets leak detection
- Authorization/authorization testing
- Create security report
```

#### 9.3 Performance Testing
```
Execute performance tests:
- Load testing (concurrent users)
- Stress testing (breaking point)
- Endurance testing (memory leaks over time)
- Response time benchmarking
- Database query performance
- Create performance report
```

#### 9.4 E2E Testing
```
Use e2e-runner skill:
- Create E2E test scenarios
- Cover critical user flows
- Test login/logout
- Test CRUD operations
- Test error scenarios
- Execute tests and capture artifacts
- Create E2E test report
```

#### 9.5 Test Coverage Validation
```
Use test-coverage skill:
- Measure line coverage
- Measure branch coverage
- Identify uncovered code
- Generate coverage report
- Target: ≥80% coverage
```

### Gate Checks
- [ ] Code quality: No CRITICAL or HIGH issues
- [ ] Security scan: No HIGH or CRITICAL vulnerabilities
- [ ] Performance: Meets all NFRs (non-functional requirements)
- [ ] E2E tests: All critical paths passing
- [ ] Test coverage: ≥80% (lines and branches)
- [ ] All tests passing (unit, integration, E2E)
- [ ] Linting: No errors, warnings addressed
- [ ] Documentation: Complete and accurate

### Deliverables
- `QA_REPORT.md` (comprehensive quality report)
- Code quality report with issue list
- Security scan report with findings
- Performance test results with benchmarks
- E2E test report with screenshots/videos
- Test coverage report (≥80%)
- Bug list (with severity/priority)

### Decision Point

**IF** any gate check fails:
- Fix issues autonomously
- Re-run failed checks
- Iterate until all gates pass

**WHEN** all gates pass:
- Auto-proceed to Phase 10 (Ralph Loop Optimization)

### Next Phase Trigger
All quality gates passing.

---

## Phase 10: Ralph Loop Optimization - **10 ITERATIONS**

### Objectives
- 系统性优化代码质量
- 优化性能
- 清理技术债务
- 迭代至生产级质量

### Autonomous Execution

完全自主执行10次迭代，除非提前达到生产级。

### Iteration Termination Conditions

**提前终止条件（满足任一即可停止）：**
- 项目达到生产级运行质量（各子功能100%优秀）
- 连续3次迭代无显著改进
- 所有关键指标达到优秀级别

**强制终止条件：**
- 完成10次完整迭代

### Process (Each Iteration)

#### Iteration Loop (Execute 1-10 times)

```
ITERATION N/10:

STEP 1: ANALYSIS
- Identify optimization opportunities:
  * Performance bottlenecks (profiling)
  * Code smells and anti-patterns
  * Dead code and duplication
  * Technical debt items
  * Security improvements
  * Documentation gaps

STEP 2: OPTIMIZATION
Execute improvements:
- Performance optimization:
  * Hot spot optimization
  * Database query optimization
  * Caching improvements
  * Resource cleanup
- Code refactoring:
  * Improve readability
  * Extract reusable components
  * Apply design patterns
  * Reduce complexity
- Technical debt reduction:
  * Fix identified issues
  * Update dependencies
  * Improve error handling

STEP 3: TESTING
- Run full test suite
- Verify all tests pass
- Run performance benchmarks
- Check for regressions
- Update metrics

STEP 4: QUALITY VALIDATION
- Re-run security scan
- Re-run code quality check
- Verify coverage maintained
- Document improvements

STEP 5: DOCUMENTATION
- Update ITERATION_LOG.md:
  * Iteration number
  * Changes made
  * Metrics before/after
  * Issues resolved
  * New issues found (if any)
- Update PROGRESS.md
- Update relevant documentation

STEP 6: EVALUATION
- Assess if production-ready:
  * Performance targets met?
  * Code quality A or better?
  * Security clean?
  * All features working?
- IF production-ready: Consider early termination
- ELSE: Continue to next iteration
```

### Metrics Tracking

每次迭代追踪：

```
Metrics to Track:
- Test pass rate (target: 100%)
- Code coverage (target: ≥80%)
- Code quality score (target: A)
- Security vulnerabilities (target: 0 HIGH/CRITICAL)
- Performance benchmarks:
  * Response time p50/p95/p99
  * Throughput (requests/second)
  * Resource utilization (CPU, memory)
- Technical debt count (target: trending down)
- Code complexity (target: trending down)
```

### Gate Checks (Per Iteration)
- [ ] All tests passing (100%)
- [ ] No regressions introduced
- [ ] Coverage maintained (≥80%)
- [ ] At least one improvement made
- [ ] Iteration documented

### Completion Criteria

Phase 10 完成的条件（满足其一）：
- [ ] 项目达到生产级质量（所有指标优秀）
- [ ] 连续3次迭代无显著改进
- [ ] 完成10次迭代

### Deliverables
- `ITERATION_LOG.md` (complete iteration history)
- Optimized codebase
- Performance improvement report
- Technical debt reduction report
- Updated documentation

### Next Phase Trigger
**当任一完成条件满足**：
- Auto-proceed to Phase 11 (Deployment)

---

## Phase 11: Deployment

### Objectives
- 准备生产部署
- 执行部署
- 验证部署成功
- 配置监控

### Process

#### 11.1 Pre-Deployment Preparation
```
Create DEPLOYMENT_PLAN.md:
- Deployment strategy (blue-green, canary, rolling)
- Infrastructure requirements
- Database migration scripts
- Rollback procedures
- Monitoring setup
- Notification plan
```

#### 11.2 Pre-Deployment Checks
```
Execute checklist:
- Backup current production state
- Verify database migration scripts tested
- Test rollback procedure
- Setup monitoring and alerting
- Prepare smoke tests
- Notify stakeholders (if applicable)
```

#### 11.3 Execute Deployment
```
Deploy following strategy:
- Execute deployment plan
- Run smoke tests
- Monitor system metrics
- Verify critical functions
- Confirm rollback capability
```

#### 11.4 Post-Deployment Validation
```
Verify success:
- Monitor for 24-48 hours
- Check key metrics:
  * Error rates (<0.1%)
  * Response times (meet NFRs)
  * Throughput (handle expected load)
  * Resource utilization (healthy)
- Run synthetic transactions
- Validate all features working
```

#### 11.5 Create Release
```
Version control:
- Create semantic version tag (v1.0.0)
- Generate release notes:
  * Features delivered
  * Known issues (if any)
  * Upgrade instructions
- Push tag to repository
```

### Gate Checks
- [ ] Pre-deployment checks completed
- [ ] Deployment executed successfully
- [ ] Smoke tests passing
- [ ] System metrics healthy
- [ ] All features verified working
- [ ] Monitoring configured and alerting
- [ ] Rollback capability confirmed
- [ ] Release tagged and documented

### Deliverables
- `DEPLOYMENT_PLAN.md`
- Deployment artifacts
- Release tag (v1.0.0)
- Release notes
- Monitoring dashboards
- Post-deployment validation report

### Next Phase Trigger
**当部署成功且系统稳定**：
- Auto-proceed to Phase 12 (Project Summary)

---

## Phase 12: Project Summary

### Objectives
- 生成项目总结报告
- 归档所有交付物
- 知识转移
- 项目回顾

### Process

#### 12.1 Generate Comprehensive Summary
```
Create PROJECT_SUMMARY.md:

Executive Summary:
- Project vision and objectives
- Final deliverables overview
- Key achievements
- Business impact and value delivered

Execution Timeline:
- Start and end dates
- Phases completed
- Milestones achieved
- Timeline adherence

Requirements Traceability:
- Original requirements vs. delivered
- Coverage analysis (X% delivered)
- Out-of-scope items with rationale
- Requirement changes log

Technical Summary:
- Final architecture overview
- Technology stack delivered
- Key technical decisions
- Challenges and solutions

Quality Metrics:
- Final test coverage (actual: X%, target: 80%)
- Code quality score (actual: X, target: A)
- Security issues (final: 0 HIGH/CRITICAL)
- Performance metrics (vs. targets)
- Technical debt status

Development Metrics:
- Total lines of code
- Number of tests
- Number of iterations completed
- Bug count and resolution rate
- Velocity (features per sprint)

Iteration History:
- Ralph Loop iterations summary
- Major improvements made
- Performance gains achieved
- Before/after comparisons

Lessons Learned:
- What went exceptionally well
- What could be improved
- Surprises encountered
- Risks that materialized (and mitigation)
- Mitigation strategies that worked

Future Recommendations:
- Scalability improvements
- Feature enhancements (Phase 2 ideas)
- Technical debt to address
- Technology updates to consider
- Process improvements
```

#### 12.2 Archive Artifacts
```
Organize and archive:
- Source code (with version tags)
- Documentation (all phases)
- Test reports and coverage
- Design artifacts
- Deployment scripts and configs
- Monitoring and alerting configs
- Communication logs (decisions, reviews)
- Metrics and analytics data
```

#### 12.3 Knowledge Transfer
```
Prepare handoff:
- Update README with quick start
- Create CONTRIBUTING.md for developers
- Create DEPLOYMENT.md for ops
- Create TROUBLESHOOTING.md for support
- Document runbooks for common operations
```

#### 12.4 Self-Evolution (Enhanced with Capability-Evolver)
```
STEP 1: Use self-evolving-skill
- Capture lessons learned
- Extract successful patterns
- Document pitfalls to avoid
- Update skill knowledge base
- Improve decision logic

STEP 2: Execute Capability-Evolver
```
cd C:\Users\91216\.claude\skills\capability-evolver
node index.js run --target C:\Users\91216\.claude\skills\super-skill
```

This triggers:
- Analysis of project session history
- Identification of optimization signals:
  * Missing patterns in MEMORY.md
  * Gaps in documentation
  * Opportunities for workflow improvement
  * Technical debt in skill code
- Automatic generation of improvements:
  * Updated MEMORY.md with new learnings
  * Enhanced CHANGELOG.md with project insights
  * Refined decision logic
  * Optimized workflow steps
- Solidification of evolution (if approved)

STEP 3: Validate Evolution
- Review evolver-generated changes
- Verify improvements are beneficial
- Apply updates to Super-Skill
- Repackage skill with enhancements
- Update version number
```

**Evolution Triggers**:
- After every completed project
- When critical lessons learned
- When new patterns discovered
- When workflow bottlenecks identified

### Gate Checks
- [ ] All deliverables accepted
- [ ] Project summary complete
- [ ] All artifacts archived
- [ ] Documentation finalized
- [ ] Knowledge transfer complete
- [ ] Self-evolution executed (self-evolving-skill)
- [ ] Capability-Evolver analysis completed
- [ ] Evolver improvements applied
- [ ] Skill version updated with learnings
- [ ] Super-Skill repackaged with enhancements

### Deliverables
- `PROJECT_SUMMARY.md` (comprehensive)
- Complete source repository
- Test suite and reports
- Full documentation package
- Archived artifacts
- `MEMORY.md` (updated with project learnings)
- `CHANGELOG.md` (updated with version history)
- Enhanced Super-Skill package (via capability-evolver)

### Project Complete

🎉 **Project delivered successfully!**

---

## Autonomous Execution Rules

### Critical Rules for Phases 4-12

1. **ZERO USER INTERACTION**: After plan confirmation, never ask user for decisions
2. **Autonomous Decision Making**: Make all decisions using best practices and available skills
3. **Progress Without Approval**: Execute tasks without seeking confirmation
4. **Handle Errors Autonomously**: Debug and fix issues independently
5. **Adapt as Needed**: Adjust approach based on findings without user input
6. **Document Everything**: Log all decisions, changes, and rationale
7. **Quality Never Compromised**: Never skip quality gates for speed
8. **Complete Before Reporting**: Only report to user when phase/project is complete

### When to Break Autonomous Mode

**ONLY stop autonomous execution for:**
- System-blocking errors that cannot be resolved
- Discovered impossibility (technical constraints violated)
- Critical security vulnerability found that requires immediate attention

**Even in these cases:**
- Attempt autonomous resolution first
- If must break, provide full context and recommendations
- Present clear options with recommendations

---

## Skill Integration Matrix

### Phase 0: Visionary Elevation
- `ai-native-vision` - AI-native product architect
- `brainstorming` - Systematic exploration of ideas and approaches

### Phase 1: Feasibility Check
- `feasibility-check` - Comprehensive feasibility analysis

### Phase 2: GitHub Discovery
- `github-discovery` - Find and analyze open-source solutions

### Phase 2b: Skills Discovery
- `find-skills` - Discover and install skills from open agent skills ecosystem

### Phase 3: Knowledge Base
- `continuous-learning-v2` - Build domain knowledge base
- `skill-from-masters` - Collect best practices

### Phase 4: Requirements
- `prompt-architect` - Structure requirements
- `brainstorming` - Clarify requirements through systematic exploration
- Direct user interaction for refinement

### Phase 5-5b: Architecture & Design
- `architect` - System architecture design
- `skill-from-masters` - Architecture patterns
- `frontend-patterns` / `backend-patterns` - Tech-specific patterns
- `brainstorming` - Design exploration and decision-making

### Phase 6: WBS
- `planner` - Work breakdown structure
- `planning-with-files` - Plan documentation

### Phase 7: Project Initialization
- `auto-git-create` - Automated GitHub repository creation
- Direct execution of setup tasks
- Tool configuration scripts

### Phase 8: Autonomous Development
- `tdd-workflow` - Test-driven development
- `security-review` - Security validation
- `code-review` - Code quality
- `superpowers` - Parallel task execution
- `systematic-debugging` - Four-phase debugging with root cause investigation
- `multi-agent-orchestration` - Parallel agent teams for development
- `advanced-reasoning` - CoT/ToT for complex implementation decisions

### Phase 9: QA
- `code-review` - Quality review
- `security-review` - Security scanning
- `e2e` (via Task) - E2E testing
- `test-coverage` - Coverage analysis
- `systematic-debugging` - Bug investigation and resolution
- `advanced-reasoning` - ToT for complex bug diagnosis

### Phase 10: Ralph Loop
- `ralph-loop` - Intelligent iteration
- `refactor-clean` - Code cleanup
- `advanced-reasoning` - DFS ToT for optimization exploration

### Phase 11: Deployment
- `auto-git-create` - GitHub repository management and publishing
- `commit` - Version control and release
- Direct execution of deployment

### Phase 12: Project Summary & Evolution
- `doc-updater` - Documentation finalization
- `self-evolving-skill` - Learn and evolve
- `capability-evolver` - Analyze and optimize with GEP protocol
- `darwin-evolution` - Darwin Gödel Machine self-improvement (up to 50 generations)
- `advanced-reasoning` - GoT for learning synthesis
- `claude-mem` - Persistent memory storage (all phases)

### Cross-Cutting
- `skill-version-manager` - Version control and rollback (all phases)
- `continuous-learning-v2` - Knowledge capture (all phases)
- `capability-evolver` - Continuous optimization and evolution (post-project)
- `claude-mem` - Persistent memory and context retrieval (all phases, since V3.2)
- `find-skills` - Dynamic capability extension (Phase 2b, since V3.3)
- `multi-agent-orchestration` - Parallel agent coordination (all phases, since V3.6)
- `advanced-reasoning` - Reasoning enhancement (all phases, since V3.6)
- `darwin-evolution` - Self-improvement engine (post-project, since V3.6)

---

## Example: Complete Autonomous Execution Flow

```
User: "Build me a task management app"

Claude (Super-Skill activates):

[Phase 1: Feasibility Check]
→ Runs feasibility-check
→ Generates FEASIBILITY_REPORT.md
→ Score: 85/100 - GO
→ Auto-proceed

[Phase 2: GitHub Discovery]
→ Runs github-discovery
→ Finds 47 task management apps
→ Analyzes top 3
→ Best match covers 75% requirements
→ Decision: Clone + Adapt
→ Auto-clone and setup
→ Auto-proceed

[Phase 2b: Skills Discovery]
→ Runs find-skills
→ Searches for: react performance, testing, security
→ Finds 12 relevant skills
→ Evaluates and scores each
→ Auto-installs 3 skills (≥80% relevance):
  - vercel-react-best-practices (92%)
  - security-review (88%)
  - tdd-workflow (85%)
→ Generates SKILLS_DISCOVERY_REPORT.md
→ Auto-proceed

[Phase 3: Knowledge Base]
→ Runs continuous-learning-v2
→ Builds domain knowledge
→ Documents tech decisions
→ Auto-proceed

[Phase 4: Requirements - INTERACTION POINT 2]
→ Clarifies requirements with user
→ Presents complete specification
→ User confirms: "Yes, proceed"
→ REQUIREMENTS.md baselined
→ Auto-proceed

[Phase 5: Architecture]
→ Designs system
→ Creates ARCHITECTURE.md
→ Auto-proceed

[Phase 5b: Detailed Design]
→ Designs components
→ Creates API_DESIGN.md
→ Auto-proceed

[Phase 6: WBS]
→ Creates work breakdown
→ Defines 127 tasks
→ Identifies critical path
→ Auto-proceed

[Phase 7: Initialization]
→ Sets up repository
→ Configures tools
→ Sets up CI/CD
→ Auto-proceed

[Phase 8: Autonomous Development - ZERO USER INTERACTION]
→ Executes 127 tasks autonomously
→ Makes 234 autonomous decisions
→ Commits 347 times
→ NO user interaction
→ All features complete
→ All tests passing (100%)
→ Coverage 87%
→ Auto-proceed

[Phase 9: QA]
→ Runs code-review
→ Runs security-review
→ Runs E2E tests
→ Runs performance tests
→ All gates pass
→ Auto-proceed

[Phase 10: Ralph Loop - 10 ITERATIONS]
→ Iteration 1/10: Performance +15%
→ Iteration 2/10: Code quality B→A
→ Iteration 3/10: Security clean
→ ...
→ Iteration 7/10: No improvement for 3 iterations
→ Production-ready achieved
→ Early termination
→ Auto-proceed

[Phase 11: Deployment]
→ Creates deployment plan
→ Executes deployment
→ Verifies success
→ Creates release v1.0.0
→ Auto-proceed

[Phase 12: Project Summary]
→ Generates PROJECT_SUMMARY.md
→ Archives artifacts
→ Self-evolves with lessons
→ Updates skill to v2.1

[FINAL DELIVERABLE]
→ "🎉 Task management app complete!
→ Delivered: v1.0.0
→ Coverage: 87%
→ Quality: A
→ All features working
→ Summary: [Path to PROJECT_SUMMARY.md]
→ Repository: [Path]
→ Ready for production use"

ZERO user interaction after Phase 4.
```

---

## Version History

- **v3.2** (2026-02-24): Integrated Claude-Mem persistent memory system, 90% token savings, cross-session context retention
- **v3.1** (2026-02-22): Integrated Capability-Evolver for self-optimization, enhanced Phase 12 with evolution workflow
- **v3.0** (2026-02-22): Added AI Native Visionary Phase 0, 13-phase complete workflow
- **v2.0** (2026-02-12): Complete rewrite with autonomous execution, 12-phase workflow, GitHub discovery, feasibility-first
- **v1.0** (2026-02-12): Initial 8-phase workflow

---

## Quick Reference for Claude

### When Super-Skill Activates

User says things like:
- "Build me [app type]"
- "Create [project description]"
- "I need [feature] developed"
- "Help with [complex project]"

### First Steps

1. **Check for Super-Skill updates** (auto-update self and nested skills)
2. **Create version snapshot** (enable rollback)
3. **Start Phase 1** (Feasibility Check)
4. **Follow autonomous workflow** through all 12 phases
5. **Self-evolve** at the end

### Interaction Points

Remember: Only 3 user interaction points:
1. Initial requirement input
2. Requirement confirmation (end of Phase 4)
3. Plan confirmation (if presenting complete execution plan)

After interaction point 3: Execute autonomously to completion.

---

**Autonomous. Comprehensive. Production-Ready.**
