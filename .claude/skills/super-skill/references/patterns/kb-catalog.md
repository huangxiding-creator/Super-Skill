# Pattern: KB catalog with "read if" triggers（知识库目录 + 读取条件）

**Source (pattern only, own text):** aerovato/operator-memory — licence BSD-3-Clause. No code or
text copied; the idea adapted here is "a small catalog loaded at session start, where every
document carries a condition for when to open it; everything else stays on disk".
**Applies to:** P3 (create), P8 Workers and Judges (consult), P12 (maintain), every resumed session.

## The problem

`KNOWLEDGE_BASE/` grows to dozens of files. A fresh session or a Worker in its own worktree
then either reads all of it (context spent on data it does not need) or none of it (re-explores
the codebase, re-learns decisions that are already written down). `ss mem search` helps only
when you already know what to ask; a newcomer to the task does not.

## The rule

> Keep one short catalog, `KNOWLEDGE_BASE/INDEX.md`, with one line per document: what it holds
> and **when to read it**. Every session and every Worker reads the catalog (plus `CONTEXT.md`)
> first, then opens only the documents whose *Read if* matches the task.

Same start, same orientation — deterministic, no embeddings, no extra service.

```markdown
# KNOWLEDGE_BASE index

| Document | Holds | Read if |
|---|---|---|
| [auth.md](auth.md) | token flow, session expiry, OAuth provider quirks | task edits `src/auth/**` or covers REQ-010…REQ-014 |
| [billing.md](billing.md) | webhook idempotency, proration decisions | task touches payments, invoices or REQ-03x |
| [decisions.md](decisions.md) | ADR log: accepted and rejected options | changing a component boundary or adding a dependency |
| [integrations/](integrations/INDEX.md) | sub-index: third-party APIs | task calls an external API |
```

## Writing good lines

- **Triggers, not topics.** "about auth" is weak; "task edits `src/auth/**` or covers REQ-01x"
  is strong — a Worker can match it against its task's `files` and `covers` fields mechanically.
- **Keep it short.** One line per document, roughly one screen in total. When it outgrows that,
  split by area into sub-indexes; the main index then holds one line per sub-index.
- **The catalog is the entry point, search is the fallback.** Use `ss mem search` for
  "where was X mentioned"; use the catalog to know what exists before you know what to search.

## Keeping it true (same discipline as canonical docs, ss-worker step 5)

- **A document that is not in the catalog is invisible.** Adding, renaming, splitting or
  merging a `KNOWLEDGE_BASE/` document changes its catalog line in the same commit.
- **Update the source, do not add a record.** When project truth changes, edit the document
  that states it in place; no "update 2026-xx-xx" notes appended below stale text, no parallel
  document for something an existing one covers. Overlapping documents → consolidate; a
  document too long to read for one task → split and add sub-index lines.
- **Cheap check (Think in Code).** At the P3 gate and in P12, compare the `.md` files under
  `KNOWLEDGE_BASE/` with the link targets in `INDEX.md` using a short script that prints only
  two lists — documents missing from the catalog and catalog links that point nowhere — and
  expect both to be empty. See [think-in-code](think-in-code.md).

## Checklist

- [ ] P3: `KNOWLEDGE_BASE/INDEX.md` exists and lists every KB document with a *Read if* trigger.
- [ ] Worker report names the KB documents it opened (and why they matched), not "read the KB".
- [ ] Judge: a commit that adds/renames/splits a KB document also changes `INDEX.md`.
- [ ] P12: catalog check prints two empty lists; stale or overlapping documents were merged.

Not machine-enforced yet: the P3 gate in `phases.json` still only requires one KB file and
`CONTEXT.md` (the nightly self-update may not edit phase contracts). A maintainer can promote
this to a `file_exists KNOWLEDGE_BASE/INDEX.md` gate check once the convention has proven itself.
