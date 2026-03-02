---
name: brainstorming
description: Systematic exploration of ideas and approaches before implementation. Integrates with Super-Skill Phase 0 (Visionary Elevation) and Phase 4 (Requirements Engineering) for comprehensive solution discovery.
tags: [discovery, planning, ideation, architecture]
version: 1.0.0
source: https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md
integrated-with: super-skill v3.4+
---

# Brainstorming Skill

This skill helps you explore ideas, approaches, and solutions systematically before diving into implementation. It ensures comprehensive understanding and optimal design decisions.

## When to Use This Skill

Use this skill when:
- Starting a new feature or project (Phase 0: Visionary Elevation)
- Requirements are unclear or incomplete
- Multiple solution approaches are possible
- Complex architectural decisions need to be made
- User asks to "brainstorm" or "explore options"
- Before committing to an implementation path

## Core Principles

### 1. One Question at a Time
Never overwhelm with multiple questions. Ask sequentially, process the answer, then ask the next.

### 2. YAGNI Ruthlessly
Cut scope aggressively. If a feature isn't essential for the core use case, defer or remove it.

### 3. Explore Before Committing
Always understand the full context before proposing solutions.

## 6-Step Brainstorming Process

### Step 1: Explore Context

Before proposing anything, understand the full picture:

```
Questions to answer:
- What is the core problem being solved?
- Who are the users/stakeholders?
- What are the constraints (time, budget, technical)?
- What exists already that we can leverage?
- What are the success criteria?
```

### Step 2: Ask Questions (One at a Time)

Systematically clarify requirements:

```
Example sequence:
1. "What is the primary user persona for this feature?"
   → Process answer, note key insights

2. "What is the most critical workflow this enables?"
   → Process answer, note key insights

3. "Are there any hard technical constraints I should know about?"
   → Process answer, note key insights
```

**Rule**: Wait for the answer before asking the next question.

### Step 3: Propose 2-3 Approaches

Present distinct approaches with trade-offs:

```markdown
## Approach 1: [Name]
- **Description**: Brief overview
- **Pros**: Key advantages
- **Cons**: Key disadvantages
- **Complexity**: Low/Medium/High
- **Time Estimate**: Rough estimate

## Approach 2: [Name]
...

## Approach 3: [Name] (if applicable)
...
```

### Step 4: Present Recommended Design

After user selects or provides feedback:

```markdown
## Recommended Design

### Architecture Overview
[High-level architecture diagram or description]

### Key Components
- Component A: Purpose and responsibility
- Component B: Purpose and responsibility
- ...

### Data Flow
[How data moves through the system]

### API Contracts
[Key interfaces between components]

### Risk Areas
- Risk 1: Mitigation strategy
- Risk 2: Mitigation strategy
```

### Step 5: Document Decisions

Create a decision record:

```markdown
## Design Decision Record

### Context
[Why this decision was needed]

### Decision
[What was decided]

### Rationale
[Why this approach was chosen]

### Alternatives Considered
[Other options and why they weren't chosen]

### Consequences
[Implications of this decision]
```

### Step 6: Transition to Implementation

Hand off to implementation phase:

```
Checklist before implementation:
- [ ] All requirements clarified
- [ ] Design documented and approved
- [ ] Technical approach confirmed
- [ ] Risks identified and mitigated
- [ ] Ready for WBS creation (Phase 6)
```

## Integration with Super-Skill

### Phase 0: Visionary Elevation

Brainstorming enhances Phase 0 by:

1. **Exploring AI-Native Possibilities**
   - What if AI handled 90% of this workflow?
   - What would a zero-UI version look like?
   - How might this be solved in 2030?

2. **Challenging Assumptions**
   - Is this constraint real or assumed?
   - What's the boldest approach possible?
   - What would competitors never expect?

3. **Generating Breakthrough Ideas**
   - Anti-consensus design exploration
   - Extreme constraint breakthrough
   - AI-first architecture patterns

### Phase 4: Requirements Engineering

Brainstorming supports requirements by:

1. **Clarifying Ambiguities**
   - One question at a time exploration
   - Deep dive into edge cases
   - User journey mapping

2. **Validating Requirements**
   - Are these requirements complete?
   - What's missing?
   - What's over-specified?

3. **Prioritization**
   - MoSCoW analysis (Must/Should/Could/Won't)
   - Impact vs. Effort matrix
   - YAGNI filtering

## Decision Matrix for Brainstorming

```
IF requirements are clear and simple:
  → Skip extended brainstorming
  → Proceed directly to implementation planning

IF requirements are complex or unclear:
  → Run full 6-step brainstorming process
  → Document all decisions
  → Get user confirmation before proceeding

IF multiple stakeholders involved:
  → Ask clarifying questions first
  → Present options to all stakeholders
  → Facilitate decision-making
```

## Example Brainstorming Session

```
USER: I need a user authentication system

AGENT: I'd like to understand the context better.
       What type of application is this for?

USER: A B2B SaaS dashboard

AGENT: Got it, B2B SaaS. What level of security
       is required? (e.g., basic auth, SSO, MFA?)

USER: We need SSO with Microsoft Entra and MFA

AGENT: Understood. Are there compliance requirements
       like SOC2 or HIPAA I should know about?

USER: SOC2 compliance is needed

AGENT: [After gathering context, presents 2-3 approaches
       with trade-offs, recommends a design, documents
       decisions, and transitions to implementation]
```

## Gate Checks for Brainstorming

- [ ] Context fully explored
- [ ] All clarifying questions asked (one at a time)
- [ ] 2-3 approaches presented with trade-offs
- [ ] Design recommendation provided
- [ ] Decisions documented
- [ ] Ready for implementation phase

## Deliverables

- Design Decision Record (DDR)
- Recommended architecture overview
- Risk assessment and mitigation strategies
- Clear path to Phase 6 (WBS)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-01 | Initial integration with Super-Skill V3.4 |

---

## License

MIT License - Based on [Obra Superpowers](https://github.com/obra/superpowers)
