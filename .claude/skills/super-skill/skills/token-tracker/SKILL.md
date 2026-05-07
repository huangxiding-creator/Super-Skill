---
name: token-tracker
description: Session token tracking with waste detection. Estimates token usage per read/write, detects 5 waste patterns (repeated reads, anatomy-sufficient reads, memory bloat, stale cerebrum, anatomy miss rate), maintains session ledger for optimization feedback.
---

# Token Tracker

Inspired by [OpenWolf](https://github.com/cytostack/openwolf) token estimation and waste detection system. Provides concrete metrics for context optimization.

## When to Use

- Automatically via hooks (no manual trigger needed)
- During long sessions to monitor token efficiency
- After session for waste pattern analysis
- When optimizing context engineering strategy

## When NOT to Use

- For precise token counting (this is estimation only)
- As a replacement for Claude's native context management

## Token Estimation

### Formula

```
tokens = ceil(text.length / ratio)

where:
  ratio = 3.5  for code files (.ts, .py, .go, .rs, .java)
  ratio = 4.0  for prose files (.md, .txt, .rst)
  ratio = 3.75 for mixed content (.json, .yaml, .html)
```

### Estimation Accuracy

| Content Type | Ratio | Accuracy |
|-------------|-------|----------|
| Pure code | 3.5 | ±15% |
| Markdown | 4.0 | ±10% |
| JSON/YAML | 3.75 | ±12% |
| Mixed | 3.5-4.0 | ±20% |

## Session Ledger

Tracks token usage across the entire session.

### Ledger Format

```json
{
  "session_id": "2026-05-06T12:00:00",
  "start_time": "2026-05-06T12:00:00Z",
  "end_time": "2026-05-06T14:30:00Z",
  "tokens": {
    "read": 125000,
    "written": 45000,
    "saved_by_anatomy": 35000,
    "saved_by_repeat_block": 12000
  },
  "files": {
    "read_count": 47,
    "write_count": 23,
    "unique_reads": 38,
    "repeat_reads": 9
  },
  "waste": {
    "repeated_reads": 9,
    "anatomy_could_suffice": 5,
    "memory_bloat": 0,
    "total_wasted": 22000
  },
  "efficiency": {
    "useful_ratio": 0.82,
    "savings_ratio": 0.30
  }
}
```

### Location

`.claude/token-ledger.json` in the project root.

## Waste Detection Patterns

### 1. Repeated Reads (Most Common)

**Detection**: Same file path read 2+ times within a session.

**Action**: Block second read if content hasn't changed. Emit reminder: "File X was already read (Y tokens). Content unchanged since last read."

### 2. Anatomy-Could-Suffice

**Detection**: File is in anatomy.md with adequate description, and read purpose is exploration (not editing).

**Action**: Suggest anatomy description instead of full read. "File X has description: 'Y'. Read it anyway? (Z tokens)"

### 3. Memory Bloat

**Detection**: Memory files (MEMORY.md, cerebrum.md) exceeding size limits.

**Thresholds**:
- MEMORY.md: 25KB / 200 lines
- cerebrum.md: 15KB / 150 lines

**Action**: Warn and suggest consolidation. "MEMORY.md is X KB (limit: 25KB). Run consolidation?"

### 4. Stale Cerebrum

**Detection**: cerebrum.md not updated in >7 days.

**Action**: Session-start warning. "Cerebrum hasn't been updated in X days. Consider refreshing learnings."

### 5. Anatomy Miss Rate

**Detection**: >30% of files read have no anatomy entry or poor descriptions.

**Action**: Suggest re-scanning anatomy. "Anatomy miss rate: X%. Consider re-scanning project."

## Hook Integration

### Post-Read Hook
1. Estimate tokens from file content length
2. Check if file was previously read (repeat detection)
3. Check anatomy for alternative (anatomy-suffice detection)
4. Update session ledger

### Post-Write Hook
1. Estimate tokens written
2. Update session ledger
3. Check memory file sizes (bloat detection)

### Session-Start Hook
1. Load previous session ledger for comparison
2. Check cerebrum freshness
3. Reset session counters

### Stop Hook
1. Calculate session efficiency metrics
2. Generate waste report
3. Compare with previous sessions
4. Suggest optimization strategies

## Efficiency Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Useful Ratio | (total - wasted) / total | ≥0.80 |
| Savings Ratio | saved / (saved + read) | ≥0.25 |
| Repeat Rate | repeat_reads / total_reads | ≤0.10 |
| Anatomy Hit Rate | anatomy_hits / exploration_reads | ≥0.60 |

## Phase Integration

| Phase | Tracking Focus |
|-------|---------------|
| Phase 0-3 | Track exploration reads |
| Phase 5-6 | Track architecture reads |
| Phase 8 | Track development reads + writes |
| Phase 9 | Track QA reads |
| Phase 10 | Track optimization reads |
| Phase 12 | Full session analysis |

## Rules

1. **Estimation, not precision** — ratios are heuristics, not exact counts
2. **Waste detection is advisory** — sometimes repeated reads are necessary
3. **Ledger is per-session** — reset on new session, archive old ledgers
4. **Size limits are soft** — warn but don't block
5. **Efficiency trends matter more than absolute numbers** — compare across sessions
