---
name: error-recovery
description: Comprehensive error handling, self-healing, and resilience patterns. Implements retry strategies, circuit breakers, fallbacks, and automated recovery for production-grade reliability.
tags: [error-handling, resilience, self-healing, circuit-breaker, retry]
version: 1.0.0
source: Based on resilience4j, Polly patterns, Site Reliability Engineering best practices
integrated-with: super-skill v3.7+
---
# Error Recovery Skill

This skill provides comprehensive error handling, self-healing, and resilience patterns for building fault-tolerant applications with automated recovery capabilities.

## Resilience Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESILIENCE PATTERNS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RETRY                                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Exponential Backoff   • Jitter   • Max Attempts       │    │
│  │ • Retryable Errors      • Timeout  • Idempotency        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  CIRCUIT BREAKER                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Closed → Open → Half-Open → Closed                    │    │
│  │ • Failure Threshold     • Recovery Timeout              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  FALLBACK                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Default Values   • Cached Data   • Graceful Degradation│   │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  BULKHEAD                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Isolate Failures   • Resource Limits   • Queuing      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Retry Strategies

### Exponential Backoff with Jitter

```typescript
interface RetryConfig {
  maxAttempts: number;
  initialDelay: number;
  maxDelay: number;
  multiplier: number;
  jitter: boolean;
  retryableErrors: string[];
}

async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  config: RetryConfig
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      // Check if error is retryable
      if (!isRetryable(error, config.retryableErrors)) {
        throw error;
      }

      // Don't wait after last attempt
      if (attempt === config.maxAttempts) {
        break;
      }

      // Calculate delay with exponential backoff
      const delay = calculateDelay(
        attempt,
        config.initialDelay,
        config.maxDelay,
        config.multiplier,
        config.jitter
      );

      await sleep(delay);
    }
  }

  throw new RetryExhaustedError(
    `Operation failed after ${config.maxAttempts} attempts`,
    lastError
  );
}

function calculateDelay(
  attempt: number,
  initial: number,
  max: number,
  multiplier: number,
  jitter: boolean
): number {
  // Exponential backoff
  let delay = initial * Math.pow(multiplier, attempt - 1);

  // Cap at max
  delay = Math.min(delay, max);

  // Add jitter (randomization)
  if (jitter) {
    delay = delay * (0.5 + Math.random());
  }

  return Math.floor(delay);
}

function isRetryable(error: Error, retryablePatterns: string[]): boolean {
  const errorMessage = error.message.toLowerCase();
  return retryablePatterns.some(pattern =>
    errorMessage.includes(pattern.toLowerCase())
  );
}
```

### Decorated Functions

```typescript
// Retry decorator
function retryable(config: Partial<RetryConfig> = {}) {
  const fullConfig: RetryConfig = {
    maxAttempts: 3,
    initialDelay: 1000,
    maxDelay: 30000,
    multiplier: 2,
    jitter: true,
    retryableErrors: ['timeout', 'econnreset', '503', '502'],
    ...config
  };

  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      return retryWithBackoff(
        () => originalMethod.apply(this, args),
        fullConfig
      );
    };

    return descriptor;
  };
}

// Usage
class PaymentService {
  @retryable({ maxAttempts: 5, initialDelay: 2000 })
  async processPayment(order: Order): Promise<PaymentResult> {
    // Will automatically retry on transient failures
    return await this.paymentGateway.charge(order);
  }
}
```

## Circuit Breaker

### Implementation

```typescript
type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitBreakerConfig {
  failureThreshold: number;
  successThreshold: number;
  timeout: number;
  resetTimeout: number;
}

class CircuitBreaker<T> {
  private state: CircuitState = 'CLOSED';
  private failures: number = 0;
  private successes: number = 0;
  private lastFailureTime: number = 0;

  constructor(
    private operation: () => Promise<T>,
    private config: CircuitBreakerConfig,
    private fallback?: () => Promise<T>
  ) {}

  async execute(): Promise<T> {
    if (this.state === 'OPEN') {
      if (this.shouldAttemptReset()) {
        this.state = 'HALF_OPEN';
      } else {
        return this.handleOpenState();
      }
    }

    try {
      const result = await this.executeWithTimeout();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private async executeWithTimeout(): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        reject(new TimeoutError('Operation timed out'));
      }, this.config.timeout);

      this.operation()
        .then(result => {
          clearTimeout(timeoutId);
          resolve(result);
        })
        .catch(error => {
          clearTimeout(timeoutId);
          reject(error);
        });
    });
  }

  private onSuccess(): void {
    this.failures = 0;

    if (this.state === 'HALF_OPEN') {
      this.successes++;
      if (this.successes >= this.config.successThreshold) {
        this.state = 'CLOSED';
        this.successes = 0;
      }
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.state === 'HALF_OPEN') {
      this.state = 'OPEN';
      this.successes = 0;
    } else if (this.failures >= this.config.failureThreshold) {
      this.state = 'OPEN';
    }
  }

  private shouldAttemptReset(): boolean {
    return Date.now() - this.lastFailureTime >= this.config.resetTimeout;
  }

  private async handleOpenState(): Promise<T> {
    if (this.fallback) {
      return this.fallback();
    }
    throw new CircuitOpenError('Circuit breaker is open');
  }

  getState(): CircuitState {
    return this.state;
  }

  getStats(): CircuitStats {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      lastFailureTime: this.lastFailureTime
    };
  }
}
```

### Usage Pattern

```typescript
// Circuit breaker for external API
const apiCircuit = new CircuitBreaker(
  () => fetchExternalAPI(),
  {
    failureThreshold: 5,
    successThreshold: 3,
    timeout: 5000,
    resetTimeout: 30000
  },
  () => getCachedData() // Fallback
);

// Use in service
class ExternalService {
  async getData(): Promise<Data> {
    try {
      return await apiCircuit.execute();
    } catch (error) {
      if (error instanceof CircuitOpenError) {
        logger.warn('External API circuit is open, using fallback');
        return this.getFallbackData();
      }
      throw error;
    }
  }
}
```

## Fallback Strategies

### Graceful Degradation

```typescript
interface ServiceTier {
  name: string;
  priority: number;
  execute: () => Promise<any>;
}

class FallbackChain {
  constructor(private tiers: ServiceTier[]) {
    // Sort by priority (lower = higher priority)
    this.tiers.sort((a, b) => a.priority - b.priority);
  }

  async execute<T>(): Promise<T> {
    const errors: Error[] = [];

    for (const tier of this.tiers) {
      try {
        const result = await tier.execute();
        logger.info(`Successfully executed tier: ${tier.name}`);
        return result;
      } catch (error) {
        logger.warn(`Tier ${tier.name} failed, trying next`, { error });
        errors.push(error as Error);
      }
    }

    throw new AllTiersFailedError(
      'All fallback tiers failed',
      errors
    );
  }
}

// Usage
const dataFetchChain = new FallbackChain([
  {
    name: 'live-api',
    priority: 1,
    execute: () => fetchFromLiveAPI()
  },
  {
    name: 'cache',
    priority: 2,
    execute: () => fetchFromCache()
  },
  {
    name: 'static-defaults',
    priority: 3,
    execute: () => Promise.resolve(getDefaultData())
  }
]);
```

### Cached Fallback

```typescript
class CachedFallbackService<T> {
  private cache: Map<string, { data: T; timestamp: number }> = new Map();
  private staleTimeout: number;

  constructor(
    private fetcher: (key: string) => Promise<T>,
    options: { staleTimeout?: number } = {}
  ) {
    this.staleTimeout = options.staleTimeout || 300000; // 5 minutes
  }

  async get(key: string): Promise<T> {
    try {
      const freshData = await this.fetcher(key);
      this.cache.set(key, { data: freshData, timestamp: Date.now() });
      return freshData;
    } catch (error) {
      const cached = this.cache.get(key);
      if (cached && !this.isStale(cached.timestamp)) {
        logger.warn(`Using cached fallback for ${key}`);
        return cached.data;
      }
      throw error;
    }
  }

  private isStale(timestamp: number): boolean {
    return Date.now() - timestamp > this.staleTimeout;
  }
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
error_recovery_phase_mapping:
  phase_8_development:
    actions:
      - implement_retry_strategies
      - add_circuit_breakers
      - create_fallback_chains

  phase_9_qa:
    actions:
      - error_injection_testing
      - resilience_validation
      - recovery_testing

  phase_10_optimization:
    actions:
      - tune_retry_parameters
      - adjust_circuit_thresholds
      - optimize_fallback_strategies

  phase_11_deployment:
    actions:
      - configure_monitoring
      - setup_alerting
      - enable_auto_recovery
```

## Best Practices Checklist

### Retry
- [ ] Exponential backoff implemented
- [ ] Jitter added to prevent thundering herd
- [ ] Max attempts defined
- [ ] Retryable errors identified

### Circuit Breaker
- [ ] Failure threshold set appropriately
- [ ] Reset timeout configured
- [ ] Fallback defined
- [ ] State monitoring enabled

### Fallback
- [ ] Graceful degradation paths defined
- [ ] Cache fallback available
- [ ] Default values provided
- [ ] User experience maintained

### Bulkhead
- [ ] Concurrent limits set
- [ ] Queue timeouts defined
- [ ] Isolation boundaries clear
- [ ] Monitoring in place

## Deliverables

- Retry configuration
- Circuit breaker setup
- Fallback chains
- Error classification
- Self-healing actions
- Monitoring dashboard

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `Bulkhead Pattern`, `Error Classification`, `Self-Healing Actions`, `Version History`, `References`.
