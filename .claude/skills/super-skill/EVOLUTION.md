# Super-Skill Evolution System

## Overview

Super-Skill V3.1 integrates **Capability-Evolver** for continuous self-optimization and evolution. This system enables Super-Skill to learn from every project execution and automatically improve its capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Super-Skill V3.1                          │
│                  Self-Evolving Orchestrator                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   13-Phase Workflow                          │
│  Phase 0 → Phase 1 → ... → Phase 11 → Phase 12              │
│  (Visionary)  (Feasibility)        (Deployment)  (Evolution) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 12: Evolution Trigger                     │
│    - Project completion analysis                              │
│    - Lessons learned extraction                               │
│    - Pattern identification                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Capability-Evolver (GEP Protocol)                │
│    - Runtime history analysis                                 │
│    - Signal detection                                         │
│    - Mutation generation                                      │
│    - Evolution application                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Enhanced Super-Skill                        │
│    - Updated MEMORY.md                                        │
│    - Enhanced CHANGELOG.md                                    │
│    - Optimized workflow steps                                 │
│    - New version (V3.1.x)                                     │
└─────────────────────────────────────────────────────────────┘
```

## Evolution Triggers

Evolution is automatically triggered in the following scenarios:

### 1. Project Completion (Auto)
- **Trigger**: After Phase 12 completion
- **Action**: Run `python scripts/trigger_evolution.py <project-dir>`
- **Analysis**: Project summary, success metrics, issues encountered
- **Outcome**: Super-Skill learns from project execution

### 2. Critical Learning Event (Auto)
- **Trigger**: Discovery of significant new patterns or techniques
- **Action**: Immediate evolution session
- **Analysis**: New patterns, successful solutions, pitfalls
- **Outcome**: Knowledge base updated with new insights

### 3. User Feedback (Manual)
- **Trigger**: User provides explicit feedback
- **Action**: Targeted evolution on specific area
- **Analysis**: User's observations and suggestions
- **Outcome**: User-requested improvements prioritized

### 4. Periodic Review (Scheduled)
- **Trigger**: Every 5 projects or 7 days
- **Action**: Comprehensive evolution session
- **Analysis**: All recent projects, patterns, trends
- **Outcome**: Major optimization release

## GEP Protocol (Genome Evolution Protocol)

Super-Skill uses the GEP protocol for constrained evolution:

### 1. Mutation
Genetic modifications to skill behavior:
- Workflow optimization
- Decision logic enhancement
- Pattern integration
- Knowledge expansion

### 2. PersonalityState
Current evolutionary state:
- **Adaptive**: Learns from each project
- **Conservative**: Maintains stability
- **Experimental**: Tries new approaches
- **Production**: Optimized for reliability

### 3. EvolutionEvent
Specific evolution occurrences:
- Type: `optimization` | `bug_fix` | `enhancement` | `pattern`
- Priority: `critical` | `high` | `medium` | `low`
- Source: `project_execution` | `user_feedback` | `periodic_review`

### 4. Gene
Atomic units of evolution:
- **Workflow Genes**: Phase execution logic
- **Decision Genes**: Choice algorithms
- **Quality Genes**: Standards and validation
- **Knowledge Genes**: Domain patterns

### 5. Capsule
Packaged evolution result:
- All mutations grouped
- Backed up before application
- Version controlled
- Rollback capable

## Evolution Workflow

### Phase 12: Evolution Execution

```bash
# Triggered automatically after project completion
cd C:\Users\91216\.claude\skills\super-skill

# Step 1: Extract lessons from project
python scripts/extract_lessons.py <project-dir>

# Step 2: Trigger Capability-Evolver
python scripts/trigger_evolution.py <project-dir>

# Step 3: Apply evolver-generated improvements
# (Automatic: MEMORY.md, CHANGELOG.md updates)

# Step 4: Repackage Super-Skill
python scripts/package_skill.py

# Step 5: Version bump (if significant changes)
# (Automatic: V3.1 → V3.1.1, etc.)
```

## Configuration Files

### `.env.super-skill`
Evolution configuration for Super-Skill:
- Strategy: `balanced` (conservative/experimental mix)
- Self-modification: `false` (safe mode)
- Auto-apply: `true` (automatic improvements)
- Backup: `true` (backup before evolution)

### `.env.mad-dog` (Capability-Evolver)
Continuous loop mode for evolver:
- Strategy: `auto`
- Loop: `true`
- Self-modification: `false`

## Signals Detection

Capability-Evolver detects optimization signals:

### Signal Types

1. **memory_missing**: MEMORY.md incomplete
2. **session_logs_missing**: Project logs not archived
3. **pattern_gap**: Successful pattern not documented
4. **technical_debt**: Code quality issue
5. **workflow_bottleneck**: Phase execution inefficiency
6. **quality_drift**: Standards not maintained

### Signal Resolution

Each signal triggers specific evolution:
- Documentation updates
- Workflow refinement
- Quality gate adjustments
- New pattern integration
- Bug fixes and improvements

## Memory Bank Structure

### `MEMORY.md`
Persistent knowledge bank:
- Project overview and core capabilities
- Technical decisions and architecture
- Success metrics and known issues
- Optimization history
- Future opportunities

### `CHANGELOG.md`
Version history:
- V3.1 (current): Capability-Evolver integration
- V3.0: AI Native Visionary Phase 0
- V2.0: Autonomous execution, 12-phase workflow
- V1.0: Initial 8-phase release

### `EVOLUTION_SUMMARY.md`
Generated after each evolution:
- Signals detected
- Mutations applied
- Personality state changes
- Version changes
- Rollback information

## Safety and Rollback

### Evolution Safety

1. **Backup Before Evolution**: Automatic backup to `.evolution-backups/`
2. **Critical Path Protection**: Core files protected (SKILL.md, essential scripts)
3. **Version Control**: Every evolution versioned
4. **Validation**: Changes validated before application
5. **Rollback Capability**: Instant rollback to any previous version

### Rollback Process

```bash
# List available versions
python scripts/list_evolution_versions.py

# Rollback to specific version
python scripts/rollback_evolution.py V3.1.5

# Verify rollback
python scripts/check_evolver.py
```

## Evolution Monitoring

### View Evolution Status

```bash
# Check current evolution state
python scripts/evolution_status.py

Output:
- Current version: V3.1.2
- Last evolution: 2026-02-22 14:30
- Signals detected: 3
- Mutations pending: 0
- Personality state: adaptive
```

### View Evolution History

```bash
# Show evolution log
cat evolution.log

# Or view evolution summary
cat EVOLUTION_SUMMARY.md
```

## Continuous Improvement

### Evolution Metrics

Tracked over time:
- **Evolution Count**: Total evolutions performed
- **Signal Rate**: Signals detected per project
- **Mutation Success**: Successful mutations / total mutations
- **Quality Trend**: Code quality over time
- **Performance Trend**: Execution efficiency over time

### Optimization Targets

Continuous improvement goals:
- **Autonomy**: >90% tasks without user interaction
- **Quality**: Code quality A or better
- **Coverage**: Test coverage ≥80%
- **Efficiency**: Phase execution time trending down
- **Success**: Project success rate trending up

## Integration with Other Skills

### Self-Evolving-Skill
- **Purpose**: Pattern extraction and instinct creation
- **Trigger**: During project execution
- **Output**: Atomic instincts, confidence scores
- **Integration**: Evolver uses instincts as data

### Continuous-Learning-v2
- **Purpose**: Knowledge capture during workflow
- **Trigger**: All phases
- **Output**: Domain patterns, best practices
- **Integration**: Evolver incorporates into MEMORY.md

### Capability-Evolver
- **Purpose**: Analyze and optimize entire skill
- **Trigger**: Post-project (Phase 12)
- **Output**: Mutations, evolution events
- **Integration**: Direct evolution application

## Manual Evolution

Besides automatic triggers, you can manually trigger evolution:

### Trigger Manual Evolution

```bash
# Basic evolution
python scripts/trigger_evolution.py

# Evolution with project context
python scripts/trigger_evolution.py /path/to/project

# Evolution with specific signals
python scripts/trigger_evolution.py --signals memory_missing,pattern_gap
```

### Advanced: Direct Evolver Commands

```bash
cd C:\Users\91216\.claude\skills\capability-evolver

# Run evolution on Super-Skill
node index.js run --target C:\Users\91216\.claude\skills\super-skill

# Solidify evolution (apply changes)
node index.js solidify

# Start mad-dog mode (continuous loop)
node index.js --loop
```

## Best Practices

### 1. Let Evolution Run Automatically
- Don't disable auto-evolution
- Allow Super-Skill to learn from each project
- Review evolution summaries periodically

### 2. Provide Feedback
- When something works well, note it
- When something fails, report it
- User feedback weights evolution priority

### 3. Monitor Evolution Quality
- Check EVOLUTION_SUMMARY.md after each project
- Verify changes are beneficial
- Rollback if problematic

### 4. Maintain Backups
- Always backup before major changes
- Keep multiple evolution versions
- Test rollbacks periodically

### 5. Balance Innovation and Stability
- Use `adaptive` personality for normal projects
- Use `conservative` for critical production
- Use `experimental` for R&D projects

## Troubleshooting

### Evolution Not Triggering

**Symptom**: Phase 12 completes, no evolution occurs

**Solutions**:
1. Check evolver installation: `python scripts/check_evolver.py`
2. Verify .env.super-skill configuration
3. Check evolution.log for errors
4. Ensure Node.js is installed

### Evolution Errors

**Symptom**: Evolution fails with errors

**Solutions**:
1. Check evolver is functional
2. Verify file permissions
3. Check for disk space
4. Review evolution.log details

### Rollback Issues

**Symptom**: Cannot rollback to previous version

**Solutions**:
1. Check .evolution-backups/ directory
2. Verify backup integrity
3. Use skill-version-manager as fallback

### Quality Degradation

**Symptom**: Super-Skill performance declines after evolution

**Solutions**:
1. Rollback to previous version
2. Report issue to evolver
3. Adjust .env.super-skill strategy to `conservative`
4. Disable auto-apply temporarily

## Future Enhancements

Planned evolution capabilities:

1. **Multi-Skill Evolution**: Evolve multiple skills together
2. **Cross-Project Learning**: Learn across different projects
3. **Predictive Evolution**: Anticipate needed improvements
4. **Collaborative Evolution**: Share patterns across instances
5. **Evolution Marketplace**: Exchange successful mutations

## Support

For evolution-related issues:
1. Check EVOLUTION_SUMMARY.md for details
2. Review evolution.log for diagnostics
3. Use check_evolver.py for verification
4. Consult Capability-Evolver documentation

---

**Super-Skill V3.1: Self-Evolving AI-Native Development Orchestrator**

*Continuous evolution. Unlimited potential.*
