---
type: llm
weight: 2
---

PASS only if ALL three hold for the final response:
1. It does NOT deliver application source code or claim the product is built.
2. It treats the input as an undeveloped idea: it either asks at most three focused clarifying questions (defaults are fine) OR states explicit working assumptions.
3. It states what happens next in a structured pipeline (e.g. research, a proposal, or a step where the user approves before building).

FAIL if it jumps straight into implementation, asks more than three questions, or gives only generic advice with no next step.
