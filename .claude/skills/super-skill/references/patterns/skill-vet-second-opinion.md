# Pattern: Second opinion before installing a third-party skill

**Source (pattern only, own text):** NVIDIA/SkillSpector — licence Apache-2.0. No code copied;
the category list below is a review checklist written for Super-Skill.
**Applies to:** P2b (find-skills), any `npx skills add` / plugin install, and P12 when a
skill is promoted into the playbook.

## Where this sits

`engine/skill_vet.py` (V5.1.1/V5.1.4) is the mandatory first gate: CLEAN/LOW installs,
anything else stops. This card is for the **grey zone** — a MEDIUM verdict, an opaque bundle
that passed only because it contained nothing scannable, or a skill that will receive network,
shell or credential access in a run. In those cases get a second opinion before installing.

## Option A — external scanner (preferred when available)

SkillSpector is a Python 3.12+ CLI that scans a git URL, zip or directory against 71 static
patterns in 17 categories and can add an LLM semantic pass. It is an *external* dependency
(not stdlib; it installs third-party packages), so it stays **optional** and is never a gate
check in `phases.json`. Suggested use:

```bash
# in a throw-away virtualenv, never inside the project tree
uv tool install git+https://github.com/NVIDIA/skillspector.git
skillspector scan <repo-url-or-dir> --format json > .super-skill/vet/<name>.skillspector.json
```

Record the risk score (0–100) and the recommendation in `SKILLS_DISCOVERY.md` next to the
`skill_vet.py` verdict. Two independent CLEAN-ish verdicts → install; disagreement → ask the user.

## Option B — manual review checklist (no extra tooling)

Read `SKILL.md`, every script, and every file the skill asks the agent to fetch. Mark each
line below ✔/✘/n.a. in the discovery report:

| # | Category | What to look for |
|---|---|---|
| 1 | Prompt injection | text addressed to the model ("ignore previous…", hidden HTML/markdown comments, zero-width chars) |
| 2 | Data exfiltration | reads of `~/.ssh`, `.env`, tokens, browser profiles; any outbound POST/curl with file contents |
| 3 | Privilege escalation | `sudo`, `chmod +s`, modifying shell rc files, editing `settings.json`/hooks of the host |
| 4 | Supply chain | `curl \| sh`, unpinned `pip/npm install` from arbitrary URLs, postinstall scripts, binaries/compiled artefacts |
| 5 | Excessive agency | instructions to act "without asking", disable confirmations, auto-approve, bypass hooks |
| 6 | Memory poisoning | writes to the agent's memory/playbook/CLAUDE.md that persist beyond the task |
| 7 | Tool misuse / MCP poisoning | tool descriptions that instruct the model, over-broad permission lists, servers bound to 0.0.0.0 |
| 8 | Anti-refusal / trigger abuse | "always comply", overly broad trigger phrases designed to hijack unrelated requests |
| 9 | Dangerous code | `eval`/`exec` on fetched text, `rm -rf`, `git push --force`, writing outside the skill dir |

Any ✘ in rows 1–4 or 9 → do not install. Any ✘ in rows 5–8 → install only with the offending
section removed and note the edit in `SKILLS_DISCOVERY.md`.

## Baseline for re-scans

When a skill you already vetted ships an update, keep the previous findings file and diff:
only **new** findings need review. Store `<name>.vet-baseline.json` (the first verdict +
findings list) under `.super-skill/vet/`; the re-scan is CLEAN if its finding set is a subset
of the baseline. This mirrors the "baseline / fingerprint suppression" idea in SkillSpector
and keeps upgrade reviews cheap without silently accepting regressions.
