# Best Practices 2026 Reference

Comprehensive collection of AI-native development best practices from industry leaders.

## Sources

| Source | Author | Focus |
|--------|--------|-------|
| [LLM Coding Workflow 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e) | Addy Osmani | AI-assisted engineering |
| [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Anthropic | Skill creation |
| [AI Agent Frameworks 2026](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) | OpenAgents | Framework comparison |

---

## 1. Planning First (Specs Before Code)

> "Don't just throw wishes at the LLM — begin by defining the problem and planning a solution."

### The Waterfall-in-15-Minutes Pattern

1. **Brainstorm specification** with AI iteratively
2. **Ask questions** until requirements and edge cases are fleshed out
3. **Compile into spec.md** - requirements, architecture, data models, testing strategy
4. **Generate project plan** with bite-sized tasks
5. **Iterate on plan** - critique and refine

### Spec.md Template

```markdown
# Project Specification

## Requirements
- [ ] Functional requirement 1
- [ ] Functional requirement 2
- [ ] Non-functional requirements

## Architecture Decisions
- Decision 1: Rationale
- Decision 2: Rationale

## Data Models
- Entity 1: Fields, relationships
- Entity 2: Fields, relationships

## Testing Strategy
- Unit tests: Coverage target
- Integration tests: Key flows
- E2E tests: Critical paths
```

---

## 2. Iterative Chunks Pattern

> "Scope management is everything — feed the LLM manageable tasks, not the whole codebase at once."

### Chunk Size Guidelines

| Task Type | Optimal Size | Warning Signs |
|-----------|--------------|---------------|
| Feature | 1 function/module | "Implement the entire app" |
| Bug fix | 1 issue | "Fix all the bugs" |
| Refactor | 1 file/pattern | "Refactor everything" |

### Anti-Pattern: The Jumbled Mess

> "Like 10 devs worked on it without talking to each other."

**Solution**: Split into smaller pieces, implement one at a time.

---

## 3. Context Packing Pattern

> "LLMs are only as good as the context you provide — show them the relevant code, docs, and constraints."

### Context Packing Checklist

- [ ] High-level goals and invariants
- [ ] Examples of good solutions
- [ ] Warnings about approaches to avoid
- [ ] Performance constraints
- [ ] Known edge cases

### Context Tools

| Tool | Purpose |
|------|---------|
| **gitingest** | Dump codebase to text |
| **repo2txt** | Generate codebase bundle |
| **Context7 MCP** | Intelligent context selection |
| **Claude Projects** | Import GitHub repo |

### Guidance in Prompts

```
Here is the current implementation of X.
We need to extend it to do Y.
Be careful not to break Z.
```

---

## 4. Model Selection Strategy

> "Not all coding LLMs are equal — pick your tool with intention."

### Model Characteristics

| Model | Best For |
|-------|----------|
| **Claude Opus** | Complex reasoning, architecture |
| **Claude Sonnet** | Balanced coding, everyday tasks |
| **Claude Haiku** | Fast iterations, lightweight tasks |
| **Gemini Pro** | Natural interactions, first-try accuracy |

### Model Musical Chairs

If one model gets stuck:
1. Copy prompt to another service
2. Compare approaches
3. Use insights from both

---

## 5. Human-in-the-Loop Pattern

> "AI will happily produce plausible-looking code, but you are responsible for quality."

### Review Protocol

```
1. Read through generated code
2. Run it / test it
3. Ask AI to explain complex parts
4. Have another AI review it
5. Only merge when understood
```

### Testing Integration

- **TDD with AI**: Generate tests first, then implement
- **Post-generation**: Run test suite, debug failures
- **Feedback loop**: Feed failures back to AI

### Chrome DevTools MCP Pattern

For UI debugging:
1. Grant AI browser access
2. Inspect DOM, get performance traces
3. Diagnose bugs with runtime data

---

## 6. Version Control as Safety Net

> "Frequent commits are your save points — they let you undo AI missteps."

### Commit Strategy

| Trigger | Action |
|---------|--------|
| Task complete | Commit with clear message |
| Tests pass | Commit checkpoint |
| Before risky change | Commit current state |

### Branch Patterns

| Pattern | Use Case |
|---------|----------|
| **Feature branches** | New features |
| **Git worktrees** | Parallel AI sessions |
| **Cherry-pick** | Selective merge |

### Never Commit Code You Can't Explain

If AI generates something convoluted:
1. Ask AI to add comments
2. Rewrite in simpler terms
3. Don't commit until understood

---

## 7. Customization with Rules and Examples

> "Steer your AI assistant by providing style guides, examples, and rules files."

### CLAUDE.md Template

```markdown
# Project Rules for Claude

## Style
- Use 4 spaces indent
- Prefer functional style over OOP
- Avoid arrow functions in React

## Linting
- All code must pass ESLint
- Use Prettier formatting

## Patterns
- Use repository pattern for data access
- Error boundaries in React components
- Prefer composition over inheritance

## Anti-Patterns
- Don't use useEffect for data fetching (use React Query)
- Don't mutate state directly
- Don't use any type
```

### In-Line Examples

```
Here's how we implemented X:
[code example]

Use a similar approach for Y.
```

---

## 8. Automation as Force Multiplier

> "Use your CI/CD, linters, and code review bots — AI will work best in an environment that catches mistakes automatically."

### CI/CD Integration

```
AI writes code → CI runs tests → Feed failures to AI → AI fixes → Repeat
```

### Quality Gates

| Gate | Tool | Integration |
|------|------|-------------|
| **Linting** | ESLint, Prettier | Include errors in prompt |
| **Type checking** | TypeScript | Feed type errors to AI |
| **Tests** | Jest, Vitest | Auto-run after changes |
| **Security** | Snyk, CodeQL | Block vulnerable code |

### AI-on-AI Review

1. Claude writes code
2. Gemini reviews for errors
3. Incorporate feedback
4. Higher quality output

---

## 9. Continuous Learning Pattern

> "Treat every AI coding session as a learning opportunity."

### Amplification Effect

| Your Skills | AI Result |
|-------------|-----------|
| Strong fundamentals | 10x productivity |
| Weak foundation | Amplified confusion |

### Learning Techniques

- Ask AI to explain its code
- Debug AI mistakes to deepen understanding
- Use AI as research assistant
- Periodically code without AI

---

## 10. Skill Authoring Best Practices (Anthropic)

### Concise is Key

> "The context window is a public good."

- Assume Claude is already smart
- Challenge each piece of information
- Prefer examples over explanations

### Degrees of Freedom

| Freedom Level | When to Use | Example |
|---------------|-------------|---------|
| **High** | Multiple valid approaches | Code reviews |
| **Medium** | Preferred pattern exists | API design |
| **Low** | Fragile, exact sequence | Database migrations |

### Progressive Disclosure

```
SKILL.md (overview, <500 lines)
├── references/
│   ├── domain1.md (loaded when needed)
│   └── domain2.md (loaded when needed)
└── scripts/
    └── utility.py (executed, not read)
```

### Validation Loops

```
Run validator → Fix errors → Repeat
```

### Evaluation-Driven Development

1. Identify gaps
2. Create evaluations
3. Establish baseline
4. Write minimal instructions
5. Iterate

---

## Quick Reference Cards

### Pre-Coding Checklist

- [ ] Spec written and reviewed
- [ ] Plan broken into chunks
- [ ] Context prepared (code, docs, constraints)
- [ ] Right model selected
- [ ] CLAUDE.md/GEMINI.md updated

### During Coding Checklist

- [ ] Working in small iterations
- [ ] Running tests frequently
- [ ] Committing after each success
- [ ] Reviewing all generated code
- [ ] Asking for explanations when unclear

### Post-Coding Checklist

- [ ] All tests pass
- [ ] Code reviewed and understood
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Ready to merge

---

## Version

**V1.0.0** - 2026-03-14
- Based on Addy Osmani's LLM Coding Workflow 2026
- Anthropic's Skill Authoring Best Practices
- OpenAgents Framework Comparison 2026
