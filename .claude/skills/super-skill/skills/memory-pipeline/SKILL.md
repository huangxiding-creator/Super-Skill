---
name: memory-pipeline
description: Dual-phase memory system: extract durable facts from conversations (4 types), then consolidate nightly (dedup, prune, reindex). Keeps MEMORY.md as a concise index, never a content dump.
---

# Memory Pipeline

Combines dream-memory and memory-extractor patterns from [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills).

## Two Phases

### Phase A: Extract (during/after conversation)
Extract durable memories into 4 typed categories:

| Type | What to Save | Examples |
|------|-------------|----------|
| **user** | Role, preferences, style, knowledge | "prefers immutability", "senior Go engineer" |
| **feedback** | Corrections, validated preferences | "don't mock database in tests", "prefer small PRs" |
| **project** | Deadlines, constraints, motivations | "freeze after March 5", "legal flagged auth" |
| **reference** | External system pointers | "pipeline bugs in Linear INGEST project" |

**Rules:**
- Save only DURABLE information (survives across sessions)
- Never store code-state facts that can drift (file paths, function names, line numbers)
- Update existing topic file before creating a new one
- Organize by topic, not chronology

### Phase B: Consolidate (nightly or on-demand)
Periodic cleanup of the memory store:

1. **Orient** - Inspect MEMORY.md index and topic files
2. **Gather** - Review recent logs and transcripts
3. **Consolidate** - Merge overlapping topic files, update with new durable facts
4. **Prune** - Remove stale pointers, convert relative dates to absolute
5. **Reindex** - Rewrite MEMORY.md as concise one-line-per-entry index

**Rules:**
- `MEMORY.md` is an INDEX, never a content dump (cap: 200 lines / 25KB)
- Prefer merging into existing topic files over creating new ones
- Convert all relative dates to absolute dates
- Never store facts that should be re-read from source code

## Integration with Hooks

- **PostToolUse (Write/Edit)**: Extract memories when saving files
- **Stop**: Run extraction + consolidation at session end
- **Notification**: Load memories at session start

## Output Contract

```
## Memory Pipeline Report

### Extracted (Phase A)
- [type] topic-file.md: what was saved
- [skipped] reason: why it was not durable

### Consolidated (Phase B)
- Merged: X files → Y files
- Pruned: Z stale entries
- Index: N lines (was M lines)
- Cap status: under/over limit
```
