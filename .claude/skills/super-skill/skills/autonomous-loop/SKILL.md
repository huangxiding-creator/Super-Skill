---
name: autonomous-loop
description: Infinite autonomous development loop inspired by karpathy/autoresearch. Executes keep/discard experiment cycles with git-based experiment tracking, fixed budgets, and simplicity criteria. For 24-hour unattended operation.
---

# Autonomous Loop: Infinite Experiment Cycle

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) (58K+ stars).

## Core Philosophy

**"The human programs the process, the AI executes it."**

The human edits the instructions (SKILL.md / program.md). The AI modifies the code. The evaluation infrastructure is read-only ground truth. This separation enables fully autonomous 24-hour operation.

## The Infinite Loop

```
┌─────────────────────────────────────────────────────────────┐
│  AUTONOMOUS LOOP (runs until human interrupts)              │
│                                                             │
│  1. READ   → Analyze current git state and codebase         │
│  2. MODIFY → Implement experimental improvement             │
│  3. COMMIT → Git commit with experiment description         │
│  4. TEST   → Run tests, capture output (NOT streamed)       │
│  5. EVALUATE → Parse results against acceptance criteria    │
│  6. DECIDE → KEEP (improved) or DISCARD (worse/equal)      │
│  7. LOG    → Record to experiment log                       │
│  8. NEXT   → Advance to next experiment idea                │
│                                                             │
│  On CRASH: Read error log → Fix or SKIP → Continue loop    │
│  On TIMEOUT: Kill process → Log → Continue loop             │
└─────────────────────────────────────────────────────────────┘
```

## Decision Rules

### KEEP Criteria (all must be true)
- Tests pass (existing + new)
- Code quality metric maintained or improved
- No regressions in performance
- Complexity justified by improvement magnitude

### DISCARD Criteria (any triggers discard)
- Tests fail
- Performance regression
- Build errors
- Complexity increase without proportional benefit

### Simplicity Criterion (from autoresearch)
- **Small improvement + ugly complexity** = NOT worth it
- **Small improvement from DELETING code** = definitely keep
- **Equal performance + simpler code** = keep
- **Equal performance + more complex code** = discard

### Thresholds
| Metric | KEEP threshold | Notes |
|--------|----------------|-------|
| Test pass rate | 100% | No exceptions |
| Coverage | ≥ previous | Never decrease |
| Build time | ≤ previous + 10% | No significant slowdown |
| Bundle size | ≤ previous + 5% | Watch for bloat |
| Lines of code | Prefer fewer | Simplicity wins |

## Git-as-Experiment-Tracker

### Branch Strategy
```
main                          (stable, production)
├── autoresearch/session-1    (session branch, only keep commits)
├── autoresearch/session-2    (next session)
```

### Commit Convention
```
[experiment] description of change

val_metric: X.XXX (was Y.YYY)
decision: keep|discard
rationale: why this change was made
```

### Experiment Log (NOT git-tracked)
```
# experiments.tsv
commit  metric  status    description
a1b2c3d 0.85    keep      baseline
b2c3d4e 0.87    keep      add caching layer
c3d4e5f 0.84    discard   switch to library X
```

## Autonomous Behavior Protocol

### NEVER STOP Rules
- Do NOT pause to ask the human for approval between experiments
- The human might be asleep - continue indefinitely
- If you run out of ideas, think harder:
  1. Re-read the codebase for missed patterns
  2. Try combining previous successful approaches
  3. Try radical changes to break plateaus
  4. Search for best practices online
  5. Re-examine discarded ideas with new perspective

### Failure Handling
| Failure Type | Action |
|-------------|--------|
| Simple bug (typo, import) | Fix immediately, re-run |
| NaN / infinite loop | Skip, log "crash", next idea |
| OOM / resource limit | Reduce scope, retry once |
| Timeout (>budget) | Kill process, log, next idea |
| Fundamental flaw | Log "discard", next idea |

### Budget Constraints
```bash
TIME_BUDGET_PER_EXPERIMENT=300    # 5 minutes max per experiment
MAX_EXPERIMENTS_PER_SESSION=100   # ~100 experiments overnight
MEMORY_BUDGET_MB=4096             # Max memory per experiment
```

## Integration with Super-Skill Phases

### Phase 8 Enhancement: Autonomous Development
The autonomous loop replaces traditional Phase 8 development:
- Traditional: Implement feature → test → debug → commit
- Autonomous: Loop { modify → test → evaluate → keep/discard } × N

### Phase 10 Enhancement: Ralph Loop
The Ralph Loop becomes an instance of the autonomous loop:
- Each optimization iteration = one experiment
- Convergence = no improvement over 3 consecutive experiments

### Phase 12 Enhancement: Evolution
Post-run evolution uses the experiment log:
- Analyze keep/discard patterns
- Extract which mutation types succeed most
- Feed into next session's strategy

## Read-Only Infrastructure

The following are immutable during autonomous operation:
- Test suite definitions (ground truth for evaluation)
- CI/CD pipeline configuration
- Lint rules and code style configuration
- Environment configuration and secrets

The AI agent only modifies:
- Implementation code
- Documentation (as experiments prove value)
- Configuration that experiments explicitly test

## Experiment Strategy

### Idea Generation Priority
1. **Fix known issues** (from crash logs, failed tests)
2. **Apply proven patterns** (from best practices search)
3. **Optimize bottlenecks** (from profiling data)
4. **Simplify code** (delete dead code, reduce complexity)
5. **Try novel approaches** (from research, cross-domain patterns)

### Anti-Patterns to Avoid
- Running the same failed experiment twice without changes
- Adding complexity for marginal improvements
- Ignoring crash logs and error messages
- Modifying test expectations to make tests pass
- Committing without running the full test suite

## Configuration

```bash
AUTONOMOUS_LOOP_ENABLED=true
AUTONOMOUS_TIME_BUDGET=300
AUTONOMOUS_MAX_EXPERIMENTS=100
AUTONOMOUS_BRANCH_PREFIX="autoresearch"
AUTONOMOUS_SIMPLICITY_WEIGHT=0.3
AUTONOMOUS_LOG_FILE="experiments.tsv"
```

## Version
V1.0 - 2026-03-29 - Initial implementation based on karpathy/autoresearch patterns
