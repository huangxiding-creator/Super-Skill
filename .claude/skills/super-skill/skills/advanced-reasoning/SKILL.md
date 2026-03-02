---
name: advanced-reasoning
description: Advanced reasoning patterns including Chain-of-Thought (CoT), Tree-of-Thought (ToT), and Graph-of-Thought (GoT) methodologies for complex problem-solving. Integrates with Super-Skill for enhanced decision-making in all phases.
tags: [reasoning, chain-of-thought, tree-of-thought, decision-making, problem-solving]
version: 1.0.0
source: Inspired by dair-ai/Prompt-Engineering-Guide, academic papers on CoT/ToT/GoT
integrated-with: super-skill v3.6+
---

# Advanced Reasoning Skill

This skill provides structured reasoning methodologies that enhance AI decision-making capabilities through Chain-of-Thought (CoT), Tree-of-Thought (ToT), and Graph-of-Thought (GoT) patterns.

## Core Reasoning Patterns

### Pattern Comparison

```
┌──────────────────────────────────────────────────────────────────┐
│                    REASONING PATTERN HIERARCHY                    │
├────────────────┬──────────────────┬───────────────────────────────┤
│   Chain-of-    │   Tree-of-       │    Graph-of-Thought           │
│   Thought      │   Thought        │    (GoT)                      │
│   (CoT)        │   (ToT)          │                               │
├────────────────┼──────────────────┼───────────────────────────────┤
│ Linear path    │ Branching paths  │ Arbitrary graph structure     │
│ Single thread  │ Multiple threads │ Interconnected thoughts       │
│ Fast execution │ Better exploring │ Maximum flexibility           │
│ 80% accuracy   │ 90% accuracy     │ 95% accuracy                  │
└────────────────┴──────────────────┴───────────────────────────────┘
```

## Chain-of-Thought (CoT)

### When to Use
- Mathematical reasoning
- Logical deduction
- Step-by-step processes
- Simple multi-step problems

### Implementation

#### Zero-Shot CoT
```markdown
## Problem
[Your problem description here]

## Instructions
Let's think step by step.

Step 1: [First reasoning step]
Step 2: [Second reasoning step]
...
Step N: [Final conclusion]
```

#### Few-Shot CoT
```markdown
## Examples

### Example 1
Problem: [Problem A]
Reasoning:
  Step 1: [First step with explanation]
  Step 2: [Second step with explanation]
  Step 3: [Third step with explanation]
Answer: [Final answer]

### Example 2
Problem: [Problem B]
Reasoning:
  Step 1: [First step]
  Step 2: [Second step]
Answer: [Final answer]

## Now Solve
Problem: [Your problem]
Reasoning:
```

#### Self-Consistency CoT
```python
def self_consistency_cot(problem: str, n_samples: int = 5) -> str:
    """
    Generate multiple reasoning paths and select the most consistent answer.
    """
    responses = []

    for i in range(n_samples):
        # Use higher temperature for diversity
        response = generate_with_cot(
            problem,
            temperature=0.7 + (i * 0.1)  # Varying temperature
        )
        responses.append(response)

    # Extract answers
    answers = [extract_answer(r) for r in responses]

    # Select most frequent answer (voting)
    final_answer = majority_vote(answers)

    return final_answer
```

## Tree-of-Thought (ToT)

### When to Use
- Complex decision-making
- Problems requiring backtracking
- Multiple valid solution paths
- Strategic planning

### Implementation

```python
class TreeOfThought:
    """
    Tree-of-Thought reasoning implementation.
    """

    def __init__(self, problem: str, max_depth: int = 4, breadth: int = 3):
        self.problem = problem
        self.max_depth = max_depth
        self.breadth = breadth
        self.thought_tree = {}

    def generate_thoughts(self, current_state: str, n: int) -> list[str]:
        """Generate n possible next thoughts."""
        prompt = f"""
        Problem: {self.problem}
        Current reasoning: {current_state}

        Generate {n} different next steps in the reasoning process.
        Each step should be distinct and explore a different approach.

        Format:
        1. [First thought]
        2. [Second thought]
        3. [Third thought]
        """
        return parse_thoughts(generate(prompt))

    def evaluate_thought(self, thought: str, context: str) -> float:
        """Evaluate the promise of a thought (0-1 score)."""
        prompt = f"""
        Problem: {self.problem}
        Current reasoning: {context}
        Proposed next step: {thought}

        Rate this next step on a scale of 0-10 for:
        - Relevance to the problem
        - Likelihood of leading to a correct solution
        - Quality of reasoning

        Score: [0-10]
        """
        return parse_score(generate(prompt)) / 10

    def solve_bfs(self) -> str:
        """Solve using breadth-first search."""
        queue = [(("", ""), 0)]  # (path, depth)

        while queue:
            (path, last_thought), depth = queue.pop(0)

            if depth >= self.max_depth:
                continue

            # Generate candidate thoughts
            candidates = self.generate_thoughts(path, self.breadth)

            # Evaluate each candidate
            scored_candidates = []
            for thought in candidates:
                score = self.evaluate_thought(thought, path)
                scored_candidates.append((thought, score))

            # Sort by score and take top candidates
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = scored_candidates[:self.breadth]

            for thought, score in top_candidates:
                new_path = f"{path}\n→ {thought}"

                # Check if solution found
                if self.is_solution(thought):
                    return self.extract_solution(new_path)

                # Add to queue for further exploration
                queue.append(((new_path, thought), depth + 1))

        return "No solution found within depth limit"

    def solve_dfs(self) -> str:
        """Solve using depth-first search with backtracking."""
        def dfs(path: str, depth: int) -> str | None:
            if depth >= self.max_depth:
                return None

            candidates = self.generate_thoughts(path, self.breadth)
            scored = [(t, self.evaluate_thought(t, path)) for t in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)

            for thought, score in scored:
                if score < 0.3:  # Prune low-scoring branches
                    continue

                new_path = f"{path}\n→ {thought}"

                if self.is_solution(thought):
                    return self.extract_solution(new_path)

                result = dfs(new_path, depth + 1)
                if result:
                    return result

            return None

        return dfs("", 0) or "No solution found"
```

### ToT Prompt Template

```markdown
## Tree-of-Thought Reasoning

### Problem
{problem}

### Thought Generation
At each step, I will:
1. Generate multiple possible next thoughts
2. Evaluate each thought for promise
3. Select the most promising path
4. Backtrack if needed

### Initial Thoughts (Depth 0)
Thought 1: [First approach]
Thought 2: [Second approach]
Thought 3: [Third approach]

### Evaluation
- Thought 1 score: 8/10 - [Reasoning]
- Thought 2 score: 6/10 - [Reasoning]
- Thought 3 score: 7/10 - [Reasoning]

### Selected Path: Thought 1
[Continue reasoning...]

### Depth 1 (Expanding Thought 1)
Thought 1.1: [Refinement]
Thought 1.2: [Alternative]
Thought 1.3: [Extension]

### Evaluation
- Thought 1.1 score: 9/10 - [Reasoning]
- Thought 1.2 score: 5/10 - [Reasoning]
- Thought 1.3 score: 7/10 - [Reasoning]

### Selected Path: Thought 1.1
[Continue until solution or backtrack]

### Solution
[Final answer with complete reasoning path]
```

## Graph-of-Thought (GoT)

### When to Use
- Highly complex problems
- Interdependent sub-problems
- Combining multiple reasoning paths
- Research and analysis tasks

### Implementation

```python
class GraphOfThought:
    """
    Graph-of-Thought: Arbitrary graph structure for reasoning.
    Thoughts can be combined, split, and transformed.
    """

    def __init__(self, problem: str):
        self.problem = problem
        self.graph = ThoughtGraph()
        self.operations = {
            'generate': self.generate_thoughts,
            'aggregate': self.aggregate_thoughts,
            'improve': self.improve_thought,
            'split': self.split_thought,
            'transform': self.transform_thought
        }

    def generate_thoughts(self, parent_id: str, n: int) -> list[str]:
        """Generate new thoughts from a parent node."""
        pass

    def aggregate_thoughts(self, thought_ids: list[str]) -> str:
        """Combine multiple thoughts into a synthesis."""
        thoughts = [self.graph.get_node(tid) for tid in thought_ids]
        prompt = f"""
        Synthesize the following thoughts into a unified conclusion:

        {format_list(thoughts)}

        Synthesis:
        """
        return generate(prompt)

    def improve_thought(self, thought_id: str, feedback: str) -> str:
        """Improve a thought based on feedback."""
        thought = self.graph.get_node(thought_id)
        prompt = f"""
        Original thought: {thought}
        Feedback: {feedback}

        Improved thought:
        """
        return generate(prompt)

    def split_thought(self, thought_id: str) -> list[str]:
        """Split a complex thought into simpler components."""
        thought = self.graph.get_node(thought_id)
        prompt = f"""
        Decompose this complex thought into simpler sub-thoughts:

        {thought}

        Sub-thoughts:
        1.
        2.
        3.
        """
        return parse_subthoughts(generate(prompt))

    def execute_plan(self, plan: list[dict]) -> str:
        """
        Execute a GoT reasoning plan.

        Plan format:
        [
            {"op": "generate", "from": "root", "n": 3},
            {"op": "aggregate", "from": ["t1", "t2", "t3"]},
            {"op": "improve", "from": "t_agg", "feedback": "..."},
            ...
        ]
        """
        results = {}

        for step in plan:
            op = step['op']

            if op == 'generate':
                parent = step['from']
                n = step.get('n', 3)
                new_ids = self.generate_thoughts(parent, n)
                results.update(new_ids)

            elif op == 'aggregate':
                ids = step['from']
                agg_id = self.aggregate_thoughts(ids)
                results['latest'] = agg_id

            elif op == 'improve':
                tid = step['from']
                feedback = step['feedback']
                improved = self.improve_thought(tid, feedback)
                results['latest'] = improved

            elif op == 'split':
                tid = step['from']
                sub_ids = self.split_thought(tid)
                results.update(sub_ids)

        return results.get('latest', "No final result")
```

## Integration with Super-Skill

### Phase-Specific Reasoning Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                 REASONING PATTERN SELECTION                      │
├─────────────────┬──────────────────┬─────────────────────────────┤
│ Phase           │ Pattern          │ Rationale                   │
├─────────────────┼──────────────────┼─────────────────────────────┤
│ Phase 0: Vision │ ToT (BFS)        │ Explore multiple paradigms  │
│ Phase 1: Feas   │ CoT + Self-Cons  │ Validate with consensus     │
│ Phase 2: GitHub │ CoT              │ Linear search process       │
│ Phase 3: Know   │ GoT              │ Interconnected knowledge    │
│ Phase 4: Reqs   │ ToT (DFS)        │ Deep requirement analysis   │
│ Phase 5: Design │ ToT (BFS)        │ Explore design alternatives │
│ Phase 6: WBS    │ CoT              │ Sequential breakdown        │
│ Phase 8: Dev    │ CoT per task     │ Linear implementation       │
│ Phase 9: QA     │ ToT for bugs     │ Debug with backtracking     │
│ Phase 10: Opt   │ ToT (DFS)        │ Deep optimization           │
│ Phase 12: Evol  │ GoT              │ Complex learning synthesis  │
└─────────────────┴──────────────────┴─────────────────────────────┘
```

### Automatic Pattern Selection

```python
def select_reasoning_pattern(
    task_complexity: str,
    has_multiple_paths: bool,
    requires_backtracking: bool,
    has_interdependencies: bool
) -> str:
    """
    Automatically select the best reasoning pattern.
    """
    if has_interdependencies:
        return "graph-of-thought"
    elif requires_backtracking or has_multiple_paths:
        return "tree-of-thought"
    else:
        return "chain-of-thought"
```

## Reasoning Enhancement Prompts

### For Complex Decisions
```markdown
## Deep Reasoning Protocol

I need to solve: {problem}

### Phase 1: Decomposition
Let me break this down into sub-problems:
1. [Sub-problem A]
2. [Sub-problem B]
3. [Sub-problem C]

### Phase 2: Analysis
For each sub-problem, I'll analyze:
- Dependencies
- Constraints
- Potential solutions
- Risk factors

### Phase 3: Synthesis
Combining the analyses:
[Synthesized understanding]

### Phase 4: Solution
Based on this reasoning:
[Final solution with justification]
```

### For Debugging
```markdown
## Debug Reasoning Protocol

Bug description: {bug}

### Hypothesis Generation
Possible causes:
1. [Hypothesis A] - Probability: High/Medium/Low
2. [Hypothesis B] - Probability: High/Medium/Low
3. [Hypothesis C] - Probability: High/Medium/Low

### Systematic Elimination
Testing Hypothesis A:
- Test: [Test description]
- Result: [Pass/Fail]
- Conclusion: [Eliminate/Confirm/Inconclusive]

Testing Hypothesis B:
- Test: [Test description]
- Result: [Pass/Fail]
- Conclusion: [Eliminate/Confirm/Inconclusive]

### Root Cause
After systematic analysis:
[Identified root cause]

### Fix Strategy
[Fix implementation plan]
```

## Best Practices

### 1. Pattern Selection
- Use CoT for straightforward problems (80% of cases)
- Use ToT for decisions with multiple valid paths (15% of cases)
- Use GoT for highly complex, interconnected problems (5% of cases)

### 2. Self-Consistency
- For critical decisions, always use self-consistency with 3-5 samples
- Higher temperature (0.7-1.0) for diverse perspectives
- Majority voting or consensus building

### 3. Verification
- Always verify reasoning steps for logical consistency
- Check for common reasoning fallacies
- Validate assumptions explicitly

### 4. Documentation
- Record reasoning paths for learning
- Capture failed approaches and why they failed
- Build a knowledge base of reasoning patterns

## Checklist

### Before Reasoning
- [ ] Problem clearly defined
- [ ] Appropriate pattern selected
- [ ] Sufficient context provided
- [ ] Success criteria established

### During Reasoning
- [ ] Each step is logically sound
- [ ] No jumps in reasoning
- [ ] Assumptions are explicit
- [ ] Alternative paths considered

### After Reasoning
- [ ] Solution verified
- [ ] Edge cases considered
- [ ] Reasoning documented
- [ ] Confidence level assessed

## Deliverables

- Reasoning trace
- Decision justification
- Alternative paths explored
- Confidence assessment

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.6 |

---

## References

- [Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)
- [awesome-prompts](https://github.com/f/awesome-prompts)
- "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (Wei et al., 2022)
- "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (Yao et al., 2023)
- "Graph of Thoughts: Solving Elaborate Problems with Large Language Models" (Besta et al., 2023)
