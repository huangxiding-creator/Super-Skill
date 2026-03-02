---
name: systematic-debugging
description: Four-phase debugging methodology with root cause investigation, pattern analysis, hypothesis testing, and implementation. Integrates with Super-Skill Phase 8 (Development) and Phase 9 (QA) for production-grade bug resolution.
tags: [debugging, troubleshooting, root-cause, quality]
version: 1.0.0
source: https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md
integrated-with: super-skill v3.4+
---

# Systematic Debugging Skill

This skill provides a rigorous, four-phase debugging methodology that ensures bugs are fixed correctly the first time by identifying root causes before applying solutions.

## When to Use This Skill

Use this skill when:
- Encountering bugs or errors during development (Phase 8)
- Running QA and finding issues (Phase 9)
- User reports a bug or unexpected behavior
- Tests are failing unexpectedly
- System behavior is inconsistent or unpredictable
- Performance issues need investigation

## The Iron Law

> **NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST**

Never apply a fix without understanding WHY the bug occurs. Symptom-based fixes lead to:
- Bug recurrence in different forms
- Hidden side effects
- Technical debt accumulation
- Reduced system reliability

## Four-Phase Debugging Process

### Phase 1: Root Cause Investigation

**Goal**: Understand WHY the bug occurs, not just WHAT happens.

```
Step 1.1: Reproduce the Bug
- Document exact reproduction steps
- Identify required conditions
- Note environmental factors
- Create minimal reproduction case

Step 1.2: Gather Evidence
- Logs and error messages
- Stack traces
- State snapshots
- User actions leading to failure

Step 1.3: Isolate the Problem
- Binary search through code paths
- Eliminate irrelevant factors
- Identify the failing component
- Narrow to smallest possible scope

Step 1.4: Identify Root Cause
- Ask "Why?" at least 5 times
- Trace data flow
- Check assumptions
- Document the root cause clearly
```

**Root Cause Statement Template**:
```
The bug occurs because [component] assumes [assumption],
but [actual condition] is true when [trigger condition] happens.
This causes [symptom] to appear.
```

### Phase 2: Pattern Analysis

**Goal**: Understand the broader context and prevent similar bugs.

```
Step 2.1: Search for Similar Patterns
- Are there similar code patterns elsewhere?
- Could this bug occur in other places?
- Is this a systemic issue?

Step 2.2: Analyze Contributing Factors
- What allowed this bug to exist?
- Why wasn't it caught earlier?
- What tests would have prevented it?

Step 2.3: Document Patterns
- Code patterns to avoid
- Anti-patterns identified
- Best practices violated
```

**Pattern Analysis Template**:
```
## Pattern Analysis

### Similar Code Locations
- file1.ts:123 - Similar pattern, potentially affected
- file2.ts:456 - Same assumption, needs review

### Contributing Factors
1. Missing test coverage for edge case
2. Assumption not validated in code
3. Error handling incomplete

### Prevention Strategies
1. Add validation for assumption X
2. Create test case for scenario Y
3. Implement monitoring for condition Z
```

### Phase 3: Hypothesis and Testing

**Goal**: Validate the fix before implementing it.

```
Step 3.1: Formulate Hypothesis
- What change will fix the bug?
- Why will this change work?
- What side effects might occur?

Step 3.2: Design Test Cases
- Test that reproduces the bug (currently failing)
- Test that validates the fix (will pass after fix)
- Edge case tests
- Regression tests

Step 3.3: Validate Hypothesis
- Implement minimal fix
- Run test cases
- Verify fix works
- Check for side effects

Step 3.4: Refine if Needed
- If hypothesis wrong, return to Phase 1
- If side effects found, adjust approach
- Document learnings
```

**Hypothesis Template**:
```
## Hypothesis

### Proposed Fix
Change [component] to [behavior] when [condition].

### Expected Outcome
- Bug symptom will no longer occur
- System will handle edge case correctly
- No regression in existing functionality

### Validation Plan
1. Run existing test suite
2. Add new test case for bug scenario
3. Manual verification of fix
4. Edge case testing
```

### Phase 4: Implementation

**Goal**: Apply the fix safely and thoroughly.

```
Step 4.1: Implement the Fix
- Make minimal, focused changes
- Follow coding standards
- Add appropriate error handling
- Include inline comments if complex

Step 4.2: Add Tests
- Unit test for the fix
- Integration test if needed
- Regression test for the bug

Step 4.3: Update Documentation
- Update comments if behavior changed
- Document root cause in commit message
- Update relevant docs if API changed

Step 4.4: Verify and Deploy
- Run full test suite
- Verify in staging environment
- Deploy with monitoring
- Confirm fix in production
```

**Commit Message Template**:
```
fix: [brief description]

Root Cause: [why the bug occurred]

The bug occurred because [explanation]. This change fixes it by [solution].

- Adds test case for [scenario]
- Updates [component] to handle [edge case]

Fixes #[issue-number]
```

## Debugging Decision Matrix

```
IF bug is easily reproducible:
  → Focus on root cause isolation
  → Use debugging tools (breakpoints, logging)
  → Create minimal reproduction

IF bug is intermittent:
  → Focus on evidence gathering
  → Add comprehensive logging
  → Look for race conditions/timing issues

IF bug is in production:
  → Prioritize containment first
  → Gather diagnostic information
  → Apply fix carefully with rollback plan

IF bug is performance-related:
  → Profile before debugging
  → Identify bottlenecks
  → Measure before and after
```

## Integration with Super-Skill

### Phase 8: Autonomous Development

Systematic debugging integrates into development:

1. **When Errors Occur**
   - Apply Phase 1: Root Cause Investigation
   - Don't skip to quick fixes
   - Document findings

2. **Pattern Recognition**
   - Apply Phase 2: Pattern Analysis
   - Check for similar issues
   - Update coding guidelines

3. **Test-Driven Fixes**
   - Apply Phase 3: Hypothesis and Testing
   - Write failing test first
   - Verify fix with tests

### Phase 9: QA (Quality Assurance)

Systematic debugging enhances QA:

1. **Bug Triage**
   - Categorize by severity
   - Prioritize by impact
   - Assign investigation resources

2. **Root Cause Analysis**
   - Apply full 4-phase process
   - Document for future reference
   - Update test coverage

3. **Regression Prevention**
   - Add comprehensive tests
   - Update documentation
   - Share learnings with team

## Common Debugging Anti-Patterns

### 1. Shotgunning
Making random changes hoping something works.
**Instead**: Follow systematic process.

### 2. Symptom Treatment
Fixing the visible symptom without finding root cause.
**Instead**: Always ask "why" until root cause is found.

### 3. Cargo Cult Debugging
Copying fixes from similar-looking bugs without understanding.
**Instead**: Verify root cause matches before applying fix.

### 4. Assumption-Based Debugging
Assuming you know the cause without investigation.
**Instead**: Gather evidence, validate assumptions.

## Debugging Checklist

### Before Starting
- [ ] Bug is clearly defined and reproducible
- [ ] Environment and conditions documented
- [ ] Relevant logs and evidence collected

### During Investigation
- [ ] Root cause identified and documented
- [ ] Similar patterns searched and analyzed
- [ ] Hypothesis formulated and tested

### Before Fixing
- [ ] Test case created that reproduces bug
- [ ] Hypothesis validated with minimal fix
- [ ] Side effects considered and tested

### After Fixing
- [ ] Full test suite passes
- [ ] New tests added for bug scenario
- [ ] Documentation updated
- [ ] Commit message includes root cause

## Deliverables

- Root Cause Analysis Document
- Test case(s) for the bug
- Fix implementation with tests
- Updated documentation if needed

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-01 | Initial integration with Super-Skill V3.4 |

---

## License

MIT License - Based on [Obra Superpowers](https://github.com/obra/superpowers)
