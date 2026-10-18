---
name: post-run-evolution
description: Post-execution review and self-evolution system. TRIGGER after every Super-Skill project completion (Phase 12). Capabilities: (1) Comprehensive project retrospective, (2) Signal extraction for improvement, (3) Gene mutation and evolution, (4) Capsule packaging of successful patterns, (5) Skill quality scoring, (6) Auto-update based on learnings. Ensures continuous improvement across sessions.
---

# Post-Run Evolution

## Overview

Executes after every Super-Skill project completion to capture learnings, evolve capabilities, and improve future performance. Integrates with GEP Protocol for systematic self-improvement.

## Execution Sequence

```
┌─────────────────────────────────────────┐
│  POST-RUN EVOLUTION (After Phase 12)    │
├─────────────────────────────────────────┤
│  1. Project Retrospective               │
│  2. Signal Extraction                   │
│  3. Quality Scoring                     │
│  4. Evolution Decision                  │
│  5. Mutation Build & Apply              │
│  6. Capsule Packaging                   │
│  7. Cross-Session Learning Sync         │
└─────────────────────────────────────────┘
```

## Step 1: Project Retrospective

Comprehensive analysis of the completed project:

### Retrospective Template

```markdown
# PROJECT RETROSPECTIVE

## Project Overview
- Name: [project-name]
- Duration: [start-date] to [end-date]
- Phases Completed: [X/14]

## What Went Well
- [Success 1]
- [Success 2]
- [Success 3]

## What Could Be Improved
- [Improvement 1]
- [Improvement 2]
- [Improvement 3]

## Blockers Encountered
- [Blocker 1] → Resolution: [how resolved]
- [Blocker 2] → Resolution: [how resolved]

## Phase Analysis
| Phase | Duration | Quality | Notes |
|-------|----------|---------|-------|
| 0 | X min | ⭐⭐⭐⭐ | Vision clear from start |
| 1 | X min | ⭐⭐⭐⭐⭐ | Feasibility score: 0.85 |
| ... | ... | ... | ... |

## Metrics Summary
- Total Tool Calls: X
- Error Recovery Count: X
- User Interaction Points: 3 (as expected)
- Code Generated: X lines
- Tests Written: X
- Coverage Achieved: X%
```

### Retrospective Questions

1. **Efficiency**: Where did we spend the most time? Was it necessary?
2. **Quality**: Which phases had the highest/lowest quality output?
3. **Blockers**: What blocked progress? How can we prevent similar blockers?
4. **Innovations**: What new patterns or solutions did we discover?
5. **Failures**: What failed? Why? How can we avoid similar failures?

## Step 2: Signal Extraction

Extract evolution signals from project execution:

### Signal Types

| Type | Trigger | Priority |
|------|---------|----------|
| **Defensive** | Errors, failures, blockers | High |
| **Opportunity** | New patterns, optimizations | Medium |
| **Stagnation** | Repeated patterns, no improvement | Low |

### Signal Detection

```markdown
## Signal Detection Analysis

### Defensive Signals
- [ ] Error pattern detected: [description]
- [ ] Recurring blocker: [description]
- [ ] Quality degradation in: [phase/skill]

### Opportunity Signals
- [ ] New pattern discovered: [description]
- [ ] Optimization opportunity: [description]
- [ ] Skill gap identified: [missing capability]

### Stagnation Signals
- [ ] No improvement in [area] for X projects
- [ ] Repeated solutions without variation
- [ ] Declining innovation rate
```

### Signal Priority Scoring

```
Signal Score = (Impact × Frequency × Feasibility) / Risk

Impact: 1-5 (how much improvement)
Frequency: 1-5 (how often it occurs)
Feasibility: 1-5 (how easy to implement)
Risk: 1-5 (risk of breaking changes)

Score ≥ 12: Immediate evolution
Score 8-11: Queue for next evolution
Score < 8: Log for future consideration
```

## Step 3: Quality Scoring

Score project quality across dimensions:

### Quality Dimensions

| Dimension | Weight | Scoring Criteria |
|-----------|--------|------------------|
| **Correctness** | 40% | Does it work? Bug count |
| **Reliability** | 25% | Will it keep working? Error handling |
| **Maintainability** | 20% | Can others understand it? Code clarity |
| **Performance** | 10% | Is it fast enough? Response times |
| **Elegance** | 5% | Is it clean? Design quality |

### Quality Report

```markdown
## Quality Report

### Overall Score: X/5.0

### Dimension Scores
- Correctness: X/5 (Weight: 40%)
- Reliability: X/5 (Weight: 25%)
- Maintainability: X/5 (Weight: 20%)
- Performance: X/5 (Weight: 10%)
- Elegance: X/5 (Weight: 5%)

### Quality Issues Found
1. [Issue] - Severity: High/Medium/Low
2. [Issue] - Severity: High/Medium/Low

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

## Step 4: Evolution Decision

Decide whether to trigger evolution:

### Decision Matrix

| Condition | Action |
|-----------|--------|
| Signal Score ≥ 12 | Immediate evolution |
| 3+ defensive signals | Priority evolution |
| Project success + new patterns | Capsule creation |
| No significant learnings | Skip evolution |

### Evolution Types

```
1. REPAIR: Fix identified issues
   - Triggered by defensive signals
   - Focus on error prevention

2. OPTIMIZE: Improve existing capabilities
   - Triggered by opportunity signals
   - Focus on efficiency gains

3. INNOVATE: Add new capabilities
   - Triggered by skill gaps
   - Focus on new patterns
```

## Step 5: Mutation Build & Apply

Build and apply evolution mutations:

### Mutation Process

```
1. SELECT: Choose Gene/Capsule for mutation
2. DESIGN: Design mutation changes
3. VALIDATE: Check safety constraints
4. APPLY: Apply mutation to skill
5. TEST: Verify mutation works
6. COMMIT: Commit changes with rollback
```

### Mutation Safety

```markdown
## Mutation Safety Checklist

- [ ] Blast radius within limits (<60 files, <20000 lines)
- [ ] No breaking changes to public interfaces
- [ ] Backward compatible with existing workflows
- [ ] Rollback plan documented
- [ ] Test coverage maintained
```

### Mutation Log Entry

```json
{
  "id": "mutation-2026-03-14-001",
  "type": "optimize",
  "trigger": "high-agency-debugging-improvement",
  "gene": "debugging-workflow",
  "changes": [
    "Added 5-step debugging methodology",
    "Integrated pressure escalation"
  ],
  "status": "applied",
  "timestamp": "2026-03-14T23:00:00Z",
  "rollback_id": "rollback-001"
}
```

## Step 6: Capsule Packaging

Package successful patterns as evolution capsules:

### Capsule Structure

```json
{
  "id": "capsule-2026-03-14-001",
  "name": "high-agency-execution",
  "description": "Iron rules and pressure escalation for persistent execution",
  "source_project": "super-skill-integration",
  "patterns": [
    {
      "name": "three-iron-rules",
      "description": "Exhaust options, act before asking, take initiative"
    },
    {
      "name": "pressure-escalation",
      "description": "L1-L4 escalation for repeated failures"
    }
  ],
  "effectiveness_score": 4.5,
  "usage_count": 0,
  "created_at": "2026-03-14T23:00:00Z"
}
```

### Capsule Storage

```
assets/gep/capsules.json
├── capsule-001: darwin-evolution-patterns
├── capsule-002: multi-agent-orchestration
├── capsule-003: high-agency-execution
└── capsule-004: cognitive-modes-switching
```

## Step 7: Cross-Session Learning Sync

Sync learnings for future sessions:

### Sync Targets

1. **MEMORY.md** - Persistent knowledge
2. **EVOLUTION.md** - Evolution history
3. **events.jsonl** - Event log
4. **Context Hub** - Annotation sync

### Sync Process

```bash
# Update MEMORY.md with new learnings
echo "## 2026-03-14 Learning: High-Agency Execution" >> MEMORY.md

# Log evolution event
echo '{"type":"evolution","status":"complete","timestamp":"2026-03-14T23:00:00Z"}' >> assets/gep/events.jsonl

# Sync Context Hub annotations
chub annotate project-patterns "High-agency execution improved debugging efficiency by 36%"
```

## Post-Run Report

Generate comprehensive report:

```markdown
# POST-RUN EVOLUTION REPORT
Date: 2026-03-14

## Project Summary
- Project: [name]
- Phases: 14/14 completed
- Quality Score: 4.2/5.0

## Retrospective Highlights
- **Success**: [highlight]
- **Improvement**: [area]
- **Innovation**: [new pattern]

## Signals Extracted
- Defensive: 2
- Opportunity: 3
- Stagnation: 0

## Evolution Actions
- Mutations Applied: 1
- Capsules Created: 1
- Skills Updated: 2

## Learning Sync
- MEMORY.md: Updated
- Context Hub: 3 annotations added
- Events Log: 1 entry added

## Next Session Recommendations
1. [Recommendation 1]
2. [Recommendation 2]
```

## Configuration

### Environment Variables

```bash
# Enable/disable post-run evolution
POST_RUN_EVOLUTION=true                   # Default: true
POST_RUN_RETROSPECTIVE=true               # Default: true
POST_RUN_AUTO_EVOLVE=true                 # Default: true

# Evolution thresholds
EVOLUTION_SIGNAL_THRESHOLD=12             # Minimum score for auto-evolution
EVOLUTION_BLAST_RADIUS_FILES=60           # Max files affected
EVOLUTION_BLAST_RADIUS_LINES=20000        # Max lines changed
```

### Strategy Presets

| Strategy | Repair | Optimize | Innovate |
|----------|--------|----------|----------|
| balanced | Medium | Medium | Medium |
| innovate | Low | Low | High |
| harden | High | Medium | Low |
| repair-only | High | Low | None |

## Integration with Super-Skill

| Phase | Integration Point |
|-------|------------------|
| **Phase 12** | Execute after project summary |
| **darwin-evolution** | Use GEP Protocol for mutations |
| **pre-run-upgrade** | Sync learnings at next session start |

## Quick Reference

```
# Manual trigger
/super-skill --post-run-evolution

# Skip evolution
/super-skill --skip-evolution

# Force evolution
/super-skill --force-evolution --type innovate
```

## Version

**V1.0.0** - 2026-03-14
- Seven-step evolution sequence
- Signal extraction and scoring
- Quality dimension analysis
- Mutation safety system
- Capsule packaging
- Cross-session learning sync
- Integration with GEP Protocol
