---
name: get-api-docs
description: Curated API documentation fetcher using Context Hub (chub). TRIGGER when users need library/framework API docs, SDK references, or up-to-date documentation. Capabilities: (1) Search curated docs from chub registry, (2) Fetch versioned API docs by ID, (3) Add persistent annotations, (4) Submit feedback to improve docs. Core workflow: chub search → chub get → annotate → feedback. Integrates Andrew Ng's Context Hub for reliable, AI-optimized documentation.
---

# Get API Docs - Context Hub Integration

## Overview

Fetches curated, versioned API documentation from [Context Hub](https://github.com/andrewyng/context-hub) - a registry of AI-optimized documentation maintained by the community.

## Prerequisites

```bash
# Install Context Hub CLI
pip install chub

# Or with npm
npm install -g @context-hub/cli
```

## Commands

### Search Documentation

```bash
# Search for library/framework docs
chub search "react hooks"
chub search "langchain"
chub search "next.js app router"

# Output: List of matching docs with IDs
```

### Fetch Documentation

```bash
# Get docs by ID with language preference
chub get openai-chat-completions --lang py
chub get react-use-effect --lang ts
chub get langchain-chains --lang py

# Output: Formatted documentation content
```

### Annotate (Persistent Notes)

```bash
# Add persistent local notes to a doc
chub annotate openai-chat-completions "Remember to handle streaming responses with try/catch"

# Annotations persist across sessions
chub annotate react-use-effect "Cleanup function runs on unmount and dependency changes"
```

### Feedback (Improve Docs)

```bash
# Upvote helpful docs
chub feedback openai-chat-completions up

# Downvote outdated/inaccurate docs
chub feedback react-use-effect down

# Feedback improves global registry quality
```

### Update Registry

```bash
# Refresh cached registry for latest docs
chub update
```

## Usage Patterns

### Phase 3: Knowledge Base Integration

```markdown
# When building knowledge base for a project:

1. Search for relevant library docs:
   chub search "<library-name>"

2. Fetch specific API docs:
   chub get <doc-id> --lang <language>

3. Annotate with project-specific notes:
   chub annotate <doc-id> "<project-context-note>"

4. Add to KNOWLEDGE_BASE/ directory
```

### Phase 8: Development Reference

```markdown
# During development, quickly fetch API reference:

1. Search: chub search "react useState"
2. Fetch: chub get react-use-state --lang ts
3. Apply pattern in code
4. Annotate with learnings for future sessions
```

## Self-Improving Loop

```
┌─────────────┐
│   Search    │
└──────┬──────┘
       ▼
┌─────────────┐
│    Get      │──────► Apply in code
└──────┬──────┘
       ▼
┌─────────────┐
│  Annotate   │──────► Persist learnings
└──────┬──────┘
       ▼
┌─────────────┐
│  Feedback   │──────► Improve registry
└─────────────┘
```

Annotations persist across sessions and improve future doc retrieval accuracy.

## Configuration

### Environment Variables

```bash
# Cache directory (default: ~/.chub/cache)
CHUB_CACHE_DIR=~/.chub/cache

# Registry URL (default: official registry)
CHUB_REGISTRY_URL=https://registry.chub.ai
```

### Cache Management

```bash
# View cache status
chub cache status

# Clear cache
chub cache clear

# Cache location
~/.chub/cache/
```

## Integration with Super-Skill

| Phase | Usage |
|-------|-------|
| Phase 3 | Build knowledge base with library docs |
| Phase 5 | Fetch architecture patterns and API design |
| Phase 8 | Quick reference during development |
| Phase 12 | Annotate learnings for future projects |

## Example Session

```bash
# Building a Next.js project
$ chub search "next.js server actions"
Found: nextjs-server-actions, nextjs-form-handling, nextjs-mutations

$ chub get nextjs-server-actions --lang ts
# Returns: Server Actions API docs with TypeScript examples

$ chub annotate nextjs-server-actions "Use for form submissions, wrap in try/catch for error handling"

# Later sessions will include this annotation
```

## Version

**V1.0.0** - 2026-03-14
- Initial integration with Context Hub
- Search, get, annotate, feedback workflow
- Persistent local annotations
- Self-improving documentation loop
