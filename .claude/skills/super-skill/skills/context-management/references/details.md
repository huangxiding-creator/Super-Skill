# context-management — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Context Compression

### Intelligent Summarization

```typescript
interface CompressionConfig {
  maxSummaryLength: number;
  preserveCodeBlocks: boolean;
  preserveDecisions: boolean;
  preserveUserRequests: boolean;
}

class ContextCompressor {
  constructor(private config: CompressionConfig) {}

  async compress(content: string, type: ContentType): Promise<string> {
    switch (type) {
      case 'discussion':
        return this.compressDiscussion(content);
      case 'code':
        return this.compressCode(content);
      case 'decision':
        return this.compressDecision(content);
      default:
        return this.genericCompress(content);
    }
  }

  private async compressDiscussion(content: string): Promise<string> {
    const prompt = `
      Summarize the following discussion, preserving:
      - Key points and conclusions
      - Important questions raised
      - Decisions made
      - Action items

      Discussion:
      ${content}

      Summary (max ${this.config.maxSummaryLength} chars):
    `;

    return this.llmGenerate(prompt);
  }

  private compressCode(content: string): Promise<string> {
    if (this.config.preserveCodeBlocks) {
      // Keep code structure, compress comments
      return this.compressComments(content);
    }
    return this.extractSignature(content);
  }

  private extractSignature(code: string): string {
    // Extract function/class signatures without implementation
    const lines = code.split('\n');
    const signatures: string[] = [];

    for (const line of lines) {
      if (
        line.match(/^(function|class|interface|type|export|const|let|var)/) ||
        line.match(/^(def |class |async def )/)
      ) {
        signatures.push(line);
      }
    }

    return signatures.join('\n');
  }

  private async compressComments(code: string): Promise<string> {
    // Remove verbose comments, keep docstrings
    return code
      .replace(/\/\/.*$/gm, '') // Remove single-line comments
      .replace(/\/\*[\s\S]*?\*\//g, match => {
        // Keep if looks like docstring
        if (match.includes('@param') || match.includes('@return')) {
          return match;
        }
        return '';
      });
  }

  private async compressDecision(content: string): Promise<string> {
    if (this.config.preserveDecisions) {
      return content; // Don't compress decisions
    }

    // Extract just the decision outcome
    const prompt = `
      Extract the decision and rationale from:
      ${content}

      Format: DECISION: [outcome] | RATIONALE: [reason]
    `;

    return this.llmGenerate(prompt);
  }
}
```

### Checkpoint & Restore

```typescript
interface Checkpoint {
  id: string;
  timestamp: number;
  phase: number;
  contextSnapshot: string;
  metadata: {
    taskDescription: string;
    filesModified: string[];
    decisions: string[];
    nextSteps: string[];
  };
}

class CheckpointManager {
  private checkpoints: Checkpoint[] = [];

  async createCheckpoint(
    phase: number,
    context: string,
    metadata: Checkpoint['metadata']
  ): Promise<string> {
    const checkpoint: Checkpoint = {
      id: generateId(),
      timestamp: Date.now(),
      phase,
      contextSnapshot: await this.compress(context),
      metadata
    };

    this.checkpoints.push(checkpoint);
    return checkpoint.id;
  }

  async restore(checkpointId: string): Promise<Checkpoint | null> {
    return this.checkpoints.find(c => c.id === checkpointId) || null;
  }

  listCheckpoints(): Checkpoint[] {
    return [...this.checkpoints];
  }

  getLatestCheckpoint(): Checkpoint | null {
    return this.checkpoints[this.checkpoints.length - 1] || null;
  }

  private async compress(context: string): Promise<string> {
    // Create compressed snapshot
    return btoa(context.slice(0, 10000)); // Simplified
  }
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Claude Context Windows](https://docs.anthropic.com/claude/docs/context-windows)
- [Transformers Context Management](https://arxiv.org/abs/2009.06732)
- [Memory Systems in AI](https://arxiv.org/abs/2304.04829)
