---
name: ai-mastery-7
description: The 7 disciplines that turn an AI agent from a "question tool" into a fully autonomous workflow partner — distilled from Boris Cherny's Claude Code methodology. Invoke when the user asks how to use Super-Skill well, wants a weekly retrospective, asks "why does this code exist", or wants to verify their own AI-usage habits.
---

# ai-mastery-7 — The 7 Disciplines of AI Mastery

> Source: Boris Cherny (creator of Claude Code), distilled into 7 operational disciplines.
> **Core thesis**: don't treat AI as a tool — it's an autonomous agent. Give it **context + tools**, then let it run the whole workflow. Most people use <1% of their AI's capability.

This sub-skill is the **integrative layer** that binds existing Super-Skill mechanisms to the 7 human-side disciplines that most multiply AI output. Each discipline below names the Super-Skill mechanism that already implements it, plus a concrete protocol.

## When to invoke

- User asks "how do I use Super-Skill / Claude Code well?" → run **Discipline 1**
- User says "weekly retrospective / 周报 / 这周做了什么" → run **Discipline 4** script
- User asks "why does this code/decision exist?" → run **Discipline 3** script
- User is about to say "just build X" with no plan → enforce **Discipline 5**
- User wants to self-assess their AI-usage habits → run the **maturity checklist**

## The 7 Disciplines

| # | Discipline | Super-Skill mechanism | Type |
|---|-----------|----------------------|------|
| 1 | Let AI teach you how to use itself | this skill's **onboarding dialog** | protocol |
| 2 | Domain onboarding via knowledge-base Q&A | Phase 3 KB + `continuous-learning-v2` | existing |
| 3 | Understand history → understand "why" | `rationale_mining.py` (below) | **new tool** |
| 4 | Weekly retrospective from work logs | `weekly_retrospective.py` (below) | **new tool** |
| 5 | Plan before code | Phase 4 gate + `brainstorming` | existing |
| 6 | Feedback tools → self-iteration | `verification-gate` + Phase 10 Ralph Loop | existing |
| 7 | Long-term memory (CLAUDE.md / usage manual) | `memory-pipeline` + `cerebrum` + MEMORY.md | existing |

### Discipline 1 — Let AI teach you how to use itself
**Don't rush to assign work.** First calibrate the tool's capability boundary against *your* scenario.

Protocol (onboarding dialog, run once per new user/project):
1. Ask the agent: "What can you do in one shot? What needs 2–3 steps? What needs interactive help? Where are your hard limits?"
2. Point it at THIS skill tree + `references/skills-matrix.md` and ask it to map its own capabilities to the user's stated goal.
3. Record the agreed capability boundary into `CLAUDE.md` (Discipline 7) so future sessions start calibrated.

> Rationale: a tutorial is someone else's calibration. A direct dialog is real-time calibration to *your* context — strictly faster.

### Discipline 2 — Quick domain onboarding via knowledge-base Q&A
When entering a new codebase/domain, **don't read everything — ask the knowledge base**.

- Super-Skill builds this in Phase 3 (`KNOWLEDGE_BASE/` + `SCHEMAS.md`).
- For an existing repo, point `continuous-learning-v2` at it and ask: "how is X used? how did concept Y land in practice? where is method Z instantiated?"
- **No KB yet?** Build one first — let the agent harvest the domain's core references, then query it. Anthropic compresses new-hire onboarding from 2–3 weeks to 2–3 days this way.

### Discipline 3 — Understand history to understand "why"  *(new tool)*
A bare technique ("write good titles") is mechanical. The **why** (what problem, what conditions, when it fails) is real learning.

Run on any file or path:
```bash
python scripts/rationale_mining.py <path>            # full rationale timeline
python scripts/rationale_mining.py <path> --max 5    # top 5 formative commits
```
It walks `git log --follow` + `git blame` to surface *when each segment was introduced and why* (from commit messages). Pair with the agent interpreting the timeline into a "conditions where this still holds / breaks" summary.

### Discipline 4 — Weekly retrospective from work logs  *(new tool)*
Most people are *fuzzy* on what they actually delivered. Turn git history into a clear list.

```bash
python scripts/weekly_retrospective.py                          # this week, this repo
python scripts/weekly_retrospective.py --since 7 --area src     # last 7 days, src/ only
python scripts/weekly_retrospective.py --json                   # machine-readable
```
Emits markdown sections: **Delivered** · **In progress** · **Scope signals** (larger-than-expected commits, churn). Drop straight into a weekly report or retrospective doc.

### Discipline 5 — Plan before code
Never let the agent "just build X". The cheapest rework-avoider is a plan.

- Super-Skill enforces this at the **Phase 4 approval gate** and via `brainstorming`.
- The one-line guardrail: **"写代码之前先做个计划，跑给我看，同意了你再写。"**
- For multi-step intent, the "咒语" `commit push PR` is enough — a strong agent chains the tools itself; do not hand-hold.

### Discipline 6 — Give it feedback tools, let it self-iterate
An agent that can *see its own output* iterates to near-perfect in 2–3 rounds. One that can't, stops at "八九不离十".

- Wire a verifier into the loop: unit tests, `design-qc` screenshots, `verification-gate`, an iOS-simulator capture, a linter — anything that returns pass/fail or a delta.
- Phase 10 Ralph Loop operationalizes this as Analyze → Improve → Validate → Document → check convergence.
- **Variance inequality**: when improvement stalls, strengthen the *verifier*, not the generator.

### Discipline 7 — Long-term memory (CLAUDE.md / usage manual)
Every session otherwise starts from zero. Write the context down once.

- `CLAUDE.md` (project) + `MEMORY.md` (index) + `cerebrum` (Do-Not-Repeat patterns) are Super-Skill's memory substrate.
- **Keep CLAUDE.md short** — every line taxes every future session. Shorter = smarter.
- Commit it to version control: write once, the whole team benefits.
- Personal version: keep a "使用手册" of your output style, common workflows, project background. Load it every session.

## AI-Mastery Maturity Checklist

Rate each on 0 / 1 / 2 (0=never, 1=sometimes, 2=always). Score ≥10 = strong.

- [ ] I calibrated capability boundaries with the agent before assigning real work (D1)
- [ ] I query a knowledge base before reading a new codebase linearly (D2)
- [ ] I can explain *why* my own past decisions hold / when they break (D3)
- [ ] I run a weekly retrospective instead of trusting a fuzzy sense of progress (D4)
- [ ] I never say "just build X" without an approved plan (D5)
- [ ] Every agent task has a verifier that lets it see its own result (D6)
- [ ] My project has a short, version-controlled CLAUDE.md (D7)

## Scripts

| Script | Discipline | What it does |
|--------|-----------|--------------|
| `scripts/weekly_retrospective.py` | D4 | git log → weekly delivered/in-progress/scope-signal report |
| `scripts/rationale_mining.py` | D3 | git history of a path → "why it looks like this" timeline |

Both are pure-stdlib, offline, deterministic. Tests: `scripts/test_ai_mastery.py` (runs on a temp git repo).

## See also

- Full mapping + source attribution: [references/ai-mastery.md](../../references/ai-mastery.md)
- Related skills: `brainstorming` (D5), `verification-gate` (D6), `memory-pipeline` + `cerebrum` (D7), `continuous-learning-v2` (D2), `post-run-evolution` (D4 session-level).
