# Pattern: Think in Code（用脚本算，只把结果放进上下文）

**Source (pattern only, own text):** mksglu/context-mode — licence ELv2 (source-available, no code copied).
"Shape, don't dump" section: headroomlabs-ai/headroom — licence Apache-2.0 (pattern only, own text).
**Applies to:** every phase; strongest effect in P2 (repo survey), P8 (workers), P9 (QA), P10 (Ralph).

## The problem

Each raw tool result lands in the context window in full. Reading fifty files to count
functions, dumping a 400-line test log to find one failure, or paging through twenty issues
to pick three, spends context on *data* that the model then has to re-derive a *summary* from.
After compaction the data is gone and the summary may be wrong.

## The rule

> When the answer is a *computation over data*, write the computation, run it, and read only
> its printed result. The LLM programs the analysis; it does not perform it by hand.

Concretely, before issuing the Nth `Read`/`Grep` on the same question, stop and ask:
*"Could a 10-line script print the answer?"* If yes, write the script (stdlib Python, shell,
or node — whatever the repo already uses), run it once, and keep the raw data out of context.

| Instead of | Do |
|---|---|
| `Read` 30 files to find which define a class | one `python - <<EOF` that walks the tree and prints `file: class` lines |
| paste a full test log to locate the failing test | run the suite with `-q`/`--tb=line` or pipe through a script that prints only failures and their first assertion |
| fetch 20 issues/PRs to shortlist 3 | `gh … --json … -q` with a filter expression; print title + url only |
| read every `KNOWLEDGE_BASE/*.md` to answer a question | read `KNOWLEDGE_BASE/INDEX.md` ([kb-catalog](kb-catalog.md)) or `ss mem search "<query>"` (FTS5) and open the top hit only |
| re-read the whole state after compaction | read `.super-skill/handoff.md` and `ss status`, nothing else |

## Shape, don't dump — when a large output must be read

Sometimes there is no question to compute yet: you have to *look* at a 2 000-line log, a big
JSON API response or a long diff. Then reshape it before it reaches the context:

- **Keep the signal verbatim.** Lines with `ERROR`/`FATAL`/`Traceback`/`FAILED`, non-zero exit
  codes, and items whose fields differ from the majority (the one record with `status: 500`
  among 400 with `200`) are copied exactly — never paraphrased.
- **Keep the boundaries.** The first and last few entries show the shape of the data and where
  it ended; drop the repetitive middle and replace it with a count, e.g.
  `… 412 similar rows omitted (status=200, same keys) …`.
- **Keep the original retrievable.** Write the full output to a file that is not committed —
  the OS temp dir, or `.super-skill/scratch/` after adding `scratch/` to `.super-skill/.gitignore`
  — and print its path next to the shaped view. When a later step needs a detail you dropped,
  `grep` that file instead of re-running the command (which may be slow, costly or no longer
  reproducible).
- **Prose and code do not shrink this way.** Source files, specs and error messages are already
  dense; read the relevant range (`Read` with offset/limit) instead of compressing them.

## Guard rails

- **Print the result, not the data.** A script that `cat`s the files back defeats the purpose.
  Aim for an output that fits in one screen; truncate lists with a count (`… and 37 more`).
- **Scripts are evidence.** Keep the one-liner in the hand-off or task note so the Judge can
  re-run it (constitution C12/C14: verify with commands, quote real output).
- **Do not trade correctness for brevity in the answer itself.** This rule is about *where
  data goes*, not about how terse the final reply is. Aggressive "be brief" prompts have been
  reported to hurt coding/reasoning quality; keep Super-Skill's existing output style unchanged.
- **Never shape away the evidence a gate needs.** Verify commands, test summaries and the
  failing assertion are quoted as produced; shaping applies to the bulk around them.
- **Subagents are the other half.** Research and exploration that would still flood context
  should run in an `ss-researcher`/Explore subagent that returns the conclusion (see §7 JIT
  context); Think in Code is for work that stays in the main session.

## Checklist for Workers (P8) and Judges

- [ ] Any step that touched > 5 files for *information* (not editing) used a script or a subagent.
- [ ] Test runs were filtered to failures before being read.
- [ ] Large outputs that had to be read were shaped (signal verbatim, head/tail, counts) and the
      full original was saved to an uncommitted file whose path is in the task note.
- [ ] Printed outputs that mattered are quoted in the task note with the command that produced them.
