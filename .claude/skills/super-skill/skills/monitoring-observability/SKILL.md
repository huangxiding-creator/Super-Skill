---
name: monitoring-observability
description: Comprehensive monitoring, logging, tracing, and observability patterns. Covers structured logging, metrics collection, distributed tracing, alerting, and dashboard creation.
tags: [monitoring, logging, tracing, observability, metrics, alerting]
version: 1.0.0
source: Based on OpenTelemetry, Prometheus, Grafana, Datadog best practices
integrated-with: super-skill v3.7+
---

# Monitoring & Observability Skill

This skill provides comprehensive monitoring, logging, tracing, and observability patterns for production-grade applications.

## Observability Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                  OBSERVABILITY PILLARS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  METRICS                                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • CPU/Memory    • Request rate      • Error rate        │    │
│  │ • Prometheus    • StatsD            • CloudWatch        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LOGS                                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Structured logs   • Log levels    • Correlation IDs   │    │
│  │ • ELK Stack      • Loki            • CloudWatch Logs    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TRACES                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Request tracing   • Span analysis   • Dependencies    │    │
│  │ • Jaeger         • Zipkin           • OpenTelemetry     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ALERTS                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Threshold alerts   • Anomaly detection   • Runbooks   │    │
│  │ • PagerDuty      • OpsGenie         • Slack            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Structured Logging

### Logger Setup

```typescript
import pino from 'pino';

interface LogContext {
  requestId?: string;
  userId?: string;
  [key: string]: any;
}

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label })
  },
  timestamp: pino.stdTimeFunctions.isoTime,
  base: {
    service: 'api-service',
    version: process.env.APP_VERSION
  }
});

// Child logger with context
function createLogger(context: LogContext) {
  return logger.child(context);
}

// Usage
const requestLogger = createLogger({ requestId: 'req-123', userId: 'user-456' });
requestLogger.info({ action: 'order_created', orderId: 'order-789' }, 'Order created successfully');
```

### Log Levels & Standards

```typescript
enum LogLevel {
  TRACE = 'trace',  // Very detailed debugging
  DEBUG = 'debug',  // Detailed debugging
  INFO = 'info',    // Normal operations
  WARN = 'warn',    // Warning conditions
  ERROR = 'error',  // Error conditions
  FATAL = 'fatal'   // Critical errors
}

interface StructuredLog {
  timestamp: string;
  level: LogLevel;
  message: string;
  service: string;
  traceId?: string;
  spanId?: string;
  userId?: string;
  requestId?: string;
  duration?: number;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  metadata?: Record<string, any>;
}

// Request logging middleware
function requestLoggingMiddleware(req: Request, res: Response, next: NextFunction) {
  const startTime = Date.now();
  const requestId = req.headers['x-request-id'] || generateId();

  // Set context
  req.requestId = requestId;
  res.setHeader('x-request-id', requestId);

  // Log request
  logger.info({
    requestId,
    method: req.method,
    path: req.path,
    query: req.query,
    userAgent: req.headers['user-agent'],
    ip: req.ip
  }, 'Request started');

  // Log response
  res.on('finish', () => {
    const duration = Date.now() - startTime;

    logger.info({
      requestId,
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration
    }, 'Request completed');
  });

  next();
}
```

## Metrics Collection

### Prometheus Metrics

```typescript
import client from 'prom-client';

// Enable default metrics
const collectDefaultMetrics = client.collectDefaultMetrics;
collectDefaultMetrics({ register: client.register });

// Custom metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5, 10]
});

const httpRequestTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

const activeConnections = new client.Gauge({
  name: 'active_connections',
  help: 'Number of active connections'
});

const dbQueryDuration = new client.Histogram({
  name: 'db_query_duration_seconds',
  help: 'Duration of database queries',
  labelNames: ['query_type', 'table'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1]
});

// Metrics middleware
function metricsMiddleware(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();

  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;

    httpRequestDuration.labels(req.method, route, String(res.statusCode)).observe(duration);
    httpRequestTotal.labels(req.method, route, String(res.statusCode)).inc();
  });

  next();
}

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.send(await client.register.metrics());
});
```

### Business Metrics

```typescript
// Business-specific metrics
const businessMetrics = {
  ordersCreated: new client.Counter({
    name: 'orders_created_total',
    help: 'Total orders created',
    labelNames: ['status', 'payment_method']
  }),

  orderValue: new client.Histogram({
    name: 'order_value_dollars',
    help: 'Order value in dollars',
    labelNames: ['currency'],
    buckets: [10, 50, 100, 500, 1000]
  }),

  activeUsers: new client.Gauge({
    name: 'active_users',
    help: 'Number of currently active users'
  }),

  userRegistrations: new client.Counter({
    name: 'user_registrations_total',
    help: 'Total user registrations',
    labelNames: ['source']
  })
};

// Track business events
function trackOrderCreated(order: Order) {
  businessMetrics.ordersCreated.labels(order.status, order.paymentMethod).inc();
  businessMetrics.orderValue.labels(order.currency).observe(order.total);
}

function trackUserRegistration(source: string) {
  businessMetrics.userRegistrations.labels(source).inc();
}
```

## Distributed Tracing

### OpenTelemetry Setup

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-grpc';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'api-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.APP_VERSION
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT
  }),
  metricExporter: new OTLPMetricExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT
  })
});

sdk.start();

// Manual instrumentation
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('api-service');

async function processOrder(orderId: string): Promise<Order> {
  const span = tracer.startSpan('process_order', {
    attributes: { orderId }
  });

  try {
    // Child spans for sub-operations
    const order = await tracer.startActiveSpan('fetch_order', async (span) => {
      const result = await fetchOrder(orderId);
      span.end();
      return result;
    });

    await tracer.startActiveSpan('validate_order', async (span) => {
      await validateOrder(order);
      span.end();
    });

    await tracer.startActiveSpan('charge_payment', async (span) => {
      await chargePayment(order);
      span.end();
    });

    span.setStatus({ code: SpanStatusCode.OK });
    return order;
  } catch (error) {
    span.recordException(error);
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    throw error;
  } finally {
    span.end();
  }
}
```

### Trace Context Propagation

```typescript
import { context, propagation, trace } from '@opentelemetry/api';

// Inject trace context into outgoing requests
async function callExternalService(url: string, data: any) {
  const headers: Record<string, string> = {};

  // Inject trace context
  propagation.inject(context.active(), headers);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...headers
    },
    body: JSON.stringify(data)
  });

  return response.json();
}

// Extract trace context from incoming requests
function extractTraceContext(req: Request): Context {
  return propagation.extract(context.active(), req.headers);
}
```

## Alerting

### Alert Rules

```yaml
# Prometheus alerting rules
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status_code=~"5.."}[5m])) /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency"

      - alert: ServiceDown
        expr: up{job="api-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
          node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/...'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warnings'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true

  - name: 'critical-alerts'
    pagerduty_configs:
      - service_key: '<pagerduty-key>'
    slack_configs:
      - channel: '#critical-alerts'
        send_resolved: true

  - name: 'warnings'
    slack_configs:
      - channel: '#warnings'
        send_resolved: true
```

## Health Checks

```typescript
interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, { status: string; latency?: number; message?: string }>;
  version: string;
  uptime: number;
}

async function healthCheck(): Promise<HealthCheckResult> {
  const checks: HealthCheckResult['checks'] = {};

  // Database check
  try {
    const start = Date.now();
    await db.$queryRaw`SELECT 1`;
    checks.database = {
      status: 'healthy',
      latency: Date.now() - start
    };
  } catch (error) {
    checks.database = {
      status: 'unhealthy',
      message: error.message
    };
  }

  // Redis check
  try {
    const start = Date.now();
    await redis.ping();
    checks.redis = {
      status: 'healthy',
      latency: Date.now() - start
    };
  } catch (error) {
    checks.redis = {
      status: 'unhealthy',
      message: error.message
    };
  }

  // External service check
  try {
    const start = Date.now();
    const response = await fetch('https://api.external.com/health', {
      timeout: 5000
    });
    checks.external = {
      status: response.ok ? 'healthy' : 'degraded',
      latency: Date.now() - start
    };
  } catch (error) {
    checks.external = {
      status: 'degraded',
      message: error.message
    };
  }

  // Determine overall status
  const hasUnhealthy = Object.values(checks).some(c => c.status === 'unhealthy');
  const hasDegraded = Object.values(checks).some(c => c.status === 'degraded');

  const status = hasUnhealthy ? 'unhealthy' : hasDegraded ? 'degraded' : 'healthy';

  return {
    status,
    checks,
    version: process.env.APP_VERSION || 'unknown',
    uptime: process.uptime()
  };
}

// Health endpoint
app.get('/health', async (req, res) => {
  const health = await healthCheck();

  const statusCode = health.status === 'healthy' ? 200
    : health.status === 'degraded' ? 200
    : 503;

  res.status(statusCode).json(health);
});

// Readiness probe
app.get('/ready', async (req, res) => {
  const health = await healthCheck();
  if (health.status === 'unhealthy') {
    return res.status(503).json({ ready: false });
  }
  res.json({ ready: true });
});

// Liveness probe
app.get('/live', (req, res) => {
  res.json({ alive: true });
});
```

## Integration with Super-Skill

### Phase Integration

```yaml
observability_phase_mapping:
  phase_7_initialization:
    actions:
      - setup_logging
      - configure_metrics
      - enable_tracing

  phase_8_development:
    actions:
      - add_instrumentation
      - create_health_checks
      - implement_correlation_ids

  phase_11_deployment:
    actions:
      - configure_alerts
      - setup_dashboards
      - test_runbooks
```

## Best Practices Checklist

### Logging
- [ ] Structured logging format
- [ ] Appropriate log levels
- [ ] Correlation IDs
- [ ] Sensitive data redacted

### Metrics
- [ ] RED metrics (Rate, Errors, Duration)
- [ ] Business metrics
- [ ] Custom metrics documented
- [ ] Appropriate buckets

### Tracing
- [ ] All services instrumented
- [ ] Context propagation
- [ ] Error recording
- [ ] Sampling configured

### Alerting
- [ ] Alert rules defined
- [ ] Runbooks created
- [ ] Escalation paths
- [ ] False positive tuning

## Deliverables

- Logging configuration
- Metrics definitions
- Tracing setup
- Alert rules
- Health check endpoints

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Google SRE Book](https://sre.google/books/)
- [Datadog Best Practices](https://www.datadoghq.com/blog/)
