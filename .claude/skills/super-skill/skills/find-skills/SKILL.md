---
name: find-skills
description: Helps users discover and install agent skills from the open agent skills ecosystem. Integrates with Super-Skill Phase 2b for automated skills discovery during project planning.
tags: [discovery, skills, ecosystem, automation]
version: 1.1.0
source: https://github.com/vercel-labs/skills/tree/main/skills/find-skills
integrated-with: super-skill v3.3+
---

# Find Skills

This skill helps you discover and install skills from the open agent skills ecosystem.

## When to Use This Skill

Use this skill when the user:
- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)

## What is the Skills CLI?

The Skills CLI (`npx skills`) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**
- `npx skills find [query]` - Search for skills interactively or by keyword
- `npx skills add <skill-ref>` - Install a skill from GitHub or other sources
- `npx skills check` - Check for skill updates
- `npx skills update` - Update all installed skills

**Browse skills at:** https://skills.sh/

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:
1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Search for Skills

Run the find command with a relevant query:

```bash
npx skills find [query]
```

For example:
- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

The command will return results like:
```
Install with npx skills add <skill-ref>
vercel-labs/agent-skills@vercel-react-best-practices
└ https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### Step 3: Present Options to the User

When you find relevant skills, present them to the user with:
1. The skill name and what it does
2. The install command they can run
3. A link to learn more at skills.sh

Example response:
```
I found a skill that might help! The "vercel-react-best-practices" skill provides
React and Next.js performance optimization guidelines from Vercel Engineering.

To install it:
npx skills add vercel-labs/agent-skills@vercel-react-best-practices

Learn more: https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices
```

### Step 4: Vet, Then Offer to Install

Skills run with the agent's full trust (they can steer the model and ship scripts), so
**vet before installing** — never install a third-party skill unread:

```bash
git clone --depth 1 https://github.com/<owner>/<repo> <tmp>/<repo>
python "<super-skill base>/engine/skill_vet.py" <tmp>/<repo>/<path-to-skill>
```

| Verdict | Action |
|---|---|
| `CLEAN` / `LOW` | OK to install. Clean means "nothing obvious", not "proven safe". |
| `MEDIUM` | Show the findings to the user; install only after they agree. A reviewed, harmless rule may be suppressed with `--ignore <RULE>`. |
| `HIGH` / `CRITICAL` (exit 1) | **Do not install.** Show the findings (file:line + rule). Install only on an explicit user override that names the risk. |

Then, if the user wants to proceed:

```bash
npx skills add <skill-ref> -g -y
```

The `-g` flag installs globally (user-level) and `-y` skips confirmation prompts — which is
exactly why the vetting step above must come first.

## Common Skill Categories

When searching, consider these common categories:

| Category | Example Queries |
| --------------- | ---------------------------------------- |
| Web Development | react, nextjs, typescript, css, tailwind |
| Testing | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| Documentation | docs, readme, changelog, api-docs |
| Code Quality | review, lint, refactor, best-practices |
| Design | ui, ux, design-system, accessibility |
| Productivity | workflow, automation, git |

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
3. **Check popular sources**: Many skills come from `vercel-labs/agent-skills` or `ComposioHQ/awesome-claude-skills`

## When No Skills Are Found

If no relevant skills exist:
1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. Suggest the user could create their own skill with `npx skills init`

Example:
```
I searched for skills related to "xyz" but didn't find any matches.

I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill:
npx skills init my-xyz-skill
```

---

## Integration with Super-Skill (Phase 2b)

When used as part of Super-Skill's Phase 2b: Skills Discovery, this skill operates autonomously:

### Automated Skills Discovery Process

```
Phase 2b Trigger: After GitHub Discovery (Phase 2) finds no suitable project
                  OR when specialized capabilities are needed

STEP 1: Identify Required Capabilities
- Analyze project requirements from Phase 1/2
- List required technical domains
- Map domains to potential skills

STEP 2: Search Skills Ecosystem
- Execute targeted searches for each domain
- Query: npx skills find <domain> <task>
- Collect and rank results

STEP 3: Evaluate Skills
For each candidate skill:
- Relevance to project requirements
- Installation complexity
- Maintenance status
- License compatibility
- Documentation quality

STEP 4: Vet, Then Auto-Install Critical Skills
- Fetch the source to a temp dir (git clone --depth 1), never install first
- Run: python "<base>/engine/skill_vet.py" <skill-dir> --json
- Auto-install only if relevance ≥80% AND verdict is CLEAN or LOW
- MEDIUM → list under "Manual review items", do not auto-install
- HIGH/CRITICAL → reject, record rule ids + file:line in the report
- Use: npx skills add <skill-ref> -g -y
- Log installations and vet verdicts to project record

STEP 5: Generate Skills Report
Create SKILLS_DISCOVERY_REPORT.md:
- Found skills list with scores
- Vet verdict (level, score, top findings) per candidate
- Installed skills list
- Integration recommendations
- Manual review items (if any)
```

### Decision Matrix for Skills Discovery

```
IF project requires specialized domain:
  → Search for domain-specific skills
  → Evaluate top 3 candidates
  → Vet each with skill_vet.py
  → Auto-install if score ≥ 80% AND vet verdict ≤ LOW

IF no suitable skills found:
  → Document gap in SKILLS_DISCOVERY_REPORT.md
  → Proceed to Phase 3 (Knowledge Base)
  → Flag for potential skill creation

IF skills found and installed:
  → Update project context with new capabilities
  → Proceed to Phase 4 (Requirements)
```

### Gate Checks for Phase 2b

- [ ] Skills ecosystem searched for all required domains
- [ ] Candidate skills evaluated and scored
- [ ] Every install candidate vetted with skill_vet.py (verdict recorded)
- [ ] Critical skills (≥80% relevance, vet ≤ LOW) auto-installed
- [ ] SKILLS_DISCOVERY_REPORT.md generated
- [ ] Integration recommendations documented

### Deliverables

- `SKILLS_DISCOVERY_REPORT.md` - Comprehensive skills analysis
- Installed skills ready for use
- Updated project context with new capabilities

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-10-01 | Pre-install vetting gate (`engine/skill_vet.py`, pattern from NVIDIA/SkillSpector, Apache-2.0) |
| 1.0.0 | 2026-03-01 | Initial integration with Super-Skill V3.3 |

---

## License

MIT License - Based on [Vercel Labs Skills](https://github.com/vercel-labs/skills)
