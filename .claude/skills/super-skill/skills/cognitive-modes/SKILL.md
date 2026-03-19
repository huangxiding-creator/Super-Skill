---
name: cognitive-modes
description: Six cognitive modes for AI development from Y Combinator CEO Garry Tan. TRIGGER when users need different perspectives: product vision, architecture review, paranoid code review, release automation, browser testing, or retrospectives. Modes: CEO (10-star vision), Eng Manager (architecture), Paranoid Reviewer (bugs), Release Engineer (ship), QA Engineer (browser automation), Engineering Manager (retrospectives).
---

# Cognitive Modes for AI Development

## Overview

Six distinct cognitive modes adapted from gstack (Garry Tan, Y Combinator CEO). Each mode provides a specialized perspective for different development phases. **Philosophy: Wear the right hat for the task.**

## Mode Overview

| Mode | Role | Trigger | Focus |
|------|------|---------|-------|
| **CEO** | Founder/CEO | `/plan-ceo-review` | 10-star product vision |
| **Eng Manager** | Tech Lead | `/plan-eng-review` | Architecture, edge cases |
| **Paranoid Reviewer** | Staff Engineer | `/review` | Production bugs |
| **Release Engineer** | Release Eng | `/ship` | Deploy automation |
| **QA Engineer** | QA Engineer | `/browse` | Browser automation |
| **Eng Manager (Retro)** | EM | `/retro` | Retrospectives |

---

## Mode 1: CEO / Founder

**Trigger**: `/plan-ceo-review`

### Mindset
"Rethink the problem. Find the 10-star product."

### Questions to Ask
- What problem are we REALLY solving?
- Is this the best possible solution?
- Would a user pay for this? Why?
- What's the simplest thing that could work?
- Are we building the right thing?

### Output
- Product vision statement
- User value proposition
- Success metrics
- MVP definition
- Kill criteria (when to pivot)

### Example Prompt
```
Act as a CEO reviewing this feature:
- Challenge the core assumptions
- Identify the 10-star version
- Define success metrics
- What would you cut to ship faster?
```

---

## Mode 2: Eng Manager / Tech Lead

**Trigger**: `/plan-eng-review`

### Mindset
"Architecture, data flow, diagrams, state machines, edge cases."

### Questions to Ask
- What are the components?
- How do they interact?
- What are the data flows?
- What states can the system be in?
- What edge cases exist?

### Output
- System architecture diagram
- Component interaction map
- State machine definitions
- Edge case inventory
- Integration points

### Artifacts
```
docs/
├── ARCHITECTURE.md      # High-level design
├── DATA_FLOW.md         # Data flow diagrams
├── STATE_MACHINES.md    # State transitions
└── EDGE_CASES.md        # Edge case handling
```

### Example Prompt
```
Act as an Eng Manager reviewing this design:
- Draw the system architecture
- Map all data flows
- Define state machines
- List ALL edge cases
- Identify integration risks
```

---

## Mode 3: Paranoid Reviewer

**Trigger**: `/review`

### Mindset
"Find bugs that pass CI but blow up in production."

### Focus Areas
1. **N+1 Queries**: Database inefficiencies
2. **Race Conditions**: Concurrency bugs
3. **Trust Boundaries**: Security vulnerabilities
4. **Memory Leaks**: Resource exhaustion
5. **Error Handling**: Silent failures
6. **Edge Cases**: Unhappy paths

### Review Checklist
- [ ] All database queries analyzed for N+1
- [ ] Concurrency scenarios documented
- [ ] All user inputs validated
- [ ] Error messages don't leak secrets
- [ ] Rate limiting implemented
- [ ] Graceful degradation exists
- [ ] Logging captures diagnostics
- [ ] Metrics track key operations

### Example Prompt
```
Act as a Paranoid Staff Engineer:
- Find the bug that passes tests but fails in prod
- Check for N+1 queries
- Identify race conditions
- Validate trust boundaries
- Look for silent failures
```

---

## Mode 4: Release Engineer

**Trigger**: `/ship`

### Mindset
"Sync main, run tests, push, open PR."

### Workflow
```
1. Sync: git fetch origin && git rebase origin/main
2. Test: npm test / cargo test / pytest
3. Lint: npm run lint / cargo clippy
4. Build: npm run build / cargo build --release
5. Commit: Conventional commit message
6. Push: git push -u origin <branch>
7. PR: Create with description and test plan
```

### PR Checklist
- [ ] All tests pass
- [ ] No lint errors
- [ ] Build succeeds
- [ ] Documentation updated
- [ ] Breaking changes noted
- [ ] Migration guide (if needed)

### Example Prompt
```
Act as a Release Engineer:
- Sync with main
- Run full test suite
- Create conventional commit
- Push and open PR
- Include test plan
```

---

## Mode 5: QA Engineer

**Trigger**: `/browse`

### Mindset
"Browser automation with Playwright."

### Capabilities
- Automated browser testing
- Screenshot capture
- Form interaction
- Navigation testing
- Visual regression
- Accessibility testing

### Playwright Patterns
```typescript
// Screenshot on failure
test('user flow', async ({ page }) => {
  try {
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@example.com')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/dashboard')
  } catch (e) {
    await page.screenshot({ path: 'failure.png' })
    throw e
  }
})
```

### Test Categories
1. **Smoke Tests**: Critical path works
2. **Happy Path**: Expected user flows
3. **Edge Cases**: Boundary conditions
4. **Error States**: Error handling
5. **Visual Regression**: UI consistency

### Example Prompt
```
Act as a QA Engineer:
- Test the user login flow
- Capture screenshots at each step
- Verify error handling
- Check accessibility
- Report all findings
```

---

## Mode 6: Engineering Manager (Retro)

**Trigger**: `/retro`

### Mindset
"Analyze commit history, work patterns."

### Analysis Areas
1. **Velocity**: Commits per day/week
2. **Patterns**: What kinds of changes
3. **Hotspots**: Files changed most
4. **Collaboration**: Who works on what
5. **Technical Debt**: Recurring issues

### Retro Questions
- What went well?
- What could be improved?
- What blocked us?
- What should we start doing?
- What should we stop doing?

### Output
```
RETROSPECTIVE.md
├── What Went Well
├── What to Improve
├── Blockers Encountered
├── Action Items
└── Metrics Summary
```

### Example Prompt
```
Act as an Engineering Manager running a retro:
- Analyze commit history for patterns
- Identify recurring issues
- Find technical debt hotspots
- Suggest process improvements
- Create action items
```

---

## Mode Switching Guide

| Phase | Recommended Mode |
|-------|------------------|
| Phase 0 | CEO (10-star vision) |
| Phase 5 | Eng Manager (architecture) |
| Phase 8 | Paranoid Reviewer (bugs) |
| Phase 9 | QA Engineer (testing) |
| Phase 11 | Release Engineer (deploy) |
| Phase 12 | Eng Manager Retro |

## Mode Combination Patterns

### Full Feature Review
```
1. CEO: Validate product direction
2. Eng Manager: Design architecture
3. Paranoid Reviewer: Find bugs
4. QA Engineer: Test thoroughly
5. Release Engineer: Ship it
6. Eng Manager Retro: Learn and improve
```

### Debugging Session
```
1. Paranoid Reviewer: Find the bug
2. Eng Manager: Assess impact
3. CEO: Validate fix direction
4. Release Engineer: Deploy fix
```

## Integration with Super-Skill

| Mode | Super-Skill Phase | Skill Synergy |
|------|-------------------|---------------|
| CEO | Phase 0, 4 | ai-native-vision, brainstorming |
| Eng Manager | Phase 5, 5b | api-patterns, data-patterns |
| Paranoid Reviewer | Phase 8, 9 | systematic-debugging, security-scanning |
| Release Engineer | Phase 7, 11 | auto-git-create, cicd-automation |
| QA Engineer | Phase 9 | testing-automation, accessibility-a11y |
| Eng Manager Retro | Phase 12 | darwin-evolution, continuous-learning-v2 |

## Quick Reference

```
/plan-ceo-review   → Vision, 10-star product
/plan-eng-review   → Architecture, edge cases
/review            → Find production bugs
/ship              → Deploy automation
/browse            → Browser testing
/retro             → Retrospective analysis
```

## Version

**V1.0.0** - 2026-03-14
- Six cognitive modes from gstack
- Mode-specific prompts and checklists
- Phase integration mapping
- Mode combination patterns
