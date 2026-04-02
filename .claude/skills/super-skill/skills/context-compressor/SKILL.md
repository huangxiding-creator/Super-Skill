---
name: context-compressor
description: Produces a 9-part structured continuation summary for long sessions, agent handoffs, and context window pressure. Preserves user intent and correction history.
---

# Context Compressor

Inspired by [cc-harness-skills](https://github.com/LearnPrompt/cc-harness-skills) structured-context-compressor pattern.

## When to Use

- Context window approaching limits (>75% used)
- Before agent-to-agent handoffs
- Session pause/resume across breaks
- Before compaction events
- When starting a new session that continues previous work

## The 9-Part Structure

```
## 1. Primary Request and Intent
[What the user actually asked for, in their words]

## 2. Key Technical Concepts
[Domain knowledge, architectural decisions, tech stack choices]

## 3. Files and Code Sections
[What was created/modified, with key snippets]

## 4. Errors and Fixes
[What went wrong and how it was resolved]

## 5. Problem Solving
[Approaches tried, abandoned paths, reasoning]

## 6. All User Messages
[Every user message, or accurate paraphrase - NEVER compress corrections away]

## 7. Pending Tasks
[What remains to be done]

## 8. Current Work
[Exactly where we left off, at what line in what file]

## 9. Next Aligned Step
[The single most important thing to do next]
```

## Critical Rules

- **Preserve ALL user messages** - corrections changed the direction of work; losing them means repeating mistakes
- **Section 6 is non-negotiable** - if you compress nothing else, keep the user messages
- **Section 8 must be precise** - "file X, line Y, implementing Z" not "was working on something"
- **Section 9 is ONE step** - not a plan, just the immediate next action

## Integration with Hooks

The `Stop` hook triggers context compression before session end, producing a `SESSION_SUMMARY.md` in the project root using this 9-part format.

## Output Contract

```json
{
  "sections_completed": 9,
  "user_messages_preserved": true,
  "current_work_precise": true,
  "next_step_single": true,
  "estimated_token_savings": "70-90%"
}
```
