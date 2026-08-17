# prompt-engineering — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Prompt Optimization

### Iterative Refinement

```python
class PromptOptimizer:
    """
    Iteratively refine prompts based on performance.
    """

    def __init__(
        self,
        initial_prompt: str,
        evaluation_criteria: List[str]
    ):
        self.prompt = initial_prompt
        self.criteria = evaluation_criteria
        self.history = []

    async def evaluate_and_refine(
        self,
        test_cases: List[dict],
        model: Any,
        iterations: int = 5
    ) -> str:
        """
        Evaluate prompt performance and refine.
        """
        for i in range(iterations):
            # Test current prompt
            results = await self.evaluate(test_cases, model)

            # Identify weaknesses
            weaknesses = self.analyze_results(results)

            if not weaknesses:
                break

            # Generate refined prompt
            self.prompt = await self.refine_prompt(
                self.prompt,
                weaknesses,
                model
            )

            self.history.append({
                "iteration": i,
                "prompt": self.prompt,
                "results": results
            })

        return self.prompt

    async def evaluate(
        self,
        test_cases: List[dict],
        model: Any
    ) -> List[dict]:
        """
        Evaluate prompt on test cases.
        """
        results = []
        for case in test_cases:
            response = await model.generate(
                self.prompt.format(input=case["input"])
            )
            results.append({
                "input": case["input"],
                "expected": case["expected"],
                "actual": response,
                "correct": self.check_correctness(response, case["expected"])
            })
        return results
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Chain-of-Thought Paper](https://arxiv.org/abs/2201.11903)
- [Self-Consistency Paper](https://arxiv.org/abs/2203.11171)
- [Least-to-Most Paper](https://arxiv.org/abs/2205.10625)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
