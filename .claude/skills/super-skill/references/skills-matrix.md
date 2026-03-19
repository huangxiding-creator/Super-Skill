# Super-Skill Integration Matrix

## 28+ Specialized Skills

### Core Development Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `darwin-evolution` | GEP Protocol self-evolution | Phase 12 |
| `multi-agent-orchestration` | LangGraph/AutoGen/CrewAI | Phase 8 |
| `advanced-reasoning` | CoT/ToT/GoT reasoning | All phases |
| `brainstorming` | Systematic exploration | Phase 0, 4, 5 |
| `systematic-debugging` | 4-phase debugging | Phase 8, 9 |
| `get-api-docs` | Context Hub curated docs | Phase 3, 5, 8 |

### Infrastructure Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `mcp-integration` | Model Context Protocol | Phase 5, 8 |
| `cicd-automation` | GitHub Actions patterns | Phase 7, 11 |
| `auto-git-create` | Repository automation | Phase 7, 11 |
| `security-scanning` | SAST/SCA/Secret scanning | Phase 9 |

### Development Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `testing-automation` | TDD/E2E/Mutation testing | Phase 8, 9 |
| `code-transformation` | AST-based refactoring | Phase 8 |
| `automated-documentation` | Docstring generation | Phase 8 |
| `error-recovery` | Retry/Circuit breaker | Phase 8 |
| `context-management` | Token budget management | All phases |

### Architecture Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `data-patterns` | SQL/NoSQL patterns | Phase 5, 8 |
| `api-patterns` | REST/GraphQL patterns | Phase 5, 8 |
| `state-management` | React Query/Zustand | Phase 5, 8 |
| `performance-optimization` | Frontend/Backend/DB | Phase 9, 10 |

### Operations Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `monitoring-observability` | Logging/Metrics/Tracing | Phase 11 |
| `feature-flags` | LaunchDarkly patterns | Phase 8, 11 |
| `file-storage` | S3/GCS/R2 patterns | Phase 5, 8 |

### User Experience Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `accessibility-a11y` | WCAG 2.1 compliance | Phase 8, 9 |
| `internationalization-i18n` | i18next/RTL support | Phase 8 |
| `real-time-websockets` | Socket.io/SSE | Phase 5, 8 |

### Specialized Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `search-indexing` | Elasticsearch/pgvector | Phase 5, 8 |
| `prompt-engineering` | CoT/Structured output | All phases |

### Discovery Skills

| Skill | Purpose | Phase Usage |
|-------|---------|-------------|
| `find-skills` | Skills ecosystem search | Phase 2b |

---

## Skill Invocation Patterns

### Automatic Invocation
Skills are automatically invoked based on phase requirements:
```
Phase 8: Autonomous Development
├── testing-automation (for TDD)
├── api-patterns (for API development)
├── data-patterns (for database work)
└── code-transformation (for refactoring)
```

### Manual Invocation
Skills can be manually invoked via skill system:
```bash
/skill-name [arguments]
```

### Conditional Invocation
Skills invoked based on detected needs:
```
IF real_time_required → real-time-websockets
IF search_required → search-indexing
IF i18n_required → internationalization-i18n
```

---

## External Skill Dependencies

### Required External Skills
| Skill | Source | Install Command |
|-------|--------|-----------------|
| `ai-native-vision` | Vercel Labs | `npx skills add ai-native-vision` |
| `feasibility-check` | Vercel Labs | `npx skills add feasibility-check` |
| `github-discovery` | Vercel Labs | `npx skills add github-discovery` |
| `continuous-learning-v2` | Vercel Labs | `npx skills add continuous-learning-v2` |
| `capability-evolver` | Vercel Labs | `npx skills add capability-evolver` |
| `skill-version-manager` | Vercel Labs | `npx skills add skill-version-manager` |

### Optional External Skills
| Skill | Source | Purpose |
|-------|--------|---------|
| `claude-mem` | thedotmack | Persistent memory |
| `self-evolving-skill` | Vercel Labs | Pattern learning |

---

## Skill Health Verification

### Startup Check
```bash
# Check all skill dependencies
python scripts/check_evolver.py

# Verify skill versions
node scripts/verify_skills.js
```

### Health Indicators
- ✅ All required skills installed
- ✅ All skills at latest version
- ✅ No deprecated skills in use
- ✅ Skill cache is valid

---

## Skill Development Guidelines

### Adding New Skills
1. Create `skills/<skill-name>/SKILL.md`
2. Add proper YAML frontmatter (name, description)
3. Implement skill logic
4. Add to integration matrix
5. Update phase mappings

### Skill Quality Checklist
- [ ] Clear name and description
- [ ] Single responsibility
- [ ] Documented usage patterns
- [ ] Test coverage (if applicable)
- [ ] Integration with phases defined
