---
name: verification-gate
description: Read-only challenge pass after implementation. Distinguishes verified from merely claimed done. Checks tests ran, changes match request, no regressions. Three-state output: verified/unverified/failed.
---

# Verification Gate

Inspired by [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills) verification-gate pattern.

## When to Use

- After Phase 8 (Development) completes
- After Phase 9 (QA) passes
- Before Phase 11 (Deployment)
- Before marking ANY task as complete
- When claiming "done" on a feature

## When NOT to Use

- During active development (use testing-automation instead)
- For planning or research phases

## Protocol

### Step 1: Gather Context (Read-Only)
```bash
git status
git diff --stat
git diff --name-only
git rev-parse HEAD
```

### Step 2: Run Challenge Checks
1. **Does the change match the request?** Compare diff against original requirement
2. **Did validation actually run?** Check for test output, not just "tests should pass"
3. **Are there obvious regressions?** Changed files that weren't part of the request
4. **Is anything overstated as "done"?** Claims without evidence

### Step 3: Produce Verdict

| State | Meaning | Action |
|-------|---------|--------|
| **VERIFIED** | All checks passed with evidence | Proceed to next phase |
| **UNVERIFIED** | Cannot confirm or deny | Run additional checks before proceeding |
| **FAILED** | Evidence of problems | Return to Phase 8 for fixes |

### Step 4: Output Report
```
## Verification Report

### Verified
- [item]: [evidence]

### Unverified
- [item]: [what's missing]

### Failed
- [item]: [what broke]

### Verdict: VERIFIED | UNVERIFIED | FAILED
### Next Step: [action]
```

## Rules

- **Read-only by default** - never modify code during verification
- **Findings before summary** - list evidence first, then conclude
- **Never imply validation ran if it did not** - honest assessment
- **Distinguish verified, unverified, and failed** - three states, not two
