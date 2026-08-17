# error-recovery — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Bulkhead Pattern

```typescript
import { Semaphore } from 'async-mutex';

class Bulkhead {
  private semaphore: Semaphore;

  constructor(
    private maxConcurrent: number,
    private maxWaitMs: number = 5000
  ) {
    this.semaphore = new Semaphore(maxConcurrent);
  }

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    const acquired = await this.tryAcquire();

    if (!acquired) {
      throw new BulkheadRejectionError(
        `Bulkhead full: ${this.maxConcurrent} concurrent operations`
      );
    }

    try {
      return await operation();
    } finally {
      this.semaphore.release();
    }
  }

  private async tryAcquire(): Promise<boolean> {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        resolve(false);
      }, this.maxWaitMs);

      this.semaphore.acquire().then(() => {
        clearTimeout(timeout);
        resolve(true);
      });
    });
  }
}

// Usage
const apiBulkhead = new Bulkhead(10, 2000); // Max 10 concurrent

async function callExternalAPI(params: any) {
  return apiBulkhead.execute(() =>
    fetch('/api/external', { method: 'POST', body: JSON.stringify(params) })
  );
}
```

## Error Classification

```typescript
enum ErrorSeverity {
  LOW = 'LOW',           // Can be ignored or logged
  MEDIUM = 'MEDIUM',     // Requires attention
  HIGH = 'HIGH',         // Service degradation
  CRITICAL = 'CRITICAL'  // Service failure
}

enum ErrorCategory {
  TRANSIENT = 'TRANSIENT',     // Temporary, may succeed on retry
  PERMANENT = 'PERMANENT',     // Will always fail
  EXTERNAL = 'EXTERNAL',       // Third-party service error
  INTERNAL = 'INTERNAL',       // Our code error
  RESOURCE = 'RESOURCE',       // Resource exhaustion
  VALIDATION = 'VALIDATION',   // Input validation
  AUTH = 'AUTH'               // Authentication/authorization
}

class ClassifiedError extends Error {
  constructor(
    message: string,
    public severity: ErrorSeverity,
    public category: ErrorCategory,
    public retryable: boolean,
    public originalError?: Error
  ) {
    super(message);
  }
}

function classifyError(error: Error): ClassifiedError {
  // Network errors
  if (error.message.includes('ECONNRESET') ||
      error.message.includes('ETIMEDOUT')) {
    return new ClassifiedError(
      'Network connectivity issue',
      ErrorSeverity.MEDIUM,
      ErrorCategory.TRANSIENT,
      true,
      error
    );
  }

  // Rate limiting
  if (error.message.includes('429')) {
    return new ClassifiedError(
      'Rate limit exceeded',
      ErrorSeverity.MEDIUM,
      ErrorCategory.EXTERNAL,
      true,
      error
    );
  }

  // Auth errors
  if (error.message.includes('401') || error.message.includes('403')) {
    return new ClassifiedError(
      'Authentication failed',
      ErrorSeverity.HIGH,
      ErrorCategory.AUTH,
      false,
      error
    );
  }

  // Default to internal error
  return new ClassifiedError(
    error.message,
    ErrorSeverity.MEDIUM,
    ErrorCategory.INTERNAL,
    false,
    error
  );
}
```

## Self-Healing Actions

```typescript
interface SelfHealingAction {
  trigger: ErrorCategory | ErrorSeverity;
  action: (error: ClassifiedError, context: any) => Promise<void>;
}

class SelfHealingService {
  private actions: SelfHealingAction[] = [];

  register(action: SelfHealingAction): void {
    this.actions.push(action);
  }

  async handle(error: Error, context: any): Promise<void> {
    const classified = classifyError(error);

    for (const { trigger, action } of this.actions) {
      if (this.matchesTrigger(classified, trigger)) {
        try {
          await action(classified, context);
          logger.info(`Self-healing action executed for ${classified.category}`);
        } catch (healError) {
          logger.error('Self-healing action failed', { healError });
        }
      }
    }
  }

  private matchesTrigger(
    error: ClassifiedError,
    trigger: ErrorCategory | ErrorSeverity
  ): boolean {
    return error.category === trigger || error.severity === trigger;
  }
}

// Register self-healing actions
const healer = new SelfHealingService();

// Clear cache on data corruption
healer.register({
  trigger: ErrorCategory.RESOURCE,
  action: async (error, context) => {
    await context.cache.clear();
    logger.info('Cache cleared due to resource error');
  }
});

// Reconnect on connection errors
healer.register({
  trigger: ErrorCategory.TRANSIENT,
  action: async (error, context) => {
    await context.connectionPool.reconnect();
    logger.info('Reconnected due to transient error');
  }
});
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Resilience4j](https://github.com/resilience4j/resilience4j)
- [Polly](https://github.com/App-vNext/Polly)
- [Google SRE Book](https://sre.google/books/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
