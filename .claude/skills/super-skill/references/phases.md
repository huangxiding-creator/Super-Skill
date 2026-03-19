# Super-Skill 14-Phase Workflow Reference

## Table of Contents
1. [Phase 0: Visionary Elevation](#phase-0-visionary-elevation)
2. [Phase 1: Feasibility Analysis](#phase-1-feasibility-analysis)
3. [Phase 2: GitHub Discovery](#phase-2-github-discovery)
4. [Phase 2b: Skills Discovery](#phase-2b-skills-discovery)
5. [Phase 3: Knowledge Base](#phase-3-knowledge-base)
6. [Phase 4: Requirements Engineering](#phase-4-requirements-engineering)
7. [Phase 5-5b: Architecture & Design](#phase-5-5b-architecture--design)
8. [Phase 6: WBS](#phase-6-wbs)
9. [Phase 7: Project Initialization](#phase-7-project-initialization)
10. [Phase 8: Autonomous Development](#phase-8-autonomous-development)
11. [Phase 9: QA](#phase-9-qa)
12. [Phase 10: Ralph Loop](#phase-10-ralph-loop)
13. [Phase 11: Deployment](#phase-11-deployment)
14. [Phase 12: Evolution](#phase-12-evolution)

---

## Phase 0: Visionary Elevation

### Purpose
Transform user requirements into AI-native vision through breakthrough thinking.

### 7-Step Visionary Process
1. **Requirement Capture**: Parse initial user request
2. **Constraint Analysis**: Identify explicit and implicit constraints
3. **Opportunity Mapping**: Find AI-native opportunities
4. **Vision Synthesis**: Create breakthrough vision
5. **Feasibility Preview**: Quick technical assessment
6. **Two-Dimensional Output**: AI-Enhanced vs AI-Native options
7. **Stakeholder Alignment**: Confirm vision with user

### Output Artifacts
- `VISION.md` - Visionary requirement document
- `CONSTRAINTS.md` - Constraint analysis
- `AI_NATIVE_OPTIONS.md` - Solution options

### Trigger
- User provides initial requirement
- Phase transition from previous project

---

## Phase 1: Feasibility Analysis

### Purpose
Evaluate technical, economic, operational, and scheduling feasibility.

### CC-FPS Framework (Claude Code Feasibility Scoring)

| Dimension | Weight | Factors |
|-----------|--------|---------|
| Technical | 30% | Tech stack fit, complexity, dependencies |
| Economic | 25% | Cost-benefit, ROI, resource availability |
| Operational | 25% | Team capability, maintenance, support |
| Scheduling | 20% | Timeline, milestones, critical path |

### Scoring
- **Score ≥ 0.7**: Proceed to Phase 2
- **Score 0.5-0.7**: Review risks, require mitigation plan
- **Score < 0.5**: Recommend pivot or termination

### Output Artifacts
- `FEASIBILITY_REPORT.md` - Comprehensive analysis
- `RISK_REGISTER.md` - Identified risks and mitigations

### Skills Used
- `feasibility-check` - Primary analysis

---

## Phase 2: GitHub Discovery

### Purpose
Find existing open-source solutions before building from scratch.

### Discovery Process
1. **Search**: Query GitHub for relevant projects
2. **Evaluate**: Score projects on relevance, quality, maintenance
3. **Analyze**: Review code structure, dependencies, license
4. **Decide**: Build vs Clone vs Adapt

### Decision Matrix

| Score | Action |
|-------|--------|
| ≥80% | Clone and adapt |
| 60-80% | Extract patterns |
| <60% | Build from scratch |

### Output Artifacts
- `GITHUB_DISCOVERY_REPORT.md` - Discovery findings
- `CLONE_DECISION.md` - Build/Clone decision

### Skills Used
- `github-discovery` - Primary search
- `find-skills` - Skills ecosystem search

---

## Phase 2b: Skills Discovery

### Purpose
Automatically find and install skills from open agent skills ecosystem.

### Process
1. **Gap Analysis**: Identify missing capabilities
2. **Skills Search**: Query skills ecosystem
3. **Evaluation**: Score skills on relevance (≥80% auto-install)
4. **Installation**: `npx skills add <skill-name>`

### Output Artifacts
- `SKILLS_DISCOVERY_REPORT.md` - Skills findings

### Skills Used
- `find-skills` - Primary discovery

---

## Phase 3: Knowledge Base

### Purpose
Build comprehensive domain knowledge for the project.

### Knowledge Types
1. **Domain Knowledge**: Business logic, terminology
2. **Technical Knowledge**: APIs, schemas, patterns
3. **Context Knowledge**: Project-specific decisions

### Output Artifacts
- `KNOWLEDGE_BASE/` - Knowledge directory
- `SCHEMAS.md` - Data schemas
- `API_REFERENCE.md` - API documentation

### Skills Used
- `continuous-learning-v2` - Knowledge capture

---

## Phase 4: Requirements Engineering

### Purpose
Define detailed, actionable requirements.

### Requirements Structure
```markdown
## Functional Requirements
- FR-001: [Requirement]
- FR-002: [Requirement]

## Non-Functional Requirements
- NFR-001: Performance: [Target]
- NFR-002: Security: [Target]
- NFR-003: Scalability: [Target]

## Acceptance Criteria
- AC-001: [Criteria]
```

### Output Artifacts
- `REQUIREMENTS.md` - Complete requirements
- `ACCEPTANCE_CRITERIA.md` - Acceptance tests

### Skills Used
- `brainstorming` - Requirement clarification

---

## Phase 5-5b: Architecture & Design

### Purpose
Design system architecture and component structure.

### Phase 5: System Architecture
- Tech stack selection
- Service boundaries
- Data flow design
- Infrastructure design

### Phase 5b: Component Design
- Component breakdown
- API contracts
- Database schemas
- Security design

### Output Artifacts
- `ARCHITECTURE.md` - System design
- `API_DESIGN.md` - API specifications
- `DATABASE_DESIGN.md` - Data models

### Skills Used
- `api-patterns` - API design
- `data-patterns` - Database design
- `security-scanning` - Security review

---

## Phase 6: WBS (Work Breakdown Structure)

### Purpose
Break project into executable tasks.

### WBS Structure
```
Project
├── Epic 1: [Feature Area]
│   ├── Story 1.1: [User Story]
│   │   ├── Task 1.1.1: [Technical Task]
│   │   └── Task 1.1.2: [Technical Task]
│   └── Story 1.2: [User Story]
├── Epic 2: [Feature Area]
│   └── ...
```

### Output Artifacts
- `WBS.md` - Work breakdown
- `TASK_BACKLOG.md` - Prioritized tasks

---

## Phase 7: Project Initialization

### Purpose
Set up project infrastructure.

### Setup Tasks
1. Create project directory structure
2. Initialize package manager (npm/pip/cargo)
3. Configure linting and formatting
4. Set up testing framework
5. Initialize git repository
6. Create GitHub remote
7. Configure CI/CD

### Output Artifacts
- Project directory structure
- Configuration files
- GitHub repository

### Skills Used
- `auto-git-create` - Repository creation
- `cicd-automation` - CI/CD setup

---

## Phase 8: Autonomous Development

### Purpose
Execute development with zero user interaction.

### Development Principles
- **TDD First**: Write tests before code
- **Small Commits**: Frequent, focused commits
- **Continuous Integration**: Run tests on each commit
- **Documentation**: Document as you code

### Sub-Skills Integration
| Task Type | Skill |
|-----------|-------|
| Testing | `testing-automation` |
| Code Generation | `code-transformation` |
| Debugging | `systematic-debugging` |
| API Development | `api-patterns` |
| Database | `data-patterns` |
| Real-time | `real-time-websockets` |
| Search | `search-indexing` |

### Output Artifacts
- Source code
- Test files
- Documentation

---

## Phase 9: QA (Quality Assurance)

### Purpose
Ensure quality through comprehensive testing.

### QA Checklist
- [ ] Unit tests pass (≥80% coverage)
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Accessibility (WCAG 2.1) compliance

### Skills Used
- `testing-automation` - Test execution
- `security-scanning` - Security audit
- `accessibility-a11y` - A11y compliance

### Output Artifacts
- `TEST_REPORT.md` - Test results
- `SECURITY_REPORT.md` - Security findings

---

## Phase 10: Ralph Loop

### Purpose
10-iteration optimization cycle.

### Loop Process
```
for i in 1..10:
    1. Analyze current state
    2. Identify improvement opportunities
    3. Implement improvements
    4. Validate improvements
    5. Document learnings
    6. Check convergence
```

### Convergence Criteria
- Performance targets met
- Test coverage ≥80%
- Zero critical bugs
- Documentation complete

---

## Phase 11: Deployment

### Purpose
Deploy to production environment.

### Deployment Steps
1. Pre-deployment checklist
2. Environment configuration
3. Database migrations
4. Application deployment
5. Post-deployment validation
6. Monitoring setup

### Skills Used
- `cicd-automation` - Deployment pipeline
- `monitoring-observability` - Monitoring setup

### Output Artifacts
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `RUNBOOK.md` - Operations guide

---

## Phase 12: Evolution

### Purpose
Capture learnings and evolve Super-Skill.

### Evolution Triggers
1. Project completion analysis
2. Pattern extraction
3. Skill improvement
4. Knowledge base update

### GEP Protocol Integration
- Extract signals from project
- Select Gene/Capsule
- Build mutation
- Execute evolution
- Solidify knowledge

### Output Artifacts
- `PROJECT_SUMMARY.md` - Project retrospective
- `LESSONS_LEARNED.md` - Key learnings
- Updated `MEMORY.md`
- Updated `CHANGELOG.md`

### Skills Used
- `darwin-evolution` - GEP Protocol evolution
- `capability-evolver` - Self-improvement

---

## Phase Transition Rules

### Gate Checks
| Phase | Gate Condition |
|-------|---------------|
| 0→1 | Vision confirmed |
| 1→2 | Feasibility ≥0.7 |
| 2→3 | Build decision made |
| 3→4 | Knowledge base complete |
| 4→5 | Requirements approved |
| 5→6 | Architecture approved |
| 6→7 | WBS complete |
| 7→8 | Infrastructure ready |
| 8→9 | Development complete |
| 9→10 | QA passed |
| 10→11 | Convergence achieved |
| 11→12 | Deployment successful |

### Rollback Conditions
- Critical test failure → Return to Phase 8
- Security vulnerability → Return to Phase 5
- Performance failure → Return to Phase 10
