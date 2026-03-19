---
name: darwin-evolution
description: Darwin Gödel Machine self-evolution system with GEP Protocol for AI skills. Enables iterative self-improvement through signal analysis, gene/capsule selection, protocol-constrained evolution, and benchmark-driven optimization. Core engine for Super-Skill Phase 12 continuous capability enhancement.
tags: [self-evolution, darwin, godel, gep-protocol, optimization, learning, autonomous-improvement]
version: 2.0.0
source: Inspired by arXiv:2505.22954 (Darwin Gödel Machine), arXiv:2509.18133, autogame-17/evolver
integrated-with: super-skill v3.7+
---

# Darwin Evolution Skill V2.0

A protocol-constrained self-evolution engine combining **Darwin Gödel Machine (DGM)** principles with **GEP (Genome Evolution Protocol)** for auditable, safe, and effective AI skill improvement.

## Core Philosophy

### The Self-Evolution Principle

```
+---------------------------------------------------------------+
|                  DARWIN GÖDEL MACHINE + GEP                   |
+---------------------------------------------------------------+
|                                                               |
|   1. SIGNAL EXTRACTION (from runtime history)                |
|      - Error signals (log_error, errsig)                      |
|      - Opportunity signals (feature_request, capability_gap)  |
|      - Stagnation signals (stable_success_plateau)            |
|      v                                                        |
|   2. GENE/SELECTION (pattern matching)                       |
|      - Match signals to Gene.signals_match                    |
|      - Select best Gene with drift control                    |
|      - Consider Capsule for past success                      |
|      v                                                        |
|   3. MUTATION BUILDING (controlled change)                   |
|      - Category: repair | optimize | innovate                 |
|      - Risk level: low | medium | high                        |
|      - Personality state adjustment                           |
|      v                                                        |
|   4. EXECUTION (apply changes)                               |
|      - Blast radius estimation                                |
|      - Targeted edits within constraints                      |
|      - Validation steps execution                             |
|      v                                                        |
|   5. SOLIDIFY (knowledge persistence)                        |
|      - Record EvolutionEvent                                  |
|      - Update Gene definitions                                |
|      - Create Capsule on success                              |
|      - Update Personality stats                               |
|      v                                                        |
|   6. ARCHIVE (continuous learning)                           |
|      - Fitness tracking                                       |
|      - Pattern accumulation                                   |
|      - Cross-skill learning                                   |
|      v                                                        |
|   7. REPEAT (evolution continues)                            |
|                                                               |
+---------------------------------------------------------------+
```

## GEP Protocol Objects

### 1. Mutation (The Trigger)

```json
{
  "type": "Mutation",
  "id": "mut_<timestamp>",
  "category": "repair|optimize|innovate",
  "trigger_signals": ["<signal_string>"],
  "target": "<module_or_gene_id>",
  "expected_effect": "<outcome_description>",
  "risk_level": "low|medium|high",
  "rationale": "<why_this_change_is_necessary>"
}
```

**Category Selection Logic:**
- `repair`: When error signals present (log_error, errsig)
- `optimize`: When protocol drift or stability issues
- `innovate`: When opportunity signals (user_feature_request, capability_gap)

### 2. PersonalityState (The Mood)

```json
{
  "type": "PersonalityState",
  "rigor": 0.0-1.0,        // Protocol compliance strictness
  "creativity": 0.0-1.0,   // Exploration vs exploitation
  "verbosity": 0.0-1.0,    // Output detail level
  "risk_tolerance": 0.0-1.0, // Willingness to try risky changes
  "obedience": 0.0-1.0     // Adherence to constraints
}
```

**Natural Selection:**
- Personality parameters evolve based on success/failure
- High-performing configurations are nudged towards
- Low-performing configurations are avoided

### 3. EvolutionEvent (The Record)

```json
{
  "type": "EvolutionEvent",
  "schema_version": "1.5.0",
  "id": "evt_<timestamp>",
  "parent": "<parent_evt_id|null>",
  "intent": "repair|optimize|innovate",
  "signals": ["<signal_string>"],
  "genes_used": ["<gene_id>"],
  "mutation_id": "<mut_id>",
  "personality_state": { ... },
  "blast_radius": { "files": N, "lines": N },
  "outcome": { "status": "success|failed", "score": 0.0-1.0 }
}
```

### 4. Gene (The Knowledge)

```json
{
  "type": "Gene",
  "schema_version": "1.5.0",
  "id": "gene_<name>",
  "category": "repair|optimize|innovate",
  "signals_match": ["<pattern>"],
  "preconditions": ["<condition>"],
  "strategy": ["<step_1>", "<step_2>"],
  "constraints": { "max_files": N, "forbidden_paths": [] },
  "validation": ["<node_command>"]
}
```

**Gene Types:**
- **Repair Genes**: Fix bugs, handle errors
- **Optimize Genes**: Improve performance, refactor
- **Innovate Genes**: Add features, explore new patterns

### 5. Capsule (The Result)

```json
{
  "type": "Capsule",
  "schema_version": "1.5.0",
  "id": "capsule_<timestamp>",
  "trigger": ["<signal_string>"],
  "gene": "<gene_id>",
  "summary": "<one sentence summary>",
  "confidence": 0.0-1.0,
  "blast_radius": { "files": N, "lines": N }
}
```

## Signal Detection System

### Defensive Signals

| Signal | Pattern | Action |
|--------|---------|--------|
| `log_error` | `[error]`, `error:`, `exception:` | Repair mode |
| `errsig:...` | TypeError, ReferenceError | Targeted repair |
| `recurring_error` | Same error 3+ times | Root cause fix |
| `memory_missing` | MEMORY.md incomplete | Documentation |
| `session_logs_missing` | No session logs | Archive creation |

### Opportunity Signals

| Signal | Pattern | Action |
|--------|---------|--------|
| `user_feature_request` | "add", "implement", "create" | Innovate mode |
| `user_improvement_suggestion` | "improve", "enhance" | Optimize mode |
| `perf_bottleneck` | "slow", "timeout" | Performance fix |
| `capability_gap` | "not supported", "missing" | Feature addition |
| `stable_success_plateau` | No errors, stable | Innovation push |

### Stagnation Signals

| Signal | Detection | Action |
|--------|-----------|--------|
| `evolution_stagnation_detected` | Repeated signals suppressed | Force innovation |
| `repair_loop_detected` | 3+ consecutive repairs | Switch to innovate |
| `empty_cycle_loop_detected` | 4+ zero-change cycles | Strategy shift |
| `force_innovation_after_repair_loop` | Repair exhaustion | Mandate innovate |

## Gene Selection Algorithm

### Selection Logic

```javascript
function selectGene(genes, signals, opts) {
  const bannedGeneIds = opts.bannedGeneIds || new Set();
  const preferredGeneId = opts.preferredGeneId || null;
  const driftIntensity = computeDriftIntensity(opts);

  // Score genes by signal matching
  const scored = genes
    .map(g => ({ gene: g, score: scoreGene(g, signals) }))
    .filter(x => x.score > 0 && !bannedGeneIds.has(x.gene.id))
    .sort((a, b) => b.score - a.score);

  if (scored.length === 0) return { selected: null, alternatives: [] };

  // Stochastic selection under drift
  if (driftIntensity > 0 && Math.random() < driftIntensity) {
    const topN = Math.min(scored.length, Math.ceil(scored.length * driftIntensity));
    const selectedIdx = Math.floor(Math.random() * topN);
    return { selected: scored[selectedIdx].gene, alternatives: scored.slice(0, 4).map(x => x.gene) };
  }

  return { selected: scored[0].gene, alternatives: scored.slice(1, 5).map(x => x.gene) };
}
```

### Drift Intensity

Population-size-dependent drift for exploration:

```
driftIntensity = 1 / sqrt(Ne)
```

Where `Ne` = effective population size (gene pool count)

- **Ne = 1**: intensity = 1.0 (pure drift/exploration)
- **Ne = 25**: intensity = 0.2
- **Ne = 100**: intensity = 0.1 (mostly selection)

## Default Genes

### Gene: gep_repair_from_errors

```json
{
  "type": "Gene",
  "id": "gene_gep_repair_from_errors",
  "category": "repair",
  "signals_match": ["error", "exception", "failed", "unstable"],
  "preconditions": ["signals contains error-related indicators"],
  "strategy": [
    "Extract structured signals from logs and user instructions",
    "Select an existing Gene by signals match (no improvisation)",
    "Estimate blast radius (files, lines) before editing",
    "Apply smallest reversible patch",
    "Validate using declared validation steps; rollback on failure",
    "Solidify knowledge: append EvolutionEvent, update Gene/Capsule store"
  ],
  "constraints": { "max_files": 20, "forbidden_paths": [".git", "node_modules"] }
}
```

### Gene: gep_optimize_prompt_and_assets

```json
{
  "type": "Gene",
  "id": "gene_gep_optimize_prompt_and_assets",
  "category": "optimize",
  "signals_match": ["protocol", "gep", "prompt", "audit", "reusable"],
  "preconditions": ["need stricter, auditable evolution protocol outputs"],
  "strategy": [
    "Extract signals and determine selection rationale via Selector JSON",
    "Prefer reusing existing Gene/Capsule; only create if no match exists",
    "Refactor prompt assembly to embed assets (genes, capsules, parent event)",
    "Reduce noise and ambiguity; enforce strict output schema",
    "Validate by running node index.js run and ensuring no runtime errors",
    "Solidify: record EvolutionEvent, update Gene definitions, create Capsule on success"
  ],
  "constraints": { "max_files": 20, "forbidden_paths": [".git", "node_modules"] }
}
```

### Gene: gep_innovate_from_opportunity

```json
{
  "type": "Gene",
  "id": "gene_gep_innovate_from_opportunity",
  "category": "innovate",
  "signals_match": [
    "user_feature_request",
    "user_improvement_suggestion",
    "perf_bottleneck",
    "capability_gap",
    "stable_success_plateau",
    "external_opportunity"
  ],
  "preconditions": [
    "at least one opportunity signal is present",
    "no active log_error signals (stability first)"
  ],
  "strategy": [
    "Extract opportunity signals and identify the specific user need or system gap",
    "Search existing Genes and Capsules for partial matches (avoid reinventing)",
    "Design a minimal, testable implementation plan (prefer small increments)",
    "Estimate blast radius; innovate changes may touch more files but must stay within constraints",
    "Implement the change with clear validation criteria",
    "Validate using declared validation steps; rollback on failure",
    "Solidify: record EvolutionEvent with intent=innovate, create new Gene if pattern is novel, create Capsule on success"
  ],
  "constraints": { "max_files": 25, "forbidden_paths": [".git", "node_modules", "assets/gep/events.jsonl"] }
}
```

## Operations Module

### Lifecycle Management

```bash
# Start evolver loop in background
node src/ops/lifecycle.js start

# Stop gracefully (SIGTERM -> SIGKILL)
node src/ops/lifecycle.js stop

# Check status
node src/ops/lifecycle.js status

# Health check + auto-restart if stagnant
node src/ops/lifecycle.js check
```

### Self-Repair

```javascript
// Automatic detection and repair of common issues
const selfRepair = {
  checkEmptySkillDirectories() { /* Clean up empty skill dirs */ },
  checkBrokenSymlinks() { /* Fix or remove broken symlinks */ },
  checkStaleLocks() { /* Remove stale lock files */ },
  checkOrphanedFiles() { /* Archive orphaned files */ }
};
```

### Skills Monitor

```javascript
// Monitor skill health and performance
const skillsMonitor = {
  scanSkillsDirectory() { /* List all skills */ },
  checkSkillHealth(skillPath) { /* Verify skill structure */ },
  reportSkillIssues() { /* Generate health report */ }
};
```

## Integration with Super-Skill

### Phase 12 Enhancement

```yaml
phase_12_evolution:
  trigger: project_completion

  steps:
    - name: Capture Session Learnings
      action: extract_patterns
      output: SESSION_LEARNINGS.md

    - name: Extract Signals
      action: extract_signals
      params:
        sources:
          - recentSessionTranscript
          - todayLog
          - memorySnippet
          - recentEvents

    - name: Select Gene/Capsule
      action: select_gene
      params:
        driftEnabled: false
        useMemoryGraph: true

    - name: Build Mutation
      action: build_mutation
      params:
        category: auto  # Based on signals

    - name: Select Personality
      action: select_personality
      params:
        naturalSelection: true

    - name: Execute Evolution
      action: execute_evolution
      params:
        maxBlastRadius: 60 files / 20000 lines

    - name: Validate Changes
      action: validate
      params:
        runTests: true
        runBenchmarks: true

    - name: Solidify Knowledge
      action: solidify
      params:
        recordEvent: true
        updateGene: true
        createCapsule: on_success

    - name: Update Version
      action: version_bump
      format: "{major}.{minor}.{patch}"
```

## Safety Mechanisms

### Constitutional Constraints

```yaml
immutable_rules:
  - "Never modify core safety constraints"
  - "Always maintain backward compatibility"
  - "Never bypass quality gates"
  - "Always validate before solidify"

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
```

## Evolution Metrics Dashboard

```markdown
## Evolution Status Report

### Current Generation: {generation}

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
| optimize           | 32           | 75%          | +5.1%           |
| innovate           | 18           | 83%          | +7.8%           |

### Signal Distribution (Last 30 Days)
| Signal Type        | Count | Avg Outcome Score |
|--------------------|-------|-------------------|
| log_error          | 23    | 0.72              |
| user_feature_request | 15  | 0.85              |
| perf_bottleneck    | 8     | 0.68              |

### Personality Evolution
| Parameter      | Start | Current | Trend |
|----------------|-------|---------|-------|
| rigor          | 0.70  | 0.75    | +     |
| creativity     | 0.35  | 0.42    | +     |
| risk_tolerance | 0.40  | 0.38    | -     |

### Active Archive
- Total Evolution Events: {events_count}
- Unique Genes: {genes_count}
- Successful Capsules: {capsules_count}
- Best Performing Gene: {best_gene_id}
```

## Strategy Presets

```bash
# Balanced evolution (default)
EVOLVE_STRATEGY=balanced node index.js --loop

# Maximize innovation
EVOLVE_STRATEGY=innovate node index.js --loop

# Focus on stability
EVOLVE_STRATEGY=harden node index.js --loop

# Emergency fix mode only
EVOLVE_STRATEGY=repair-only node index.js --loop

# Early stabilization (avoid experiments)
EVOLVE_STRATEGY=early-stabilize node index.js --loop

# Steady-state maintenance (minimal changes)
EVOLVE_STRATEGY=steady-state node index.js --loop

# Auto-select based on signals
EVOLVE_STRATEGY=auto node index.js --loop
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EVOLVE_STRATEGY` | `balanced` | Evolution strategy preset |
| `EVOLVE_ALLOW_SELF_MODIFY` | `false` | Allow evolver to modify itself (dangerous) |
| `EVOLVE_LOAD_MAX` | `2.0` | Max load average before backoff |
| `EVOLVE_REPORT_TOOL` | `message` | Reporting tool for status |
| `GEP_PROMPT_MAX_CHARS` | `50000` | Max prompt size in characters |

### Asset Files

```
assets/gep/
  |- genes.json       # Gene definitions
  |- capsules.json    # Success capsules
  |- events.jsonl     # Append-only evolution events
```

## Best Practices

### 1. Evolution Strategy
- Start with small, focused mutations
- Maintain diversity in gene pool
- Don't over-optimize for single benchmark
- Allow exploration of different paths

### 2. Signal Interpretation
- Error signals always take priority
- Opportunity signals trigger innovation only when stable
- Stagnation signals force strategy change

### 3. Safety First
- Always validate in sandbox
- Maintain rollback capability
- Respect constitutional limits
- Monitor for regressions

### 4. Continuous Learning
- Archive all mutations (successful and failed)
- Analyze failure patterns
- Extract reusable improvements
- Share learnings across skills

## Checklist

### Before Evolution
- [ ] Benchmarks defined and validated
- [ ] Constitutional constraints set
- [ ] Rollback mechanism tested
- [ ] Asset files initialized

### During Evolution
- [ ] Each mutation validated
- [ ] Blast radius within limits
- [ ] No constitutional violations
- [ ] Progress being tracked

### After Evolution
- [ ] EvolutionEvent recorded
- [ ] Gene/Capsule updated
- [ ] Documentation updated
- [ ] Version bumped appropriately

## Deliverables

- Evolution report with fitness improvements
- Updated skill files
- Archive of mutations in events.jsonl
- Updated genes.json and capsules.json

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-03-03 | Integrated GEP Protocol from autogame-17/evolver |
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.6 |

---

## References

- "Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Code" (arXiv:2505.22954)
- "Self-Evolving LLMs via Continual Instruction Tuning" (arXiv:2509.18133)
- autogame-17/evolver: https://github.com/autogame-17/evolver
- EvoMap Network: https://evomap.ai
