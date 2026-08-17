# darwin-evolution — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
