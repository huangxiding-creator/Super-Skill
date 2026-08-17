# real-time-websockets — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Real-Time Data Synchronization

### Optimistic Updates

```typescript
class RealtimeSync {
  private socket: Socket;
  private pendingUpdates: Map<string, PendingUpdate> = new Map();

  async updateDocument(documentId: string, changes: DocumentChanges) {
    const updateId = generateId();

    // Store pending update
    this.pendingUpdates.set(updateId, {
      documentId,
      changes,
      timestamp: Date.now()
    });

    // Optimistically apply changes locally
    applyChangesLocally(documentId, changes);

    try {
      // Send to server
      this.socket.emit('document:update', {
        updateId,
        documentId,
        changes
      });

      // Wait for acknowledgment
      await this.waitForAck(updateId);

    } catch (error) {
      // Rollback on failure
      rollbackChanges(documentId, changes);
      throw error;
    } finally {
      this.pendingUpdates.delete(updateId);
    }
  }

  private waitForAck(updateId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Update timeout'));
      }, 10000);

      this.socket.once(`ack:${updateId}`, (response) => {
        clearTimeout(timeout);
        if (response.success) {
          resolve();
        } else {
          reject(new Error(response.error));
        }
      });
    });
  }
}
```

### Conflict Resolution

```typescript
interface VersionedDocument {
  id: string;
  version: number;
  content: any;
  lastModifiedBy: string;
  lastModifiedAt: number;
}

class ConflictResolver {
  // Last-write-wins strategy
  resolveLastWriteWins(local: VersionedDocument, remote: VersionedDocument): VersionedDocument {
    return remote.lastModifiedAt > local.lastModifiedAt ? remote : local;
  }

  // Operational transformation
  transformOperations(
    localOps: Operation[],
    remoteOps: Operation[],
    baseVersion: number
  ): Operation[] {
    const transformed: Operation[] = [];

    for (const localOp of localOps) {
      let transformedOp = { ...localOp };

      for (const remoteOp of remoteOps) {
        transformedOp = this.transform(transformedOp, remoteOp);
      }

      transformed.push(transformedOp);
    }

    return transformed;
  }

  private transform(op1: Operation, op2: Operation): Operation {
    // Transform op1 against op2
    if (op1.type === 'insert' && op2.type === 'insert') {
      if (op2.position <= op1.position) {
        return { ...op1, position: op1.position + op2.text.length };
      }
    }
    // ... other transformation rules
    return op1;
  }

  // CRDT-based merge
  mergeWithCRDT(local: VersionedDocument, remote: VersionedDocument): VersionedDocument {
    // Use CRDT merge strategy (e.g., LWW-Element-Set)
    return {
      ...local,
      ...remote,
      version: Math.max(local.version, remote.version) + 1
    };
  }
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Socket.io Documentation](https://socket.io/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Operational Transformation](https://en.wikipedia.org/wiki/Operational_transformation)
