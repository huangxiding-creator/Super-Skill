---
name: pre-run-upgrade
description: Pre-execution sub-skill upgrade and best practices discovery. TRIGGER at the start of every Super-Skill session before Phase 0. Capabilities: (1) Check and upgrade all sub-skills to latest versions, (2) Search GitHub for trending best practices, (3) Discover and integrate new patterns, (4) Update Context Hub registry, (5) Sync evolution learnings. Ensures Super-Skill starts with the most current capabilities and knowledge.
---

# Pre-Run Upgrade

## Overview

Executes at the start of every Super-Skill session to ensure maximum capability readiness. Searches for upgrades, best practices, and new patterns before beginning any project work.

## Execution Sequence

```
┌─────────────────────────────────────────┐
│  PRE-RUN UPGRADE (Before Phase 0)       │
├─────────────────────────────────────────┤
│  1. Version Check                       │
│  2. Sub-Skill Upgrade                   │
│  3. Best Practices Search               │
│  4. Pattern Integration                 │
│  5. Context Hub Sync                    │
│  6. Evolution Learnings Sync            │
└─────────────────────────────────────────┘
```

## Step 1: Version Check

Check all sub-skills for available updates:

```bash
# Check Super-Skill version
cd ~/.claude/skills/super-skill && git fetch && git status

# Check each sub-skill with GitHub remote
for skill in skills/*/; do
  if [ -d "$skill/.git" ]; then
    cd "$skill" && git fetch && git status
  fi
done
```

### Version Check Output
```
VERSION_STATUS.md
├── super-skill: V3.11 → V3.12 (update available)
├── darwin-evolution: V2.0 (up to date)
├── high-agency: V1.0 (up to date)
└── cognitive-modes: V1.0 (up to date)
```

## Step 2: Sub-Skill Upgrade

Upgrade all outdated skills:

```bash
# Upgrade Super-Skill
cd ~/.claude/skills/super-skill && git pull origin main

# Upgrade via npx skills
npx skills update --all --global

# Upgrade Context Hub
chub update
```

### Upgrade Priority Matrix

| Priority | Skill Type | Auto-Upgrade |
|----------|------------|--------------|
| **Critical** | Core skills (darwin-evolution, high-agency) | Yes |
| **High** | Phase skills (testing-automation, security-scanning) | Yes |
| **Medium** | Utility skills (api-patterns, data-patterns) | Ask |
| **Low** | Optional skills | Manual |

## Step 3: Best Practices Search

Search for latest best practices from trending sources:

### GitHub Trending Search

```bash
# Search trending AI agent repositories
gh search repos "AI agent" --sort stars --limit 10 --json name,description,stargazersCount

# Search trending LangChain patterns
gh search repos "langchain" --sort stars --limit 5

# Search trending MCP servers
gh search repos "mcp server" --sort stars --limit 5
```

### Best Practices Sources

| Source | Focus | Search Query |
|--------|-------|--------------|
| LangChain | Agent patterns | `langchain agent workflow` |
| AutoGen | Multi-agent | `autogen conversation` |
| CrewAI | Role-based | `crewAI task delegation` |
| MCP Protocol | Tool integration | `mcp server tool` |
| Anthropic | Skills guide | `anthropic skills best practices` |

### Search Result Processing

```markdown
BEST_PRACTICES_REPORT.md
├── New Patterns Found: 3
│   ├── Pattern 1: Chain-of-Thought with verification
│   ├── Pattern 2: Multi-agent consensus protocol
│   └── Pattern 3: Tool use optimization
├── Integration Priority: High/Medium/Low
└── Action Items: [specific integrations]
```

## Step 4: Pattern Integration

Integrate discovered best practices:

### Integration Workflow

```
1. Analyze pattern applicability
2. Check compatibility with existing skills
3. Create integration plan
4. Update affected SKILL.md files
5. Log to EVOLUTION.md
```

### Pattern Categories

| Category | Integration Method |
|----------|-------------------|
| **Workflow** | Update phase workflow in references/phases.md |
| **Skill** | Create new sub-skill or update existing |
| **Tool** | Add to MCP integration or scripts/ |
| **Knowledge** | Add to references/ or Context Hub |

## Step 5: Context Hub Sync

Sync Context Hub for latest documentation:

```bash
# Update Context Hub registry
chub update

# Cache frequently used docs
chub get claude-api --lang ts
chub get react-hooks --lang ts
chub get langchain-chains --lang py
```

### Context Hub Cache

```
~/.chub/cache/
├── claude-api.md
├── react-hooks.md
├── langchain-chains.md
└── ...
```

## Step 6: Evolution Learnings Sync

Sync learnings from previous project evolutions:

### Learning Sources

1. **PROJECT_RETROSPECTIVE.md** - From last project
2. **EVOLUTION.md** - Accumulated evolution history
3. **capsules.json** - Successful evolution capsules
4. **events.jsonl** - Evolution event log

### Sync Process

```bash
# Read last evolution capsule
cat assets/gep/capsules.json | jq '.[-1]'

# Check for pending evolutions
cat assets/gep/events.jsonl | jq 'select(.status == "pending")'
```

## Pre-Run Report

Generate summary report:

```markdown
# PRE-RUN UPGRADE REPORT
Date: 2026-03-14

## Version Status
- Super-Skill: V3.11 → V3.12 (upgraded)
- Sub-skills: 30 total, 2 updated

## Best Practices Discovered
- 3 new patterns from GitHub trending
- 2 MCP server patterns integrated
- 1 workflow optimization applied

## Context Hub Status
- Registry updated: ✅
- New docs cached: 5

## Evolution Learnings Applied
- Last capsule: optimize-debugging-workflow
- Pending evolutions: 0

## Readiness Status: ✅ READY
```

## Configuration

### Environment Variables

```bash
# Enable/disable pre-run upgrade
PRE_RUN_UPGRADE=true                    # Default: true
PRE_RUN_BEST_PRACTICES_SEARCH=true      # Default: true
PRE_RUN_CONTEXT_HUB_SYNC=true           # Default: true
PRE_RUN_EVOLUTION_SYNC=true             # Default: true

# Search limits
PRE_RUN_SEARCH_LIMIT=10                 # Max repos to search
PRE_RUN_PATTERN_LIMIT=5                 # Max patterns to integrate
```

### Skip Conditions

Pre-run upgrade is skipped when:
- `PRE_RUN_UPGRADE=false`
- Session is a continuation (not new session)
- `--skip-upgrade` flag passed

## Integration with Super-Skill

| Phase | Integration Point |
|-------|------------------|
| **Startup** | Execute before Phase 0 |
| **Phase 0** | Vision enhancement with new patterns |
| **Phase 12** | Feed into evolution system |

## Quick Reference

```
# Manual trigger
/super-skill --pre-run-upgrade

# Skip upgrade
/super-skill --skip-upgrade

# Force full upgrade
/super-skill --force-upgrade
```

## Version

**V1.0.0** - 2026-03-14
- Six-step upgrade sequence
- GitHub trending best practices search
- Context Hub synchronization
- Evolution learnings sync
- Pre-run report generation
