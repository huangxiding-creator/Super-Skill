# advanced-reasoning — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
