---
name: darwin-evolution
description: Darwin Gödel Machine inspired self-evolution system for AI skills. Enables iterative self-improvement through open-ended exploration, archive-based evolution, and benchmark-driven optimization. Integrates with Super-Skill Phase 12 for continuous capability enhancement.
tags: [self-evolution, darwin, godel, optimization, learning, autonomous-improvement]
version: 1.0.0
source: Inspired by arXiv:2505.22954 (Darwin Gödel Machine), Automaton self-sustaining AI
integrated-with: super-skill v3.6+
---

# Darwin Evolution Skill

This skill implements a **Darwin Gödel Machine (DGM)** inspired self-evolution system that enables Super-Skill to iteratively modify and improve its own codebase through open-ended exploration and benchmark-driven optimization.

## Core Philosophy

### The Darwin Gödel Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                    DARWIN GÖDEL MACHINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. SELF-MODIFICATION                                         │
│      ↓                                                         │
│   2. BENCHMARK EVALUATION                                      │
│      ↓                                                         │
│   3. ARCHIVE SUCCESSFUL MUTATIONS                              │
│      ↓                                                         │
│   4. OPEN-ENDED EXPLORATION                                    │
│      ↓                                                         │
│   5. REPEAT (EVOLUTION CONTINUES)                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics from Research

| Benchmark | Before DGM | After DGM | Improvement |
|-----------|------------|-----------|-------------|
| SWE-bench | 20.0% | 50.0% | +150% |
| Polyglot | 14.2% | 30.7% | +116% |
| HumanEval | Baseline | +15% | Significant |

## Architecture

### Evolution Pipeline

```python
class DarwinEvolutionEngine:
    """
    Self-evolution engine inspired by Darwin Gödel Machine.
    """

    def __init__(self, target_skill_path: str):
        self.target_path = target_skill_path
        self.archive = EvolutionArchive()
        self.benchmark = BenchmarkSuite()
        self.mutation_engine = MutationEngine()
        self.generation = 0
        self.best_fitness = 0

    async def evolve(self, max_generations: int = 50) -> dict:
        """
        Main evolution loop.
        """
        results = {
            'generations': [],
            'best_version': None,
            'improvements': []
        }

        for gen in range(max_generations):
            self.generation = gen

            # Phase 1: Generate mutations
            mutations = await self.mutation_engine.generate_mutations(
                self.target_path,
                self.archive.get_diverse_candidates(n=5)
            )

            # Phase 2: Evaluate each mutation
            evaluated = []
            for mutation in mutations:
                fitness = await self.benchmark.evaluate(mutation)
                evaluated.append({
                    'mutation': mutation,
                    'fitness': fitness,
                    'generation': gen
                })

            # Phase 3: Archive successful mutations
            for result in evaluated:
                if result['fitness'] > self.best_fitness:
                    self.archive.add(result)
                    self.best_fitness = result['fitness']
                    results['improvements'].append(result)

            # Phase 4: Apply best mutation if improvement
            best_current = max(evaluated, key=lambda x: x['fitness'])
            if best_current['fitness'] > self.best_fitness * 0.95:
                await self.apply_mutation(best_current['mutation'])

            results['generations'].append({
                'gen': gen,
                'best_fitness': best_current['fitness'],
                'avg_fitness': sum(e['fitness'] for e in evaluated) / len(evaluated)
            })

            # Phase 5: Check convergence
            if self.check_convergence(results):
                break

        results['best_version'] = self.archive.get_best()
        return results
```

### Mutation Engine

```python
class MutationEngine:
    """
    Generates diverse mutations for self-improvement.
    """

    MUTATION_TYPES = [
        'prompt_refinement',      # Improve prompt clarity
        'workflow_optimization',  # Streamline phases
        'skill_addition',         # Add new capabilities
        'skill_merger',           # Combine redundant skills
        'error_handling',         # Improve robustness
        'documentation_update',   # Enhance clarity
        'performance_tuning',     # Optimize execution
        'pattern_extraction',     # Extract reusable patterns
    ]

    async def generate_mutations(
        self,
        target_path: str,
        parent_candidates: list
    ) -> list[Mutation]:
        """
        Generate diverse mutations based on successful patterns.
        """
        mutations = []

        # Analyze current skill
        current_skill = await self.load_skill(target_path)
        skill_analysis = await self.analyze_skill(current_skill)

        # Generate mutations based on analysis
        for mutation_type in self.MUTATION_TYPES:
            mutation = await self.create_mutation(
                current_skill,
                mutation_type,
                parent_candidates,
                skill_analysis
            )
            if mutation:
                mutations.append(mutation)

        return mutations

    async def create_mutation(
        self,
        skill: Skill,
        mutation_type: str,
        parents: list,
        analysis: dict
    ) -> Mutation | None:
        """
        Create a specific type of mutation.
        """
        if mutation_type == 'prompt_refinement':
            return await self.refine_prompts(skill, analysis)
        elif mutation_type == 'workflow_optimization':
            return await self.optimize_workflow(skill, analysis)
        elif mutation_type == 'skill_addition':
            return await self.suggest_new_skills(skill, analysis)
        elif mutation_type == 'skill_merger':
            return await self.merge_redundant_skills(skill, analysis)
        # ... other mutation types
```

### Evolution Archive

```python
class EvolutionArchive:
    """
    Maintains a tree of evolved agents with their fitness scores.
    Inspired by DGM's archive of coding agents.
    """

    def __init__(self, archive_path: str = ".evolution_archive"):
        self.archive_path = archive_path
        self.tree = {}  # agent_id -> agent_info
        self.fitness_history = []

    def add(self, agent_result: dict) -> str:
        """
        Add a new agent to the archive.
        """
        agent_id = generate_uuid()

        self.tree[agent_id] = {
            'id': agent_id,
            'parent': agent_result.get('parent_id'),
            'mutation': agent_result['mutation'],
            'fitness': agent_result['fitness'],
            'generation': agent_result['generation'],
            'timestamp': datetime.now().isoformat(),
            'snapshot': self.capture_snapshot(agent_result['mutation'])
        }

        self.fitness_history.append({
            'agent_id': agent_id,
            'fitness': agent_result['fitness'],
            'generation': agent_result['generation']
        })

        return agent_id

    def get_diverse_candidates(self, n: int = 5) -> list:
        """
        Select diverse candidates for next evolution round.
        Uses fitness-proportional selection with diversity bonus.
        """
        candidates = list(self.tree.values())

        # Sort by fitness
        candidates.sort(key=lambda x: x['fitness'], reverse=True)

        # Select top performers with diversity consideration
        selected = []
        for candidate in candidates:
            if len(selected) >= n:
                break

            # Check diversity against already selected
            if self.is_diverse(candidate, selected):
                selected.append(candidate)

        return selected

    def is_diverse(self, candidate: dict, selected: list) -> bool:
        """
        Check if candidate is sufficiently different from selected ones.
        """
        if not selected:
            return True

        for s in selected:
            similarity = self.compute_similarity(
                candidate['mutation'],
                s['mutation']
            )
            if similarity > 0.8:  # Too similar
                return False

        return True

    def get_best(self) -> dict:
        """
        Return the best agent from the archive.
        """
        if not self.tree:
            return None
        return max(self.tree.values(), key=lambda x: x['fitness'])
```

### Benchmark Suite

```python
class BenchmarkSuite:
    """
    Evaluates skill performance on standardized benchmarks.
    """

    BENCHMARKS = {
        'code_generation': CodeGenerationBenchmark(),
        'bug_fixing': BugFixingBenchmark(),
        'architecture_design': ArchitectureBenchmark(),
        'requirement_analysis': RequirementBenchmark(),
        'test_coverage': TestCoverageBenchmark(),
        'documentation_quality': DocumentationBenchmark(),
    }

    async def evaluate(self, mutation: Mutation) -> float:
        """
        Evaluate mutation across all benchmarks.
        Returns weighted fitness score.
        """
        scores = {}

        for name, benchmark in self.BENCHMARKS.items():
            score = await benchmark.run(mutation)
            scores[name] = score

        # Weighted average (can be customized)
        weights = {
            'code_generation': 0.25,
            'bug_fixing': 0.20,
            'architecture_design': 0.15,
            'requirement_analysis': 0.15,
            'test_coverage': 0.15,
            'documentation_quality': 0.10
        }

        fitness = sum(
            scores[k] * weights[k]
            for k in scores
        )

        return fitness
```

## Integration with Super-Skill

### Phase 12 Enhancement

```yaml
# Enhanced Phase 12 with Darwin Evolution
phase_12_evolution:
  trigger: project_completion

  steps:
    - name: Capture Session Learnings
      action: extract_patterns
      output: SESSION_LEARNINGS.md

    - name: Initialize Evolution
      action: darwin_init
      params:
        target: super-skill
        max_generations: 10

    - name: Generate Mutations
      action: mutate
      params:
        types:
          - prompt_refinement
          - workflow_optimization
          - skill_addition

    - name: Evaluate Mutations
      action: benchmark
      params:
        benchmarks:
          - code_generation
          - bug_fixing
          - architecture_design

    - name: Archive Improvements
      action: archive
      condition: fitness_improvement > 0.05

    - name: Apply Best Mutation
      action: apply
      condition: fitness > current_best

    - name: Update Version
      action: version_bump
      format: "{major}.{minor}.{patch}"
```

### Automatic Evolution Triggers

```python
EVOLUTION_TRIGGERS = {
    # Triggered after every project
    'project_completion': {
        'enabled': True,
        'max_generations': 5,
        'mutation_types': ['prompt_refinement', 'pattern_extraction']
    },

    # Triggered when critical lessons learned
    'critical_lesson': {
        'enabled': True,
        'max_generations': 3,
        'focus': 'error_handling'
    },

    # Triggered when new pattern discovered
    'pattern_discovery': {
        'enabled': True,
        'max_generations': 2,
        'focus': 'skill_addition'
    },

    # Manual trigger for major updates
    'manual_upgrade': {
        'enabled': True,
        'max_generations': 50,
        'mutation_types': 'all'
    }
}
```

## Safety Mechanisms

### Constitutional Constraints

```python
CONSTITUTION = {
    'immutable_rules': [
        "Never modify core safety constraints",
        "Always maintain backward compatibility",
        "Never remove phase gate checks",
        "Always preserve user interaction points",
        "Never bypass quality gates"
    ],

    'mutation_limits': {
        'max_file_changes': 10,
        'max_line_changes': 500,
        'forbidden_files': [
            'CONSTITUTION.py',
            'safety_constraints.json'
        ]
    },

    'rollback_triggers': [
        'benchmark_regression > 10%',
        'critical_test_failure',
        'safety_constraint_violation'
    ]
}

class ConstitutionalGuard:
    """
    Ensures mutations respect constitutional constraints.
    """

    def validate_mutation(self, mutation: Mutation) -> bool:
        """
        Validate mutation against constitutional rules.
        """
        # Check immutable rules
        for rule in CONSTITUTION['immutable_rules']:
            if self.violates_rule(mutation, rule):
                return False

        # Check mutation limits
        changes = mutation.get_changes()
        if len(changes['files']) > CONSTITUTION['mutation_limits']['max_file_changes']:
            return False

        # Check forbidden files
        for forbidden in CONSTITUTION['mutation_limits']['forbidden_files']:
            if forbidden in changes['files']:
                return False

        return True
```

### Sandbox Execution

```python
class SandboxExecutor:
    """
    Executes mutations in isolated environment.
    """

    async def test_mutation(self, mutation: Mutation) -> dict:
        """
        Test mutation in sandbox before applying.
        """
        # Create isolated environment
        sandbox = await self.create_sandbox()

        try:
            # Apply mutation in sandbox
            await sandbox.apply(mutation)

            # Run tests
            test_results = await sandbox.run_tests()

            # Run benchmarks
            benchmark_results = await sandbox.run_benchmarks()

            return {
                'success': test_results['passed'],
                'fitness': benchmark_results['fitness'],
                'side_effects': await sandbox.detect_side_effects()
            }

        finally:
            # Cleanup sandbox
            await sandbox.destroy()
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
| 20         | 0.78         | 0.74        | +20.0%      |
| 30         | 0.82         | 0.79        | +26.2%      |
| Current    | {best}       | {avg}       | +{improvement}% |

### Mutation Type Effectiveness
| Mutation Type      | Applications | Success Rate | Avg Improvement |
|--------------------|--------------|--------------|-----------------|
| prompt_refinement  | 45           | 67%          | +3.2%           |
| workflow_optimize  | 32           | 75%          | +5.1%           |
| skill_addition     | 18           | 83%          | +7.8%           |
| error_handling     | 28           | 71%          | +4.5%           |

### Active Archive
- Total Agents: {archive_size}
- Unique Mutations: {unique_count}
- Best Performer: {best_agent_id}
- Evolution Path Depth: {path_depth}
```

## Best Practices

### 1. Evolution Strategy
- Start with small, focused mutations
- Maintain diversity in archive
- Don't over-optimize for single benchmark
- Allow exploration of different paths

### 2. Benchmark Design
- Cover multiple skill dimensions
- Weight critical capabilities higher
- Include edge case handling
- Test real-world scenarios

### 3. Safety First
- Always test in sandbox
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
- [ ] Sandbox environment ready
- [ ] Rollback mechanism tested

### During Evolution
- [ ] Each mutation validated
- [ ] Sandbox testing passed
- [ ] No constitutional violations
- [ ] Progress being tracked

### After Evolution
- [ ] Best mutation identified
- [ ] Regression tests passed
- [ ] Documentation updated
- [ ] Version bumped appropriately

## Deliverables

- Evolution report with fitness improvements
- Updated skill files
- Archive of mutations
- Benchmark results

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.6 |

---

## References

- "Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Code" (arXiv:2505.22954)
- Automaton: Self-Sustaining AI Agent
- "Self-Evolving LLMs via Continual Instruction Tuning" (arXiv:2509.18133)
