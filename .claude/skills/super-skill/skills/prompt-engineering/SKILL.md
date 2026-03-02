---
name: prompt-engineering
description: Advanced prompt engineering techniques for AI interactions. Covers Chain-of-Thought, Few-Shot, Self-Consistency, Least-to-Most, and structured prompting patterns.
tags: [prompt, engineering, llm, chain-of-thought, few-shot, self-consistency]
version: 1.0.0
source: Based on academic research, OpenAI, Anthropic best practices
integrated-with: super-skill v3.7+
---

# Prompt Engineering Skill

This skill provides advanced prompt engineering techniques for effective AI interactions, covering established patterns and emerging methodologies.

## Prompting Techniques

```
┌─────────────────────────────────────────────────────────────────┐
│                  PROMPT ENGINEERING TECHNIQUES                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ZERO-SHOT                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Direct instruction   • No examples    • Simple tasks  │    │
│  │ • "Classify this..."   • Fast           • Baseline      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  FEW-SHOT                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Example-based        • Pattern learning • In-context  │    │
│  │ • 2-5 examples         • Consistent format • Task-specific│  │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  CHAIN-OF-THOUGHT                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Step-by-step        • Reasoning visible • Complex     │    │
│  │ • "Let's think..."    • Intermediate steps • Math/Logic │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  SELF-CONSISTENCY                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Multiple paths      • Majority vote     • Robust      │    │
│  │ • Diverse sampling    • High accuracy     • Expensive   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LEAST-TO-MOST                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Decomposition       • Progressive       • Hierarchical│    │
│  │ • Sub-problems        • Build up          • Compositional│   │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Zero-Shot Prompting

### Basic Patterns

```markdown
## Classification
Classify the following text as positive, negative, or neutral sentiment:

Text: "{{input}}"
Sentiment:

## Extraction
Extract all email addresses from the following text:

Text: "{{input}}"
Emails:

## Summarization
Summarize the following article in 3 bullet points:

Article: "{{input}}"
Summary:
•
•
•

## Transformation
Convert the following text to {{format}}:

Text: "{{input}}"
Output:
```

## Few-Shot Prompting

### Pattern Template

```markdown
## Task Description
You are a helpful assistant that {{task_description}}.

## Examples

### Example 1
Input: {{example_1_input}}
Output: {{example_1_output}}

### Example 2
Input: {{example_2_input}}
Output: {{example_2_output}}

### Example 3
Input: {{example_3_input}}
Output: {{example_3_output}}

## Now Process
Input: {{actual_input}}
Output:
```

### Concrete Example

```markdown
## Sentiment Analysis

Analyze the sentiment of customer reviews. Classify as POSITIVE, NEGATIVE, or NEUTRAL.

### Examples

Review: "This product exceeded my expectations! Fast shipping and great quality."
Sentiment: POSITIVE

Review: "The item arrived damaged. Very disappointed with the purchase."
Sentiment: NEGATIVE

Review: "The product works as described. Nothing special but does the job."
Sentiment: NEUTRAL

### Analyze

Review: "{{input_review}}"
Sentiment:
```

## Chain-of-Thought (CoT)

### Zero-Shot CoT

```markdown
## Problem
{{problem}}

## Instructions
Let's think step by step.

Step 1:
```

### Few-Shot CoT

```markdown
## Math Problem Solver

Solve the following math problems step by step.

### Example 1
Problem: A bakery has 23 croissants. They sold 15 and baked 12 more. How many do they have now?

Solution:
- Starting croissants: 23
- Sold: 15
- Remaining after sales: 23 - 15 = 8
- Baked more: 12
- Final count: 8 + 12 = 20
Answer: 20 croissants

### Example 2
Problem: {{example_2}}

Solution:
{{example_2_solution}}

### Now Solve
Problem: {{actual_problem}}

Solution:
```

### Self-Consistency CoT

```python
import asyncio
from typing import List, Any

async def self_consistency_cot(
    problem: str,
    model: Any,
    n_samples: int = 5,
    temperature: float = 0.7
) -> dict:
    """
    Generate multiple reasoning paths and vote on the answer.
    """
    prompt_template = f"""
    Problem: {problem}

    Let's think step by step.
    """

    # Generate diverse reasoning paths
    responses = await asyncio.gather(*[
        model.generate(
            prompt_template,
            temperature=temperature + (i * 0.05)  # Vary temperature
        )
        for i in range(n_samples)
    ])

    # Extract answers from each response
    answers = [
        extract_final_answer(response)
        for response in responses
    ]

    # Vote for most common answer
    from collections import Counter
    answer_counts = Counter(answers)
    final_answer = answer_counts.most_common(1)[0][0]

    return {
        "final_answer": final_answer,
        "confidence": answer_counts[final_answer] / n_samples,
        "reasoning_paths": responses,
        "answer_distribution": dict(answer_counts)
    }
```

## Least-to-Most Prompting

### Decomposition Phase

```markdown
## Problem Decomposition

You are an expert at breaking down complex problems into simpler sub-problems.

### Original Problem
{{complex_problem}}

### Decomposition
Break this problem into a sequence of simpler sub-problems that build upon each other:

1. First, solve:
2. Then, solve:
3. Finally, solve:

### Output Format
Sub-problems:
1. {{sub_problem_1}}
2. {{sub_problem_2}}
3. {{sub_problem_3}}
```

### Sequential Solving

```markdown
## Sequential Problem Solving

### Sub-problem 1
Question: {{sub_problem_1}}
Previous answers: None
Answer:

### Sub-problem 2
Question: {{sub_problem_2}}
Previous answers: {{answer_1}}
Answer:

### Sub-problem 3
Question: {{sub_problem_3}}
Previous answers: {{answer_1}}, {{answer_2}}
Answer:

### Final Answer
Based on the sub-problem answers, the solution to "{{original_problem}}" is:
```

## Structured Output Prompts

### JSON Output

```markdown
## Task
Extract structured information from the following text.

## Input Text
{{input_text}}

## Output Schema
Return a JSON object with the following structure:
{{
  "entities": [
    {{
      "name": "string - entity name",
      "type": "string - entity type (PERSON, ORG, LOCATION, etc.)",
      "mentions": ["string - list of mentions in text"]
    }}
  ],
  "relationships": [
    {{
      "subject": "string - entity name",
      "predicate": "string - relationship type",
      "object": "string - entity name"
    }}
  ],
  "summary": "string - brief summary of the text"
}}

## Output
```json
```

### XML Output

```markdown
## Task
Convert the following data to XML format.

## Input
{{input_data}}

## XML Schema
<root>
  <record id="string">
    <field1>value</field1>
    <field2>value</field2>
    <nested>
      <item>value</item>
    </nested>
  </record>
</root>

## Output
```

## Role-Based Prompting

### Persona Pattern

```markdown
## System Role
You are {{role_name}}, an expert in {{domain}} with the following characteristics:

- Background: {{background}}
- Expertise: {{expertise}}
- Communication style: {{style}}
- Biases to avoid: {{biases}}

## Task
{{task_description}}

## Context
{{context}}

## Constraints
- {{constraint_1}}
- {{constraint_2}}

## Response Format
{{format_instructions}}
```

### Multi-Persona Debate

```markdown
## Expert Panel Discussion

### Topic
{{debate_topic}}

### Panelists

#### Expert A ({{persona_a}})
Role: {{role_a}}
Perspective: {{perspective_a}}

#### Expert B ({{persona_b}})
Role: {{role_b}}
Perspective: {{perspective_b}}

#### Expert C ({{persona_c}})
Role: {{role_c}}
Perspective: {{perspective_c}}

### Discussion Format
1. Each expert presents their initial view (2-3 sentences)
2. Experts respond to each other's points
3. Final synthesis that acknowledges different perspectives

### Begin Discussion
Expert A:
```

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

## Integration with Super-Skill

### Phase Integration

```yaml
prompt_phase_mapping:
  phase_4_requirements:
    actions:
      - define_prompt_requirements
      - create_evaluation_criteria

  phase_8_development:
    actions:
      - design_prompt_templates
      - implement_few_shot_examples
      - test_prompt_effectiveness

  phase_10_optimization:
    actions:
      - optimize_prompts
      - a_b_test_variations
      - measure_performance
```

## Best Practices

### Prompt Design
- [ ] Clear task description
- [ ] Consistent format
- [ ] Relevant examples
- [ ] Explicit constraints

### Evaluation
- [ ] Test cases defined
- [ ] Success metrics clear
- [ ] Iterative refinement
- [ ] Version control

### Output Control
- [ ] Format specified
- [ ] Constraints defined
- [ ] Validation in place
- [ ] Error handling

## Deliverables

- Prompt templates
- Few-shot examples
- Evaluation framework
- Optimization pipeline

---

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
