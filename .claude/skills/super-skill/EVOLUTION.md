# Super-Skill Evolution System V2.0

## Overview

Super-Skill V3.8 integrates **GEP Protocol (Genome Evolution Protocol)** from autogame-17/evolver for continuous self-optimization and evolution. This system enables Super-Skill to learn from every project execution and automatically improve its capabilities through protocol-constrained, auditable evolution.

## Architecture

```
+---------------------------------------------------------------+
|                    Super-Skill V3.8                              |
|                  Self-Evolving Orchestrator                             |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                   14-Phase Workflow                                  |
|  Phase 0 -> Phase 1 -> ... -> Phase 11 -> Phase 12               |
|  (Visionary)  (Feasibility)        (Deployment)  (Evolution)      |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|              Phase 12: Evolution Trigger                               |
|    - Project completion analysis                                    |
|    - Signal extraction & de-duplication                             |
|    - Pattern identification                                           |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|              GEP Protocol Engine (from autogame-17/evolver)            |
|    - Signal Analysis (signals.js)                                   |
|    - Gene/Capsule Selection (selector.js)                            |
|    - Mutation Building (mutation.js)                                |
|    - Personality State (personality.js)                              |
|    - Evolution Archive (events.jsonl)                                |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                   Enhanced Super-Skill                               |
|    - Updated MEMORY.md                                             |
|    - Enhanced CHANGELOG.md                                         |
|    - Optimized workflow steps                                       |
|    - New version (V3.8.x)                                           |
+---------------------------------------------------------------+
```

## GEP Protocol Components

### 1. Signal Extraction (signals.js)

**Purpose**: Extract meaningful signals from runtime history

**Signal Types**:

| Category | Signals | Action |
|----------|---------|--------|
| **Defensive** | `log_error`, `errsig:*`, `recurring_error` | Repair mode |
| **Opportunity** | `user_feature_request`, `capability_gap`, `stable_success_plateau` | Innovate mode |
| **Stagnation** | `evolution_stagnation_detected`, `repair_loop_detected` | Force innovate |
| **System** | `memory_missing`, `session_logs_missing` | Documentation |

**De-duplication Logic**:
- Suppresses signals appearing 3+ times in last 8 events
- Prevents repair loops
- Forces innovation after 3+ consecutive repairs

### 2. Gene/Capsule Selection (selector.js)

**Purpose**: Match signals to evolution strategies

**Selection Process**:
```
1. Score genes by signal pattern matching
2. Filter banned genes (from failure streaks)
3. Apply drift intensity (population-dependent exploration)
4. Select preferred gene if memory graph advises
5. Return selected gene + alternatives
```

**Drift Intensity Formula**:
```
driftIntensity = 1 / sqrt(Ne)
```
- Ne = 1: intensity = 1.0 (pure drift/exploration)
- Ne = 25: intensity = 0.2
- Ne = 100: intensity = 0.1 (mostly selection)

### 3. Mutation Building (mutation.js)

**Purpose**: Generate controlled change directives

**Mutation Categories**:
| Category | Trigger | Risk Level |
|----------|---------|------------|
| `repair` | Error signals | low |
| `optimize` | Protocol drift, stability | low |
| `innovate` | Opportunity signals | medium |

**Safety Constraints**:
- High-risk personality + innovate = downgrade to optimize
- High-risk mutation requires strict personality constraints
- Forbidden: innovate + high-risk personality combination

### 4. Personality State (personality.js)

**Purpose**: Track and evolve behavioral parameters

**Parameters**:
| Parameter | Range | Effect |
|-----------|-------|--------|
| `rigor` | 0.0-1.0 | Protocol compliance strictness |
| `creativity` | 0.0-1.0 | Exploration vs exploitation |
| `verbosity` | 0.0-1.0 | Output detail level |
| `risk_tolerance` | 0.0-1.0 | Willingness for risky changes |
| `obedience` | 0.0-1.0 | Constraint adherence |

**Natural Selection**:
- High-performing configurations are nudged towards
- Low-performing configurations are avoided
- Stats tracked per personality key

## Asset Files

### genes.json
**Location**: `assets/gep/genes.json`

**Default Genes**:
1. `gene_gep_repair_from_errors` - Fix bugs and errors
2. `gene_gep_optimize_prompt_and_assets` - Improve protocol efficiency
3. `gene_gep_innovate_from_opportunity` - Add new features
4. `gene_gep_skill_creation` - Create new skills
5. `gene_gep_documentation_update` - Update documentation

**Structure**:
```json
{
  "type": "Gene",
  "id": "gene_<name>",
  "category": "repair|optimize|innovate",
  "signals_match": ["pattern"],
  "preconditions": ["condition"],
  "strategy": ["step_1", "step_2"],
  "constraints": { "max_files": N, "forbidden_paths": [] },
  "validation": ["node command"]
}
```

### capsules.json
**Location**: `assets/gep/capsules.json`

**Purpose**: Store successful evolution results for reuse

**Structure**:
```json
{
  "type": "Capsule",
  "id": "capsule_<timestamp>",
  "trigger": ["signal_string"],
  "gene": "<gene_id>",
  "summary": "<one sentence summary>",
  "confidence": 0.0-1.0,
  "blast_radius": { "files": N, "lines": N }
}
```

### events.jsonl
**Location**: `assets/gep/events.jsonl`

**Purpose**: Append-only evolution event log

**Structure** (one per line):
```json
{
  "type": "EvolutionEvent",
  "id": "evt_<timestamp>",
  "parent": "<parent_evt_id|null>",
  "intent": "repair|optimize|innovate",
  "signals": ["signal"],
  "genes_used": ["gene_id"],
  "mutation_id": "<mut_id>",
  "personality_state": { ... },
  "blast_radius": { "files": N, "lines": N },
  "outcome": { "status": "success|failed", "score": 0.0-1.0 }
}
```

## Evolution Triggers

### 1. Project Completion (Auto)
- **Trigger**: After Phase 12 completion
- **Action**: Extract signals from project execution
- **Analysis**: Success metrics, issues encountered, patterns identified
- **Outcome**: Super-Skill learns from project execution

**Process**:
```
1. Extract signals from:
   - Recent session transcript
   - Today's log
   - Memory snippet
   - Recent events history
2. Analyze recent history for de-duplication
3. Select gene/capsule based on signals
4. Build mutation with category and risk level
5. Select personality state
6. Execute evolution cycle
7. Solidify knowledge:
```

### 2. Critical Learning Event (Auto)
- **Trigger**: Discovery of significant new patterns
- **Action**: Immediate evolution session
- **Analysis**: New patterns, successful solutions, pitfalls
- **Outcome**: Knowledge base updated with new insights
**Trigger Signals**:
- `pattern_discovery`
- `critical_lesson`
- `breakthrough_solution`
- `failure_pattern_identified`

### 3. User Feedback (Manual)
- **Trigger**: User provides explicit feedback
- **Action**: Targeted evolution on specific area
- **Analysis**: User's observations and suggestions
- **Outcome**: User-requested improvements prioritized
**How to Trigger**:
```bash
# Evolution with specific signals
EVOLVE_HINT="focus on workflow optimization" node scripts/trigger_evolution.py

# Evolution with strategy override
EVOLVE_STRATEGY=innovate node scripts/trigger_evolution.py
```

### 4. Periodic Review (Scheduled)
- **Trigger**: Every 5 projects or 7 days
- **Action**: Comprehensive evolution session
- **Analysis**: All recent projects, patterns, trends
- **Outcome**: Major optimization release
**Scheduling**:
```yaml
periodic_evolution:
  enabled: true
  interval: 5 projects or 7 days
  strategy: balanced
  max_mutations: 10
```

## Evolution Workflow

### Phase 12: Evolution Execution

```bash
# Triggered automatically after project completion
cd C:\Users\91216\.claude\skills\super-skill

# Step 1: Extract signals from project
node scripts/extract_signals.js <project-dir>

# Step 2: Analyze recent history for de-duplication
node scripts/analyze_history.js

# Step 3: Select gene/capsule
node scripts/select_gene.js

# Step 4: Build mutation
node scripts/build_mutation.js

# Step 5: Select personality state
node scripts/select_personality.js

# Step 6: Execute evolution cycle
node scripts/execute_evolution.js

# Step 7: Solidify knowledge
node scripts/solidify_evolution.js

# Step 8: Update version (if significant changes)
node scripts/update_version.js
```

## Configuration Files

### `.env.super-skill`
Evolution configuration for Super-Skill:
```bash
# Evolution Strategy
EVOLVE_STRATEGY=balanced

# Self-modification (dangerous - not recommended)
EVOLVE_ALLOW_SELF_MODIFY=false

# Auto-apply improvements
EVOLVE_AUTO_APPLY=true

# Create backups before evolution
EVOLVE_BACKUP=true

# Max load average before backoff
EVOLVE_LOAD_MAX=2.0

# Reporting tool
EVOLVE_REPORT_TOOL=message

# Prompt max characters
GEP_PROMPT_MAX_CHARS=50000
```

### Strategy Presets

| Strategy | Description | Repair | Optimize | Innovate |
|----------|-------------|--------|----------|----------|
| `balanced` | Default balanced evolution | Medium | Medium | Medium |
| `innovate` | Maximize innovation | Low | Low | High |
| `harden` | Focus on stability | High | Medium | Low |
| `repair-only` | Emergency fix mode only | High | Low | None |
| `early-stabilize` | Avoid experiments | Medium | High | Low |
| `steady-state` | Minimal changes | Low | Low | Very Low |
| `auto` | Auto-select based on signals | Dynamic | Dynamic | Dynamic |

**Usage**:
```bash
# Set strategy via environment variable
EVOLVE_STRATEGY=innovate node scripts/trigger_evolution.py

# Or via command line
node scripts/trigger_evolution.py --strategy innovate
```

## Safety Mechanisms

### Constitutional Constraints

```yaml
immutable_rules:
  - "Never modify core safety constraints"
  - "Always maintain backward compatibility"
  - "Never bypass quality gates"
  - "Always preserve user interaction points"

mutation_limits:
  max_file_changes: 60
  max_line_changes: 20000
  forbidden_files:
    - ".git/**"
    - "node_modules/**"
    - "assets/gep/events.jsonl"

rollback_triggers:
  - benchmark_regression > 10%
  - critical_test_failure
  - safety_constraint_violation
```

### Blast Radius Control

```yaml
blast_radius_policy:
  check_before_edit: true
  hard_cap:
    files: 60
    lines: 20000
  repair_mode:
    fix_only_broken: true
    no_reinstall: true
    prefer_targeted_edits: true
  warning_threshold: 80%  # Warn at 80% of max
  enforcement: STOP if exceeded
```
### Validation Command Safety
```yaml
validation_safety:
  prefix_whitelist:
    - "node"
    - "npm"
    - "npx"
  forbidden_patterns:
    - "backticks"
    - "$(...)"
    - shell_operators: [";", "&", "|", ">", "<"]
  timeout_seconds: 180
  scoped_execution: true
```
## Integration with Other Skills

### Darwin Evolution Skill (V2.0)
- **Purpose**: Self-evolution engine with GEP Protocol
- **Trigger**: During all phases (continuous learning)
- **Output**: Gene updates, Capsule creation, Evolution events
- **Integration**: Direct evolution application
**Key Features**:
- Signal extraction from runtime history
- Gene/Capsule selection with drift
- Mutation building with safety constraints
- Personality state evolution
- Evolution archive with fitness tracking

### Continuous Learning V2
- **Purpose**: Knowledge capture during workflow
- **Trigger**: All phases
- **Output**: Domain patterns, best practices
- **Integration**: Evolver incorporates into MEMORY.md
### Self-Evolving Skill
- **Purpose**: Pattern extraction and instinct creation
- **Trigger**: During project execution
- **Output**: Atomic instincts, confidence scores
- **Integration**: Evolver uses instincts as data

## Monitoring and Observability
### Evolution Metrics Dashboard
```markdown
## Evolution Status Report

### Current Version: V3.8.0

### Fitness Progress
| Generation | Best Fitness | Avg Fitness | Improvement |
|------------|--------------|-------------|-------------|
| 0          | 0.65         | 0.60        | -           |
| 10         | 0.72         | 0.68        | +10.8%      |
| Current    | {best}       | {avg}       | +{improvement}% |

### Mutation Type Effectiveness
| Mutation Type      | Applications | Success Rate | Avg Improvement |
|--------------------|--------------|--------------|-----------------|
| repair             | 45           | 67%          | +3.2%           |
| optimize            | 32           | 75%          | +5.1%           |
| innovate            | 18           | 83%          | +7.8%           |

### Signal Distribution (Last 30 Days)
| Signal Type          | Count | Avg Outcome Score |
|----------------------|-------|-------------------|
| log_error            | 23    | 0.72              |
| user_feature_request | 15    | 0.85              |
| perf_bottleneck      | 8     | 0.68              |

| stable_success_plateau | 12    | 0.78              |

### Personality Evolution
| Parameter      | Start | Current | Trend |
|----------------|-------|---------|-------|
| rigor          | 0.70  | 0.75    | +     |
| creativity     | 0.35  | 0.42    | +     |
| risk_tolerance | 0.40  | 0.38    | -     |
| obedience      | 0.85  | 0.82    | -     |

### Active Archive
- Total Evolution Events: {events_count}
- Unique Genes: 5
- Successful Capsules: {capsules_count}
- Best Performing Gene: gene_gep_innovate_from_opportunity
```
### View Evolution Status
```bash
# Check current evolution state
node scripts/evolution_status.js

# Output includes:
- Current version
- Last evolution timestamp
- Signals detected
- Mutations pending
- Personality state
- Fitness score
```
### View Evolution History
```bash
# Show evolution log
cat logs/evolution.log

# Or view evolution summary
cat EVOLUTION_SUMMARY.md
```
## Manual Evolution
### Trigger Manual Evolution
```bash
# Basic evolution
node scripts/trigger_evolution.py

# Evolution with project context
node scripts/trigger_evolution.js /path/to/project

# Evolution with specific signals
node scripts/trigger_evolution.js --signals memory_missing,pattern_gap

# Evolution with strategy override
EVOLVE_STRATEGY=innovate node scripts/trigger_evolution.py

# Force evolution (skip confirmation)
node scripts/trigger_evolution.py --force
```
### Rollback
```bash
# List available versions
node scripts/list_evolution_versions.py

# Rollback to specific version
node scripts/rollback_evolution.js V3.8.5

# Verify rollback
node scripts/check_evolution.js
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
- Check evolution metrics after each project
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
1. Check evolver installation: `node scripts/check_evolution.js`
2. Verify .env.super-skill configuration
3. Check logs/evolution.log for errors
4. Ensure Node.js is installed
### Evolution Errors
**Symptom**: Evolution fails with errors
**Solutions**:
1. Check evolver functionality
2. Verify file permissions
3. Check for disk space
4. Review logs/evolution.log for details
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
1. **Multi-Skill Evolution**: Evolve multiple skills together
2. **Cross-Project Learning**: Learn across different projects
3. **Predictive Evolution**: Anticipate needed improvements
4. **Collaborative Evolution**: Share patterns across instances
5. **Evolution Marketplace**: Exchange successful mutations
## Source Attribution

This evolution system integrates the **GEP Protocol** from:
- **Repository**: https://github.com/autogame-17/evolver
- **License**: MIT
- **Key Concepts**:
  - Signal extraction and de-duplication
  - Gene/Capsule selection with drift
  - Mutation building with safety constraints
  - Personality state evolution
  - Operations module (lifecycle, self-repair, monitoring)
---

**Super-Skill V3.8: Self-Evolving AI-Native Development Orchestrator with GEP Protocol**

*Protocol-constrained evolution. Auditable improvements. Unlimited potential.*
