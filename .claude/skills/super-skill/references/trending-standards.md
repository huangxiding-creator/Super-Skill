# GitHub Trending Standards Integration (2026)

## Sources

| Project | Stars | Integration |
|---------|-------|-------------|
| [LangChain](https://github.com/langchain-ai/langchain) | 122K+ | Chain-based workflows |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 24K+ | Graph-based orchestration |
| [AutoGen](https://github.com/microsoft/autogen) | 52K+ | Multi-agent conversations |
| [CrewAI](https://github.com/crewAIInc/crewAI) | 30K+ | Role-based task delegation |
| [MCP Protocol](https://github.com/modelcontextprotocol) | Official | Tool integration standard |
| [Anthropic Skills](https://github.com/anthropics/skills) | Official | Skill building guidelines |
| [Context Hub](https://github.com/andrewyng/context-hub) | Andrew Ng | Curated API docs |
| [Awesome AI Agents 2026](https://github.com/caramaschiHG/awesome-ai-agents-2026) | Community | 300+ resources |

---

## 0. AI-Assisted Engineering Best Practices (Addy Osmani 2026)

> "Treat the LLM as a powerful pair programmer that requires clear direction, context and oversight."

### 10 Core Principles

| # | Principle | Key Insight |
|---|-----------|-------------|
| 1 | **Specs Before Code** | "Waterfall in 15 minutes" - rapid structured planning |
| 2 | **Iterative Chunks** | Feed LLM manageable tasks, not whole codebase |
| 3 | **Context Packing** | Show relevant code, docs, constraints |
| 4 | **Model Selection** | Pick right tool for each task |
| 5 | **Human in Loop** | Verify, test, review everything |
| 6 | **Commit Often** | Commits are save points |
| 7 | **Customize with Rules** | CLAUDE.md, style guides, examples |
| 8 | **Automation Force Multiplier** | CI/CD, linters, review bots |
| 9 | **Continuous Learning** | AI amplifies existing skills |
| 10 | **Accountable Engineer** | Human remains the director |

### The Waterfall-in-15-Minutes Pattern

```markdown
1. Brainstorm specification with AI iteratively
2. Ask questions until requirements fleshed out
3. Compile into spec.md (requirements, architecture, data models)
4. Generate project plan with bite-sized tasks
5. Iterate on plan until coherent
6. Only then proceed to coding
```

### Context Packing Checklist

```
- High-level goals and invariants
- Examples of good solutions
- Warnings about approaches to avoid
- Performance constraints
- Known edge cases
```

### Never Commit Code You Can't Explain

If AI generates something convoluted:
1. Ask AI to add comments explaining it
2. Rewrite in simpler terms
3. Don't commit until understood

**See**: [references/best-practices-2026.md](best-practices-2026.md) for full details.

---

## 1. AI Agent Framework Patterns

### LangGraph Integration (Graph-Based Orchestration)

```python
# LangGraph pattern for phase orchestration
from langgraph.graph import StateGraph, END

class SuperSkillState(TypedDict):
    phase: int
    artifacts: dict
    context: dict

def build_super_skill_graph():
    graph = StateGraph(SuperSkillState)

    # Add phase nodes
    graph.add_node("phase_0", visionary_elevation)
    graph.add_node("phase_1", feasibility_analysis)
    graph.add_node("phase_2", github_discovery)
    # ... more phases

    # Add conditional edges
    graph.add_conditional_edges(
        "phase_1",
        should_proceed,
        {True: "phase_2", False: END}
    )

    return graph.compile()
```

**Key Patterns:**
- State persistence across phases
- Conditional transitions with gate checks
- Checkpoint/restore capability
- Streaming outputs

### AutoGen Integration (Multi-Agent Conversations)

```python
# AutoGen pattern for multi-agent development
from autogen import AssistantAgent, UserProxyAgent

# Development crew
architect = AssistantAgent("architect", system_message=ARCHITECT_PROMPT)
developer = AssistantAgent("developer", system_message=DEVELOPER_PROMPT)
reviewer = AssistantAgent("reviewer", system_message=REVIEWER_PROMPT)

# Group chat for collaboration
groupchat = GroupChat(
    agents=[architect, developer, reviewer],
    messages=[],
    max_round=50
)
```

**Key Patterns:**
- Role-based agent definitions
- Group chat for collaboration
- Human-in-the-loop checkpoints
- Conversation-driven workflow

### CrewAI Integration (Role-Based Task Delegation)

```python
# CrewAI pattern for task delegation
from crewai import Agent, Task, Crew

# Define agents with roles
dev_agent = Agent(
    role="Senior Developer",
    goal="Write clean, tested code",
    backstory="Expert in TDD and clean architecture",
    tools=[code_editor, test_runner]
)

# Define tasks
tasks = [
    Task(description="Implement feature X", agent=dev_agent),
    Task(description="Write tests for feature X", agent=dev_agent),
]

# Execute crew
crew = Crew(agents=[dev_agent], tasks=tasks)
result = crew.kickoff()
```

**Key Patterns:**
- Role-based agent definition
- Goal-oriented task assignment
- Tool integration per agent
- Sequential/parallel execution

---

## 2. MCP Protocol Standards (2026)

### Server Configuration

```json
// mcp-servers.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Tool Discovery Pattern

```python
# MCP tool discovery and invocation
async def discover_mcp_tools():
    """Discover available MCP tools"""
    tools = await mcp_client.list_tools()
    return {
        tool.name: {
            "description": tool.description,
            "parameters": tool.inputSchema
        }
        for tool in tools
    }

async def invoke_mcp_tool(tool_name: str, arguments: dict):
    """Invoke MCP tool with arguments"""
    result = await mcp_client.call_tool(tool_name, arguments)
    return result.content
```

### Resource Pattern

```python
# MCP resource access
async def read_mcp_resource(uri: str):
    """Read resource from MCP server"""
    resource = await mcp_client.read_resource(uri)
    return resource.contents
```

---

## 3. Anthropic Skills Best Practices (2026)

### Skill Structure (15-30 Minute Build)

```
skill-name/
├── SKILL.md          # Required: name + description in YAML frontmatter
├── scripts/          # Optional: Executable code
├── references/       # Optional: Documentation to load as needed
└── assets/           # Optional: Files used in output
```

### Progressive Disclosure Pattern

```markdown
---
name: example-skill
description: Clear trigger-focused description
---

# Core Instructions
[Essential instructions only - keep under 500 lines]

## When to Load References
- For X: See [references/X.md](references/X.md)
- For Y: See [references/Y.md](references/Y.md)
```

### Metadata Best Practices

```yaml
---
name: skill-name
description: |
  Single-line description with clear triggers.
  Use when: (1) condition A, (2) condition B, (3) condition C.
  Capabilities: X, Y, Z.
---
```

### Hook Integration Pattern

```json
// settings.json hooks
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["echo 'Running bash command'"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": ["npm run format"]
      }
    ]
  }
}
```

---

## 4. Production Deployment Patterns

### Observability Stack

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"

  jaeger:
    image: jaegertracing/all-in-one
    ports:
      - "16686:16686"
```

### Metrics Collection

```python
# OpenTelemetry integration
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("phase_execution")
def execute_phase(phase: int):
    with tracer.start_as_current_span(f"phase_{phase}"):
        # Phase logic
        pass
```

### Health Checks

```python
# Health check endpoints
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    checks = {
        "database": await check_database(),
        "mcp_servers": await check_mcp_servers(),
        "memory": await check_memory()
    }
    return {"status": "ready", "checks": checks}
```

---

## 5. Context Management Patterns

### Token Budget Management

```python
class ContextManager:
    def __init__(self, max_tokens: int = 200000):
        self.max_tokens = max_tokens
        self.priority_queue = []

    def add_content(self, content: str, priority: int):
        tokens = count_tokens(content)
        self.priority_queue.append((priority, tokens, content))
        self._evict_if_needed()

    def _evict_if_needed(self):
        while self.current_tokens > self.max_tokens * 0.8:
            # Evict lowest priority content
            self.priority_queue.sort(key=lambda x: x[0])
            self.priority_queue.pop(0)
```

### Memory Persistence

```python
# ChromaDB for semantic memory
import chromadb

client = chromadb.Client()
collection = client.create_collection("skill_memory")

def store_memory(content: str, metadata: dict):
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[generate_id()]
    )

def retrieve_memories(query: str, n: int = 5):
    return collection.query(
        query_texts=[query],
        n_results=n
    )
```

---

## 6. Quality Assurance Patterns

### Automated Testing

```yaml
# GitHub Actions testing workflow
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
```

### Mutation Testing

```bash
# Stryker mutation testing
npx stryker run

# Target: 80%+ mutation score
```

### Security Scanning

```yaml
# Security workflow
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
```

---

## 7. Integration Matrix

| Feature | LangGraph | AutoGen | CrewAI | MCP | Super-Skill |
|---------|-----------|---------|--------|-----|-------------|
| Graph workflows | ✅ | ❌ | ❌ | ❌ | ✅ |
| Multi-agent chat | ❌ | ✅ | ❌ | ❌ | ✅ |
| Role-based tasks | ❌ | ❌ | ✅ | ❌ | ✅ |
| Tool integration | ✅ | ✅ | ✅ | ✅ | ✅ |
| Memory persistence | ✅ | ✅ | ❌ | ❌ | ✅ |
| Streaming | ✅ | ✅ | ❌ | ❌ | ✅ |
| Checkpointing | ✅ | ✅ | ❌ | ❌ | ✅ |

---

## References

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph How-Tos](https://langchain-ai.github.io/langgraph/)
- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Anthropic Skills Guide](https://resources.anthropic.com/)
