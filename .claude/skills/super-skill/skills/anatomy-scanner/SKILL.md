---
name: anatomy-scanner
description: Project file indexing with auto-generated descriptions and token estimates. Scans codebase to build anatomy.md index, enabling ~80% token savings by avoiding unnecessary file reads. Language-aware extractors for 20+ frameworks.
---

# Anatomy Scanner

Inspired by [OpenWolf](https://github.com/cytostack/openwolf) project anatomy system. Provides structured file index with descriptions and token estimates so Claude can decide whether to read a file.

## When to Use

- At project start (Phase 7 initialization)
- Before large codebase exploration (Phase 8)
- When context is scarce and files are many
- Before refactoring sessions (Phase 10)
- On session start to refresh stale anatomy

## When NOT to Use

- Small projects (<20 files)
- When you already know exactly which files to read
- During active file editing (updates happen automatically via hooks)

## How It Works

### Anatomy File Format

The system maintains `anatomy.md` in the project root:

```markdown
# Project Anatomy

> Auto-generated file index. Last scanned: 2026-05-06T12:00:00Z
> Files: 42 | Estimated tokens: ~15,000

| Path | Description | Tokens |
|------|-------------|--------|
| src/app.ts | Express app entry point with middleware | ~120 |
| src/routes/users.ts | User CRUD routes with validation | ~200 |
| src/models/user.ts | User model with Prisma schema | ~80 |
```

### Scanning Protocol

1. **Walk** project directory recursively
2. **Skip** binary files, node_modules, .git, dist, build
3. **Skip** files >1MB (too large for useful description)
4. **Cap** at 500 files max
5. **Extract** description using language-aware heuristics
6. **Estimate** tokens: `ceil(text.length / ratio)` where ratio = code:3.5, prose:4.0, mixed:3.75
7. **Write** atomic: write to `.tmp` then rename (crash-safe)

### Language-Aware Description Extraction

| Language/Framework | Extraction Strategy |
|-------------------|---------------------|
| TypeScript/JS | exports, functions, classes, React components |
| Python | classes, decorators, def functions |
| Go | package, func, type, interface |
| Rust | fn, struct, impl, mod |
| Java/Kotlin | class, interface, @annotations |
| PHP/Laravel | class, routes, migrations |
| Ruby/Rails | class, module, def |
| SQL | CREATE TABLE, CREATE INDEX |
| Docker/YAML | service names, key configs |
| Config files | purpose inference from filename |

### Integration with Hooks

**Pre-Read Hook**: Before reading a file, check anatomy. If description suffices, skip the read.

**Post-Write Hook**: After writing/editing a file, update its anatomy entry automatically.

### Token Savings

| Scenario | Without Anatomy | With Anatomy | Savings |
|----------|----------------|--------------|---------|
| Exploring 50 files | ~50,000 tokens | ~10,000 tokens | 80% |
| Finding one function | ~5,000 tokens | ~500 tokens | 90% |
| Refactoring session | ~80,000 tokens | ~25,000 tokens | 69% |

## Commands

```bash
# Scan and generate/update anatomy.md
Scan project directory and generate anatomy.md

# Check freshness (warns if >24h old)
Check if anatomy.md needs refresh
```

## Phase Integration

| Phase | Usage |
|-------|-------|
| Phase 7 | Initial scan during project init |
| Phase 8 | Continuous updates during development |
| Phase 9 | Reference during QA exploration |
| Phase 10 | Refresh before optimization loop |

## Rules

1. **Anatomy is an index, not content** — descriptions are one-line summaries
2. **Atomic writes** — always write to `.tmp` then rename
3. **Max 500 files** — skip deeply nested vendor dirs
4. **Token estimates are approximate** — actual usage varies by model
5. **Freshness matters** — stale anatomy (<24h) gets a warning
6. **Never skip reading for implementation** — anatomy is for exploration only
