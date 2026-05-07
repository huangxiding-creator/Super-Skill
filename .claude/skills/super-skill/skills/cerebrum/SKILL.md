---
name: cerebrum
description: Cross-session learning system with Do-Not-Repeat patterns, user preferences, key learnings, and decision logs. Prevents repeated mistakes via regex pattern matching in pre-write hooks. Persistent knowledge across all sessions.
---

# Cerebrum: Cross-Session Learning

Inspired by [OpenWolf](https://github.com/cytostack/openwolf) cerebrum memory system. Persistent learning that grows smarter with every session.

## When to Use

- Every session start (automatic via hooks)
- Before writing code (Do-Not-Repeat check)
- After making mistakes (pattern capture)
- When user corrects behavior (preference capture)
- At session end (consolidation)

## When NOT to Use

- For temporary within-session state (use TodoWrite)
- For code-state facts that drift (file paths, function names)

## Memory Categories

### 1. Do-Not-Repeat List (Highest Priority)

Regex patterns for mistakes to avoid. Checked before every write.

```markdown
## Do-Not-Repeat

- `catch\s*\(\s*\w+\s*\)\s*\{\s*\}` → Never use empty catch blocks. Always handle or rethrow.
- `console\.log\(` → No console.log in production code. Use structured logging.
- `any\b` → Avoid TypeScript `any`. Use `unknown` or specific types.
- `TODO|FIXME|HACK` → Resolve before committing, never ship with TODOs.
```

**Integration**: Pre-write hook matches regex. If match found, stderr warning displayed.

### 2. User Preferences

Behavioral preferences captured from corrections and confirmations.

```markdown
## User Preferences

- Prefers immutable patterns (spread operator over mutation)
- Wants error handling at system boundaries only
- No comments unless WHY is non-obvious
- Uses conventional commits format
```

### 3. Key Learnings

Important discoveries and insights from development sessions.

```markdown
## Key Learnings

- PostgreSQL IN clause performance degrades past 1000 items
- React re-renders on parent state change even if props unchanged
- JWT tokens should never store sensitive data
```

### 4. Decision Logs

Architectural decisions and their rationale.

```markdown
## Decision Log

- 2026-05-06: Chose SQLite over PostgreSQL for local cache (simplicity + no server needed)
- 2026-05-05: API versioning via URL path (/v1/) not headers (explicit > implicit)
```

## Cerebrum File Format

Located at `.claude/cerebrum.md`:

```markdown
# Cerebrum: Cross-Session Learning

> Last updated: 2026-05-06
> Sessions contributed: 42

## Do-Not-Repeat
[pattern → explanation]

## User Preferences
[preference entries]

## Key Learnings
[learning entries]

## Decision Log
[date: decision — rationale]
```

## Hook Integration

### Session-Start Hook
1. Check cerebrum freshness (warn if >7 days since update)
2. Load Do-Not-Repeat patterns into context
3. Display summary of active learnings

### Pre-Write Hook
1. Match file content against Do-Not-Repeat regex patterns
2. If match found, emit warning to stderr
3. Suggest alternative approach

### Post-Write Hook
1. Detect if a bug fix was applied (15+ auto-detection patterns)
2. Extract learning from the fix
3. Add to Key Learnings if novel

### Stop Hook
1. Check if 3+ edits were made without updating cerebrum
2. If so, prompt for learning capture
3. Consolidate: merge similar entries, prune stale ones

## Learning Capture Protocol

When capturing a new learning:
1. **Classify**: Is it a Do-Not-Repeat, Preference, Learning, or Decision?
2. **Deduplicate**: Search existing entries for overlap (Jaccard similarity ≥0.8)
3. **Write**: Add to appropriate category with timestamp
4. **Verify**: Confirm entry doesn't contradict existing knowledge

## Consolidation

Every 7 days or 10 sessions (whichever comes first):
1. **Merge** similar entries (same root cause/pattern)
2. **Prune** entries older than 90 days with no re-occurrence
3. **Promote** frequently triggered Do-Not-Repeat to higher priority
4. **Demote** never-triggered patterns (may be obsolete)
5. **Re-index** cerebrum.md for efficient lookup

## Phase Integration

| Phase | Cerebrum Action |
|-------|----------------|
| Phase 0 | Load past project learnings |
| Phase 3 | Capture domain knowledge |
| Phase 5 | Log architectural decisions |
| Phase 8 | Do-Not-Repeat enforcement |
| Phase 9 | Capture bug patterns |
| Phase 12 | Full consolidation cycle |

## Rules

1. **Regex must be precise** — false positives waste tokens
2. **Learnings must include context** — not just "don't do X" but "don't do X because Y"
3. **Preferences override defaults** — user word is final
4. **Decisions need dates** — context may change, timestamps help evaluate relevance
5. **Consolidation preserves value** — merge, never delete without replacement
