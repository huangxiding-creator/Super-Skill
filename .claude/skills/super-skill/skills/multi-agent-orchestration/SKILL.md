---
name: multi-agent-orchestration
description: Multi-agent orchestration system inspired by LangGraph, AutoGen, and CrewAI best practices. Provides graph-based workflow control, conversation-driven collaboration, and role-based team coordination for complex AI-native development.
tags: [multi-agent, orchestration, langgraph, autogen, crewai, collaboration]
version: 1.0.0
source: Inspired by langchain-ai/langgraph, microsoft/autogen, crewAIInc/crewAI
integrated-with: super-skill v3.6+
---

# Multi-Agent Orchestration Skill

This skill provides production-grade multi-agent orchestration capabilities, combining the best practices from leading AI agent frameworks: **LangGraph** (graph-based workflows), **AutoGen** (conversation-driven collaboration), and **CrewAI** (role-based teams).

## Core Concepts

### Three Paradigms Integration

```
┌─────────────────────────────────────────────────────────────┐
│                 MULTI-AGENT ORCHESTRATION                    │
├─────────────────┬───────────────────┬───────────────────────┤
│   LangGraph     │     AutoGen       │      CrewAI           │
│  (Graph/DAG)    │ (Conversation)    │   (Role-Based)        │
├─────────────────┼───────────────────┼───────────────────────┤
│ • State Machine │ • Async Messaging │ • Crew-Role-Task      │
│ • Checkpointing │ • Group Chat      │ • Declarative Config  │
│ • Human-in-Loop │ • Hierarchical    │ • 700+ Connectors     │
│ • Observability │ • Event-Driven    │ • High Performance    │
└─────────────────┴───────────────────┴───────────────────────┘
```

## Architecture Patterns

### Pattern 1: Graph-Based Workflow (LangGraph Style)

```yaml
# For complex, stateful workflows
workflow:
  name: feature-development
  type: dag

  nodes:
    - id: requirements
      agent: requirements-analyst
      next: [design, feasibility]

    - id: feasibility
      agent: feasibility-checker
      condition:
        pass: [design]
        fail: [requirements]

    - id: design
      agent: architect
      next: [implementation]

    - id: implementation
      agent: developer
      parallel: [frontend-dev, backend-dev]
      next: [integration]

    - id: integration
      agent: integrator
      next: [testing]

    - id: testing
      agent: qa-engineer
      condition:
        pass: [deployment]
        fail: [implementation]

    - id: deployment
      agent: devops-engineer

  checkpointing: true
  human_in_loop: [requirements, deployment]
```

### Pattern 2: Conversation-Driven (AutoGen Style)

```yaml
# For collaborative problem-solving
conversation:
  name: code-review-session
  type: group-chat

  agents:
    - name: reviewer
      role: Senior code reviewer
      system_prompt: |
        You are a meticulous code reviewer. Focus on:
        - Code quality and maintainability
        - Security vulnerabilities
        - Performance issues

    - name: author
      role: Original developer
      system_prompt: |
        You are the code author. Explain your design decisions
        and be open to feedback.

    - name: architect
      role: System architect
      system_prompt: |
        You ensure code aligns with system architecture.
        Focus on patterns and scalability.

  moderator: reviewer
  max_rounds: 10
  termination:
    condition: consensus
    keywords: [approved, rejected]
```

### Pattern 3: Role-Based Crew (CrewAI Style)

```yaml
# For structured team workflows
crew:
  name: development-team

  agents:
    - role: Project Manager
      goal: Ensure project success and timeline adherence
      backstory: |
        Experienced PM with 10+ years in software development.
        Skilled in agile methodologies and risk management.
      tools: [jira, confluence, slack]

    - role: Software Architect
      goal: Design robust, scalable systems
      backstory: |
        Senior architect specializing in microservices and
        cloud-native applications.
      tools: [draw-io, architecture-docs]

    - role: Senior Developer
      goal: Implement high-quality code
      backstory: |
        Full-stack developer with expertise in TypeScript,
        React, Node.js, and PostgreSQL.
      tools: [vscode, git, testing-framework]

    - role: QA Engineer
      goal: Ensure product quality
      backstory: |
        QA specialist with focus on test automation and
        performance testing.
      tools: [playwright, jest, lighthouse]

  tasks:
    - description: Analyze requirements
      assigned_to: Project Manager
      expected_output: REQUIREMENTS.md

    - description: Design system architecture
      assigned_to: Software Architect
      expected_output: ARCHITECTURE.md

    - description: Implement features
      assigned_to: Senior Developer
      expected_output: source_code

    - description: Test and validate
      assigned_to: QA Engineer
      expected_output: QA_REPORT.md

  process: sequential  # or hierarchical
```

## Implementation

### Agent Configuration Template

```typescript
interface AgentConfig {
  // Identity
  name: string;
  role: string;
  description: string;

  // Capabilities
  skills: string[];
  tools: ToolConfig[];
  mcp_servers?: string[];

  // Behavior
  system_prompt: string;
  temperature?: number;
  max_tokens?: number;

  // Collaboration
  communication_style: 'proactive' | 'reactive' | 'collaborative';
  decision_authority: 'full' | 'recommend' | 'execute';

  // Constraints
  allowed_actions: string[];
  forbidden_actions: string[];
  escalation_triggers: string[];
}

interface WorkflowConfig {
  // Structure
  nodes: NodeConfig[];
  edges: EdgeConfig[];

  // State
  state_schema: Record<string, any>;
  checkpoint_enabled: boolean;

  // Control
  human_in_loop: string[];  // Node IDs requiring human approval
  timeout_seconds: number;
  retry_policy: RetryPolicy;

  // Observability
  tracing_enabled: boolean;
  logging_level: 'debug' | 'info' | 'warn' | 'error';
}
```

### Orchestration Engine

```python
class MultiAgentOrchestrator:
    """
    Combines LangGraph, AutoGen, and CrewAI patterns.
    """

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.state = StateManager(config.state_schema)
        self.checkpointer = Checkpointer() if config.checkpoint_enabled else None
        self.agents = AgentRegistry()
        self.event_bus = EventBus()

    async def execute(self, initial_input: dict) -> dict:
        """Execute the workflow with checkpointing support."""

        # Initialize state
        self.state.initialize(initial_input)

        # Get execution order (topological sort for DAG)
        execution_order = self._get_execution_order()

        for node_id in execution_order:
            node = self.config.get_node(node_id)

            # Check conditions
            if not self._evaluate_conditions(node):
                continue

            # Human-in-loop check
            if node_id in self.config.human_in_loop:
                await self._request_human_approval(node_id)

            # Execute node
            agent = self.agents.get(node.agent)
            result = await agent.execute(self.state)

            # Update state
            self.state.update(node_id, result)

            # Checkpoint
            if self.checkpointer:
                await self.checkpointer.save(node_id, self.state)

            # Emit event
            self.event_bus.emit('node_completed', {
                'node_id': node_id,
                'result': result
            })

        return self.state.finalize()

    async def execute_parallel(self, node_ids: list[str]) -> dict:
        """Execute multiple nodes in parallel."""
        tasks = [
            self.agents.get(self.config.get_node(nid).agent).execute(self.state)
            for nid in node_ids
        ]
        results = await asyncio.gather(*tasks)
        return dict(zip(node_ids, results))

    def rollback(self, checkpoint_id: str):
        """Rollback to a previous checkpoint."""
        if self.checkpointer:
            self.state = self.checkpointer.load(checkpoint_id)
```

### Conversation Manager (AutoGen Style)

```python
class ConversationManager:
    """
    Manages multi-agent conversations with moderation.
    """

    def __init__(self, agents: list[AgentConfig], config: dict):
        self.agents = {a.name: a for a in agents}
        self.moderator = config.get('moderator')
        self.max_rounds = config.get('max_rounds', 10)
        self.termination = config.get('termination', {})
        self.history = []

    async def run_conversation(self, initial_message: str) -> str:
        """Run a multi-round conversation."""

        current_speaker = self.moderator or list(self.agents.keys())[0]
        message = initial_message

        for round_num in range(self.max_rounds):
            agent = self.agents[current_speaker]

            # Build context with conversation history
            context = self._build_context(message)

            # Get agent response
            response = await agent.generate_response(context)

            # Record in history
            self.history.append({
                'round': round_num,
                'speaker': current_speaker,
                'message': response
            })

            # Check termination
            if self._should_terminate(response):
                return response

            # Select next speaker
            current_speaker = self._select_next_speaker(response)
            message = response

        return self._summarize_conversation()

    def _should_terminate(self, response: str) -> bool:
        """Check if conversation should terminate."""
        if 'keywords' in self.termination:
            return any(kw in response.lower() for kw in self.termination['keywords'])
        if self.termination.get('condition') == 'consensus':
            return self._check_consensus()
        return False
```

## Integration with Super-Skill

### Phase Integration

```
Phase 0-1: Single Agent (Visionary + Feasibility)
Phase 2-3: Research Agents (GitHub Discovery + Knowledge Base)
Phase 4-5: Design Agents (Requirements + Architecture)
Phase 6-7: Planning Agents (WBS + Initialization)
Phase 8: Development Crew (Multiple parallel agents)
Phase 9: QA Team (Testing agents collaboration)
Phase 10: Optimization Loop (Self-improving agents)
Phase 11-12: Delivery Agents (Deployment + Summary)
```

### Recommended Agent Teams

#### Development Team (Phase 8)
```yaml
crew:
  name: development-crew
  agents:
    - frontend-developer
    - backend-developer
    - database-specialist
    - api-designer
    - test-engineer
  coordinator: tech-lead
  communication: async-messaging
```

#### QA Team (Phase 9)
```yaml
crew:
  name: qa-crew
  agents:
    - code-reviewer
    - security-analyst
    - performance-tester
    - e2e-tester
  coordinator: qa-lead
  communication: group-chat
```

## Best Practices

### 1. Agent Design
- Single responsibility per agent
- Clear input/output contracts
- Explicit tool permissions
- Timeout and retry handling

### 2. Workflow Design
- DAG for complex dependencies
- Checkpointing for long-running tasks
- Human-in-loop for critical decisions
- Parallel execution for independent tasks

### 3. Communication
- Structured message formats
- Event-driven updates
- Conflict resolution protocols
- Consensus mechanisms

### 4. Observability
- Distributed tracing
- State snapshots
- Performance metrics
- Error tracking

## Checklist

### Before Orchestration
- [ ] Agent roles clearly defined
- [ ] Workflow graph validated (no cycles in DAG)
- [ ] State schema documented
- [ ] Checkpoint strategy defined
- [ ] Human approval points identified

### During Execution
- [ ] State consistency maintained
- [ ] Checkpoints saved at key points
- [ ] Events emitted for observability
- [ ] Errors handled gracefully
- [ ] Timeouts respected

### After Completion
- [ ] Final state captured
- [ ] Results aggregated
- [ ] Metrics collected
- [ ] Learnings extracted

## Deliverables

- Multi-agent workflow configuration
- Agent team definitions
- Orchestration logs
- Collaboration artifacts

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.6 |

---

## References

- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based agent orchestration
- [AutoGen](https://github.com/microsoft/autogen) - Multi-agent conversation framework
- [CrewAI](https://github.com/crewAIInc/crewAI) - Role-based agent teams
