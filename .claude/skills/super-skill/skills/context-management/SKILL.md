---
name: context-management
description: Context window management, memory persistence, and intelligent context compression for long-running AI sessions. Optimizes token usage while preserving critical information.
tags: [context, memory, compression, persistence, tokens]
version: 1.0.0
source: Based on Claude Code context patterns, claude-mem integration
integrated-with: super-skill v3.7+
---
# Context Management Skill

This skill provides comprehensive context window management, memory persistence, and intelligent compression strategies for long-running AI sessions.

## Context Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTEXT MANAGEMENT SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SHORT-TERM MEMORY (Session)                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Active conversation    • Current task    • Recent Q&A │    │
│  │ • ~128K tokens max       • Rolling window  • Priority   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  WORKING MEMORY (Phase)                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Phase context          • Decisions       • Artifacts  │    │
│  │ • Cross-references       • Dependencies    • State      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LONG-TERM MEMORY (Persistent)                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Project knowledge      • Patterns        • Learnings  │    │
│  │ • User preferences       • Conventions      • History   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  COMPRESSION LAYER                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Summarization          • Extraction      • Pruning    │    │
│  │ • Semantic clustering    • Deduplication   • Archival   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Token Budget Management

### Context Allocation

```typescript
interface ContextBudget {
  // Total context window (e.g., 200K for Claude)
  total: number;

  // Reserve for response generation
  responseReserve: number;

  // System prompts and instructions
  systemOverhead: number;

  // Available for content
  available: number;
}

const DEFAULT_BUDGET: ContextBudget = {
  total: 200000,
  responseReserve: 16000,
  systemOverhead: 4000,
  get available() {
    return this.total - this.responseReserve - this.systemOverhead;
  }
};

// Warning thresholds
const THRESHOLDS = {
  comfortable: 0.5,  // 50% remaining - safe
  caution: 0.3,      // 30% remaining - start planning
  critical: 0.2,     // 20% remaining - must compress
  emergency: 0.1     // 10% remaining - immediate action
};
```

### Priority-Based Retention

```typescript
enum ContentPriority {
  CRITICAL = 1,    // Never compress (active task, user request)
  HIGH = 2,        // Retain as long as possible (decisions, code)
  MEDIUM = 3,      // Compress if needed (discussion, exploration)
  LOW = 4,         // Archive first (small talk, tangents)
  DISPOSABLE = 5   // Can be dropped (redundant, superseded)
}

interface ContextItem {
  id: string;
  content: string;
  tokens: number;
  priority: ContentPriority;
  timestamp: number;
  references: string[];
  metadata: {
    type: 'decision' | 'code' | 'discussion' | 'output' | 'reference';
    phase?: number;
    superseded?: boolean;
  };
}

class ContextManager {
  private items: Map<string, ContextItem> = new Map();
  private budget: ContextBudget;

  constructor(budget: ContextBudget = DEFAULT_BUDGET) {
    this.budget = budget;
  }

  getCurrentUsage(): number {
    return Array.from(this.items.values())
      .reduce((sum, item) => sum + item.tokens, 0);
  }

  getRemaining(): number {
    return this.budget.available - this.getCurrentUsage();
  }

  getStatus(): ContextStatus {
    const remaining = this.getRemaining();
    const ratio = remaining / this.budget.available;

    if (ratio > THRESHOLDS.comfortable) return 'COMFORTABLE';
    if (ratio > THRESHOLDS.caution) return 'CAUTION';
    if (ratio > THRESHOLDS.critical) return 'CRITICAL';
    return 'EMERGENCY';
  }

  addItem(item: ContextItem): void {
    this.items.set(item.id, item);
    this.checkAndCompress();
  }

  private checkAndCompress(): void {
    const status = this.getStatus();

    if (status === 'EMERGENCY') {
      this.emergencyCompression();
    } else if (status === 'CRITICAL') {
      this.progressiveCompression();
    }
  }

  private emergencyCompression(): void {
    // Remove all disposable items
    for (const [id, item] of this.items) {
      if (item.priority === ContentPriority.DISPOSABLE) {
        this.items.delete(id);
      }
    }

    // Then compress low priority
    this.compressByPriority(ContentPriority.LOW);
  }

  private progressiveCompression(): void {
    // Start with lowest priority
    this.compressByPriority(ContentPriority.LOW);

    // If still critical, move to medium
    if (this.getStatus() === 'CRITICAL') {
      this.compressByPriority(ContentPriority.MEDIUM);
    }
  }

  private compressByPriority(priority: ContentPriority): void {
    const toCompress = Array.from(this.items.values())
      .filter(item => item.priority === priority)
      .sort((a, b) => a.timestamp - b.timestamp); // Oldest first

    for (const item of toCompress) {
      const summary = this.summarize(item);
      this.items.set(item.id, {
        ...item,
        content: summary,
        tokens: this.estimateTokens(summary),
        priority: item.priority + 1 // Lower priority after compression
      });
    }
  }

  private summarize(item: ContextItem): string {
    // Generate concise summary preserving key information
    return `[${item.metadata.type}] ${item.content.slice(0, 200)}...`;
  }

  private estimateTokens(text: string): number {
    // Rough estimate: ~4 characters per token
    return Math.ceil(text.length / 4);
  }
}
```

## Memory Persistence

### Session Memory

```typescript
interface SessionMemory {
  sessionId: string;
  projectId: string;
  startTime: number;

  // Core memories
  memories: Memory[];

  // Cross-references
  codebase: CodebaseIndex;
  decisions: Decision[];

  // User context
  userPreferences: Record<string, any>;
  conventions: string[];
}

interface Memory {
  id: string;
  content: string;
  type: MemoryType;
  importance: number;  // 0-1
  accessCount: number;
  lastAccessed: number;
  created: number;
  expires?: number;
}

enum MemoryType {
  EPISODIC = 'episodic',   // Events and experiences
  SEMANTIC = 'semantic',   // Facts and concepts
  PROCEDURAL = 'procedural', // How to do things
  SPATIAL = 'spatial',     // Codebase structure
  SOCIAL = 'social'        // User preferences, team context
}

class PersistentMemory {
  private storage: StorageAdapter;

  async save(memory: SessionMemory): Promise<void> {
    await this.storage.set(
      `session:${memory.sessionId}`,
      JSON.stringify(memory),
      { ttl: 7 * 24 * 60 * 60 * 1000 } // 7 days
    );
  }

  async load(sessionId: string): Promise<SessionMemory | null> {
    const data = await this.storage.get(`session:${sessionId}`);
    return data ? JSON.parse(data) : null;
  }

  async addMemory(
    sessionId: string,
    content: string,
    type: MemoryType,
    importance: number = 0.5
  ): Promise<void> {
    const memory = await this.load(sessionId);
    if (!memory) return;

    memory.memories.push({
      id: generateId(),
      content,
      type,
      importance,
      accessCount: 0,
      lastAccessed: Date.now(),
      created: Date.now()
    });

    await this.save(memory);
  }

  async recall(
    sessionId: string,
    query: string,
    limit: number = 5
  ): Promise<Memory[]> {
    const memory = await this.load(sessionId);
    if (!memory) return [];

    // Score memories by relevance
    const scored = memory.memories.map(m => ({
      memory: m,
      score: this.calculateRelevance(m, query)
    }));

    // Sort by relevance and return top
    return scored
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(s => {
        s.memory.accessCount++;
        s.memory.lastAccessed = Date.now();
        return s.memory;
      });
  }

  private calculateRelevance(memory: Memory, query: string): number {
    // Simple relevance scoring
    const queryTerms = query.toLowerCase().split(/\s+/);
    const content = memory.content.toLowerCase();

    let matches = 0;
    for (const term of queryTerms) {
      if (content.includes(term)) matches++;
    }

    const recency = (Date.now() - memory.lastAccessed) / (24 * 60 * 60 * 1000);
    const importanceWeight = memory.importance * 0.3;
    const frequencyWeight = Math.min(memory.accessCount / 10, 0.2);

    return (
      (matches / queryTerms.length) * 0.5 +
      importanceWeight +
      frequencyWeight -
      recency * 0.01
    );
  }
}
```

## Integration with Super-Skill

### Phase Context Management

```typescript
class PhaseContextManager {
  private contextManager: ContextManager;
  private memory: PersistentMemory;
  private checkpoints: CheckpointManager;

  async startPhase(phase: number, task: string): Promise<void> {
    // Load relevant context from memory
    const relevantMemories = await this.memory.recall(
      this.sessionId,
      task,
      10
    );

    // Add phase context
    this.contextManager.addItem({
      id: `phase-${phase}-start`,
      content: `Starting Phase ${phase}: ${task}`,
      tokens: 20,
      priority: ContentPriority.CRITICAL,
      timestamp: Date.now(),
      references: [],
      metadata: { type: 'decision', phase }
    });

    // Create checkpoint
    await this.checkpoints.createCheckpoint(phase, '', {
      taskDescription: task,
      filesModified: [],
      decisions: [],
      nextSteps: []
    });
  }

  async endPhase(phase: number, outputs: string[]): Promise<void> {
    // Save phase learnings to memory
    for (const output of outputs) {
      await this.memory.addMemory(
        this.sessionId,
        output,
        MemoryType.EPISODIC,
        0.7
      );
    }

    // Compress phase context if needed
    const status = this.contextManager.getStatus();
    if (status !== 'COMFORTABLE') {
      await this.compressPhaseContext(phase);
    }
  }

  private async compressPhaseContext(phase: number): Promise<void> {
    // Archive completed phase context
    const compressor = new ContextCompressor({
      maxSummaryLength: 500,
      preserveCodeBlocks: false,
      preserveDecisions: true,
      preserveUserRequests: true
    });

    // ... compression logic
  }
}
```

## Best Practices

### 1. Token Budgeting
- Monitor context usage continuously
- Compress before reaching critical threshold
- Reserve space for response generation
- Use priority-based retention

### 2. Memory Management
- Persist important information
- Use semantic clustering for recall
- Implement forgetting curves
- Regular memory consolidation

### 3. Compression Strategy
- Never compress active task context
- Preserve decisions and rationale
- Maintain code signatures
- Keep user-facing content readable

### 4. Checkpoint Strategy
- Checkpoint before major operations
- Checkpoint at phase boundaries
- Keep recent checkpoints accessible
- Archive old checkpoints

## Checklist

### Session Start
- [ ] Context budget configured
- [ ] Memory loaded from persistence
- [ ] Checkpoint manager initialized
- [ ] Compression thresholds set

### During Session
- [ ] Context usage monitored
- [ ] Compression triggered when needed
- [ ] Checkpoints created at milestones
- [ ] Memory updated with learnings

### Session End
- [ ] Final checkpoint created
- [ ] Memory persisted
- [ ] Context archived
- [ ] Statistics logged

## Deliverables

- Context management configuration
- Memory persistence layer
- Compression strategies
- Checkpoint system

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `Context Compression`, `Version History`, `References`.
