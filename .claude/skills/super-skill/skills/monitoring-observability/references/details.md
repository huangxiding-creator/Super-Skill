# monitoring-observability — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
