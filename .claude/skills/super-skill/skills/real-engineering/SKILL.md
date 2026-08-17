---
name: real-engineering
description: Composable engineering flows (Matt Pocock) — grilling design-tree interviews, CONTEXT.md glossary + ADRs, tracer-bullet tickets with blocking edges, human-only-step wizards, red-first bug loops. Trigger when stress-testing a plan, resolving fuzzy jargon, splitting work into tickets, or hitting a wall only a human can pass.
---

# Real Engineering (from mattpocock/skills)

**Source**: [mattpocock/skills](https://github.com/mattpocock/skills) — "Skills for real engineers, not vibe coding." Small, composable, adaptable. Deliberately anti-monolith: *frameworks that own the process take away your control*. Super-Skill keeps its 14-phase spine for autonomous runs; this sub-skill adds the disciplines that operate at the **interaction points** — where alignment, language, and human-only steps live.

## Main Flow

```
grill (design tree) → to-spec → to-tickets (tracer bullets + blocking edges) → implement (/tdd at seams + two-axis review)
On-ramps: diagnosing-bugs (broken) · wayfinder (foggy multi-session effort)
```

Keep grill → spec → tickets in **one unbroken context window**; each implement starts fresh from its ticket. If the session nears the **smart zone** limit (~150k tokens where reasoning is still sharp), `/compact` at the nearest phase boundary — never push on degraded.

## Mechanism 1 — Grilling (deep interview)

Super-Skill's Hybrid Clarification Gate is the **quick path** (≤3 questions, ambiguity 4–7). Grilling is the **deep path** for big decisions: interview relentlessly until nothing is silently assumed.

- Map the discussion as a **design tree**: every decision branches into the decisions hanging off it.
- Work in **rounds**. The **frontier** = decisions whose prerequisites are settled. Ask the whole frontier in one round, numbered, each with a recommended answer; wait before the next round.
- **Facts are the agent's job, never the user's** — dispatch sub-agents to find facts; only the *decisions* go to the user. Don't block the round on a running exploration.
- Done when the frontier is empty. Do not act until the user confirms shared understanding.

Question format:

```
❓ **Q1** — **<title>**: <body>
➡️ <recommended answer>
```

## Mechanism 2 — Ubiquitous Language (CONTEXT.md + ADRs)

Agents dropped into a project guess the jargon and use 20 words where 1 would do. Fix: a glossary, updated the moment terms crystallise (never batched).

- `CONTEXT.md` (repo root; `CONTEXT-MAP.md` if multiple bounded contexts) — **glossary and nothing else**: `**Term**: definition (1–2 sentences, what it IS) + _Avoid_: synonyms-to-ban`. No implementation details, no spec content. Create lazily on first resolved term.
- Challenge against the glossary when the user's words conflict; sharpen fuzzy terms ("account" → Customer or User?); stress-test relationships with concrete edge-case scenarios; cross-reference with code and surface contradictions.
- **ADR** (`docs/adr/NNNN-slug.md`, 1–3 sentences is enough) — only when ALL three hold: **hard to reverse** + **surprising without context** + **a real trade-off**. Numbering: highest existing + 1.
- Verify both with `scripts/context_lint.py` (see Tests).

## Mechanism 3 — Tracer-Bullet Tickets (Phase 6 upgrade)

Break a spec into **vertical slices**, not layer-cakes:

- Each slice cuts a COMPLETE path through every layer (schema, API, UI, tests) and is demoable alone.
- Each slice fits one fresh context window; each declares its **blocking edges** (which tickets gate it). Work the **frontier**: tickets whose blockers are all done.
- Tickets describe end-to-end behaviour from the user's perspective — no file paths or code snippets (they go stale); exception: a prototype snippet that encodes a decision (state machine, schema, type shape).
- **Wide refactors are the exception**: one mechanical change fanning across the codebase (rename a column, retype a shared symbol) goes **expand–contract** — add the new form beside the old → migrate call sites in blast-radius-sized batches, each green → delete the old form once no caller remains.
- Quiz the user on the breakdown (granularity? edges correct? merge/split?) before publishing.

## Mechanism 4 — Wizard (human-only steps)

For steps **only a human can perform** — provisioning infrastructure, credentials, CI secrets, unfamiliar third-party dashboards, one-off migrations. The agent *generates* an interactive bash script that opens each URL, says exactly what to click, captures values, writes `.env` / `gh secret`, confirms at every stage. The UX library is already written: copy `scripts/wizard_template.sh`, author only the stages below the `STAGES` marker, verify with `bash -n` + static trace (never run end-to-end — it blocks on human input). Do NOT invoke when the agent could do the step itself.

## Mechanism 5 — Red-First Bug Diagnosis (Phase 8/9 upgrade)

**The feedback loop IS the skill.** Everything else is mechanical. Before theorising about any hard bug, build one command that already goes **red on this bug**:

1. Ladder: failing test → curl script → CLI + snapshot diff → headless browser → replay a captured trace → throwaway harness → fuzz loop → `git bisect run` harness → differential old-vs-new → HITL bash script (last resort).
2. **Tighten** it: faster (2s not 30s), sharper (assert the specific symptom), deterministic (pin time, seed RNG). A flaky loop is barely better than none.
3. Non-deterministic bugs: raise the reproduction rate (loop 100×, stress, narrow timing windows) until debuggable — a clean repro is not required.
4. Cannot build a loop? Say so explicitly, list what you tried, ask for env access / a redacted artifact / permission to instrument. **Never hypothesise without a red loop.** Fix ends with a regression test locking the bug down. Redact every secret in anything you show.

## Strengthened Mechanisms

- **Two-axis code review** (Phase 9 `verification-gate`): review the diff since a fixed point on two axes as parallel sub-agents — **Standards** (repo conventions + Fowler smell baseline) and **Spec** (does it faithfully implement the originating issue?).
- **Phase boundaries** (`context-compressor`): at each phase boundary choose deliberately — Continue / `/clear` / handoff file (only for new harness, new directory, colleague, or mid-phase side-task) / subagent / `/compact` (the default). Decide *at* the boundary; mid-phase, continue.
- **wait-what**: the instant a message doesn't land, re-pitch it with the missing context, in plain technical English, using the CONTEXT.md vocabulary.

## Phase Wiring

| Super-Skill phase | Mechanism |
|---|---|
| Phase 3 (Knowledge Base) | Emit `CONTEXT.md` glossary alongside KNOWLEDGE_BASE/ |
| Phase 4 (Requirements) | Deep path = grilling; quick path = Hybrid Clarification Gate |
| Phase 5 (Architecture) | ADRs for decisions passing the 3-part test |
| Phase 6 (WBS) | Tracer-bullet tickets + blocking edges; expand–contract for wide refactors |
| Phase 7/11 (Init/Deploy) | Wizard for human-only steps (credentials, dashboards, secrets) |
| Phase 8/9 (Dev/QA) | Red-first diagnosis; two-axis review before commit |
| Any (foggy big effort) | wayfinder: decision tickets producing *decisions, not deliverables*, then collapse into spec |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/wizard_template.sh` | Bash wizard library (stage/ask_secret/write_env/set_secret) — copy + author stages |
| `scripts/context_lint.py` | Lint `CONTEXT.md` glossary format + `docs/adr/` numbering |

## Tests

```bash
python skills/real-engineering/scripts/test_context_lint.py
```

Covers: glossary parsing (valid/empty-definition/duplicate-term/stray-Avoid/empty-Avoid), ADR numbering (format/duplicates), lazy-creation (missing paths are NOT errors — formats create files lazily by design), JSON output, exit codes. Auto-discovered by `health_check.py`.

## Full Source Mapping

All 25 stable source skills → Super-Skill bindings (absorbed / strengthened / already-covered), with the deep details (round format, expand–contract, two-axis review, phase-boundary tree): [references/mattpocock-skills.md](../../references/mattpocock-skills.md).
