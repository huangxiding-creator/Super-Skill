---
name: buglog
description: Searchable bug fix database with auto-detection and Jaccard similarity matching. Auto-detects 15+ bug patterns from code edits, prevents duplicate entries, surfaces related past fixes before writing. Growing knowledge base of past mistakes.
---

# Buglog: Bug Memory System

Inspired by [OpenWolf](https://github.com/cytostack/openwolf) bug tracking system. Auto-captures bug fixes and builds a searchable knowledge base.

## When to Use

- Automatically via hooks (bug detection is passive)
- Before writing fixes (check for related past bugs)
- During QA (reference known bug patterns)
- At session end (capture uncategorized fixes)

## When NOT to Use

- For feature requests (use MEMORY.md)
- For architectural decisions (use cerebrum Decision Log)

## Auto-Detected Bug Patterns

The post-write hook automatically detects these 15 fix patterns:

| # | Pattern | Detection Regex |
|---|---------|-----------------|
| 1 | Error handling added | `try\s*\{` added or `catch\s*\(` added |
| 2 | Null safety fix | `null\|undefined\|Nil` check added |
| 3 | Guard clause | `if\s*\(!\|return\|throw` at function start |
| 4 | Wrong value fix | String/number literal changed in existing line |
| 5 | Logic fix | Operator change (`&&`\|`||`\|`==`\|`!=`) |
| 6 | Operator fix | `=` → `==`, `==` → `===`, etc. |
| 7 | Missing import | New import/require added |
| 8 | Return value fix | Return statement changed |
| 9 | Async/await fix | `await` added/removed, `async` added |
| 10 | Type fix | Type annotation changed |
| 11 | CSS fix | Style/class change in CSS/SCSS |
| 12 | Refactor | Function extracted, renamed, or restructured |
| 13 | Boundary fix | Loop boundary, array index, off-by-one |
| 14 | Race condition | Lock added, timeout changed, concurrent access fix |
| 15 | Resource leak | `close()`, `finally`, cleanup added |

## Bug Entry Format

```json
{
  "id": "bug_001",
  "timestamp": "2026-05-06T12:00:00Z",
  "pattern": "null_safety",
  "file": "src/routes/users.ts",
  "description": "User profile access without null check caused crash",
  "fix": "Added null guard before accessing user.profile.name",
  "tags": ["null", "crash", "user", "profile"],
  "context": "Accessing nested object property without null check",
  "similarity_hash": "null_safety:user:profile:access:nested"
}
```

## Storage Format

`.claude/buglog.json`:
```json
{
  "version": 1,
  "entries": [
    { /* bug entry */ }
  ],
  "stats": {
    "total_entries": 42,
    "by_pattern": {
      "null_safety": 12,
      "error_handling": 8,
      "logic_fix": 6
    },
    "last_updated": "2026-05-06T12:00:00Z"
  }
}
```

## Similarity Matching (Jaccard)

Used to prevent duplicate entries and surface related bugs.

### Algorithm

```
J(A, B) = |A ∩ B| / |A ∪ B|

where A, B are sets of tags/words
threshold = 0.8 for duplicate detection
threshold = 0.5 for related bug surfacing
```

### Matching Pipeline

1. **Tag overlap**: Check shared tags between new and existing entries
2. **Word overlap**: Tokenize description, check word overlap
3. **Pattern match**: Same pattern type boosts similarity score
4. **File match**: Same file/directory boosts similarity score

### Pre-Write Matching

Before writing a fix, the pre-write hook:
1. Analyzes the intended fix
2. Searches buglog for similar past fixes
3. If similarity ≥0.5, surfaces the past fix as context
4. If similarity ≥0.8, warns about potential duplicate

### Post-Write Capture

After writing a fix, the post-write hook:
1. Detects bug pattern from the 15 auto-detection patterns
2. Extracts tags from file path and fix content
3. Checks for duplicates (Jaccard ≥0.8)
4. If novel, adds to buglog with auto-generated entry

## Missing Buglog Detection

If 3+ code edits are made during a session without updating buglog:
- Session-end hook warns: "X edits made without buglog capture"
- Suggests reviewing edits for bug fix patterns

## Hook Integration

### Pre-Write Hook
1. Analyze intended code change
2. Search buglog for related past fixes (threshold ≥0.5)
3. Surface relevant entries as context

### Post-Write Hook
1. Auto-detect bug pattern from change
2. Extract tags and context
3. Check for duplicates (Jaccard ≥0.8)
4. Add novel entries to buglog

### Stop Hook
1. Check edit count vs buglog updates
2. Warn if edits >> buglog entries (missing captures)
3. Generate session bug summary

## Phase Integration

| Phase | Buglog Action |
|-------|--------------|
| Phase 8 | Pre-write check for related bugs |
| Phase 9 | Reference during QA, capture new bugs |
| Phase 10 | Cross-reference during optimization |
| Phase 12 | Consolidation: merge similar, prune old |

## Rules

1. **Auto-capture is passive** — no manual logging required for detected patterns
2. **Tags must be lowercase** — consistent matching
3. **Similarity ≥0.8 is duplicate** — merge, don't duplicate
4. **Similarity 0.5-0.8 is related** — surface as context, don't merge
5. **Prune entries older than 180 days** — unless referenced in recent sessions
6. **Never auto-delete** — always suggest, let human decide
