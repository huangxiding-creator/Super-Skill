---
name: feature-flags
description: Feature flag and A/B testing patterns for progressive rollouts and experimentation. Covers LaunchDarkly, Unleash, Statsig, and custom implementations.
tags: [feature-flags, ab-testing, experimentation, rollout, launchdarkly]
version: 1.0.0
source: Based on LaunchDarkly, Unleash, Statsig best practices
integrated-with: super-skill v3.7+
---

# Feature Flags Skill

This skill provides comprehensive feature flag patterns for progressive rollouts, A/B testing, and experimentation.

## Feature Flag Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   FEATURE FLAG ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FLAG TYPES                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Boolean     • Multivariate    • JSON config           │    │
│  │ • On/Off      • A/B variants    • Dynamic config        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TARGETING                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • User ID     • User segments    • Percentage rollout   │    │
│  │ • Attributes  • Environment      • Time-based           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ROLLOUT STRATEGIES                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Canary      • Blue-Green       • Kill switch          │    │
│  │ • Gradual     • Ring deployment  • Emergency disable    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ANALYTICS                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Conversion  • Statistical signif.  • Impact analysis  │    │
│  │ • Engagement  • Confidence intervals • Revenue impact   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Feature Flag Implementation

### Core Types

```typescript
interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  type: 'boolean' | 'multivariate' | 'json';
  enabled: boolean;

  // Targeting rules
  targeting: TargetingRule[];

  // Default value
  defaultValue: any;

  // Variants for A/B testing
  variations?: Variation[];

  // Metadata
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

interface TargetingRule {
  conditions: Condition[];
  rollout?: RolloutConfig;
  variation?: string;
  value?: any;
}

interface Condition {
  attribute: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'in' | 'notIn' | 'matches' | 'contains';
  value: any;
}

interface RolloutConfig {
  percentage: number;
  bucketBy?: string; // Attribute to use for bucketing
}

interface Variation {
  key: string;
  name: string;
  value: any;
  percentage: number;
}
```

### Feature Flag Service

```typescript
import murmurhash from 'murmurhash';

class FeatureFlagService {
  private flags: Map<string, FeatureFlag> = new Map();
  private analytics: AnalyticsTracker;

  constructor(analytics: AnalyticsTracker) {
    this.analytics = analytics;
  }

  // Evaluate flag for a user
  evaluate(key: string, user: UserContext, defaultValue: any = false): any {
    const flag = this.flags.get(key);

    if (!flag || !flag.enabled) {
      return defaultValue;
    }

    // Check targeting rules in order
    for (const rule of flag.targeting) {
      if (this.matchesConditions(user, rule.conditions)) {
        // If rollout specified, check if user is in rollout
        if (rule.rollout) {
          const bucket = this.getBucket(user, key, rule.rollout.bucketBy);
          if (bucket > rule.rollout.percentage) {
            continue; // Not in rollout, try next rule
          }
        }

        // Track evaluation
        this.analytics.track('flag_evaluated', {
          flag: key,
          user: user.id,
          result: rule.variation || rule.value
        });

        return rule.variation ? this.getVariation(flag, rule.variation) : rule.value;
      }
    }

    // Check if multivariate with variations
    if (flag.variations && flag.variations.length > 0) {
      return this.getVariationByPercentage(user, key, flag.variations);
    }

    return flag.defaultValue;
  }

  // Check if user matches conditions
  private matchesConditions(user: UserContext, conditions: Condition[]): boolean {
    return conditions.every(condition => {
      const userValue = user[condition.attribute as keyof UserContext];

      switch (condition.operator) {
        case 'eq':
          return userValue === condition.value;
        case 'ne':
          return userValue !== condition.value;
        case 'gt':
          return userValue > condition.value;
        case 'lt':
          return userValue < condition.value;
        case 'in':
          return Array.isArray(condition.value) && condition.value.includes(userValue);
        case 'notIn':
          return Array.isArray(condition.value) && !condition.value.includes(userValue);
        case 'matches':
          return new RegExp(condition.value).test(String(userValue));
        case 'contains':
          return String(userValue).includes(condition.value);
        default:
          return false;
      }
    });
  }

  // Get consistent bucket for user (0-100)
  private getBucket(user: UserContext, key: string, bucketBy?: string): number {
    const bucketKey = bucketBy ? user[bucketBy as keyof UserContext] : user.id;
    const hash = murmurhash.v3(`${key}-${bucketKey}`);
    return (hash % 100) + 1;
  }

  // Get variation by percentage rollout
  private getVariationByPercentage(
    user: UserContext,
    key: string,
    variations: Variation[]
  ): any {
    const bucket = this.getBucket(user, key);
    let cumulative = 0;

    for (const variation of variations) {
      cumulative += variation.percentage;
      if (bucket <= cumulative) {
        return variation.value;
      }
    }

    return variations[0].value;
  }

  // Update flag
  async updateFlag(key: string, updates: Partial<FeatureFlag>): Promise<void> {
    const flag = this.flags.get(key);
    if (flag) {
      this.flags.set(key, { ...flag, ...updates, updatedAt: new Date() });
    }
  }

  // Enable/disable flag
  async setEnabled(key: string, enabled: boolean): Promise<void> {
    await this.updateFlag(key, { enabled });
    this.analytics.track('flag_toggled', { flag: key, enabled });
  }

  // Kill switch - immediately disable
  async killSwitch(key: string): Promise<void> {
    await this.setEnabled(key, false);
    // Alert team
    await this.alertTeam(`Feature flag ${key} has been killed`);
  }
}
```

### React Integration

```typescript
import { createContext, useContext, useEffect, useState } from 'react';

const FeatureFlagContext = createContext<FeatureFlagService | null>(null);

export function FeatureFlagProvider({
  children,
  user
}: {
  children: React.ReactNode;
  user: UserContext;
}) {
  const [service] = useState(() => new FeatureFlagService(analytics));

  // Subscribe to flag updates
  useEffect(() => {
    const unsubscribe = service.subscribe(() => {
      // Force re-render when flags change
    });

    return unsubscribe;
  }, [service]);

  return (
    <FeatureFlagContext.Provider value={service}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

// Hook to check feature flag
export function useFeatureFlag(key: string, defaultValue: any = false): any {
  const service = useContext(FeatureFlagContext);
  const user = useUser();
  const [value, setValue] = useState(() =>
    service?.evaluate(key, user, defaultValue)
  );

  useEffect(() => {
    setValue(service?.evaluate(key, user, defaultValue));
  }, [service, key, user, defaultValue]);

  return value;
}

// Boolean flag hook
export function useFlag(key: string, defaultValue = false): boolean {
  return useFeatureFlag(key, defaultValue);
}

// Variant hook for A/B testing
export function useVariant(key: string): string {
  return useFeatureFlag(key, 'control');
}

// Usage
function MyComponent() {
  const showNewFeature = useFlag('new-dashboard');
  const variant = useVariant('checkout-flow');

  return (
    <div>
      {showNewFeature ? <NewDashboard /> : <OldDashboard />}

      {variant === 'simplified' ? (
        <SimplifiedCheckout />
      ) : (
        <StandardCheckout />
      )}
    </div>
  );
}
```

## A/B Testing Patterns

### Experiment Configuration

```typescript
interface Experiment {
  id: string;
  name: string;
  description: string;
  hypothesis: string;

  // Variants
  variants: ExperimentVariant[];

  // Targeting
  targeting: {
    userSegments: string[];
    percentage: number;
    startDate: Date;
    endDate?: Date;
  };

  // Metrics
  primaryMetric: string;
  secondaryMetrics: string[];

  // Statistical config
  statisticalConfig: {
    significanceLevel: number; // 0.05 for 95% confidence
    power: number; // 0.8 typical
    minDetectableEffect: number;
  };
}

interface ExperimentVariant {
  id: string;
  name: string;
  isControl: boolean;
  percentage: number;
  config: Record<string, any>;
}

class ExperimentService {
  private experiments: Map<string, Experiment> = new Map();
  private analytics: AnalyticsTracker;

  // Assign user to experiment
  assignUser(experimentId: string, user: UserContext): ExperimentVariant {
    const experiment = this.experiments.get(experimentId);
    if (!experiment) {
      return this.getControlVariant(experimentId);
    }

    // Check if user is targeted
    if (!this.isTargeted(user, experiment.targeting)) {
      return this.getControlVariant(experimentId);
    }

    // Check if experiment is running
    if (!this.isRunning(experiment)) {
      return this.getControlVariant(experimentId);
    }

    // Assign variant based on bucketing
    const bucket = this.getBucket(user, experimentId);
    let cumulative = 0;

    for (const variant of experiment.variants) {
      cumulative += variant.percentage;
      if (bucket <= cumulative) {
        this.analytics.track('experiment_assigned', {
          experiment: experimentId,
          variant: variant.id,
          user: user.id
        });
        return variant;
      }
    }

    return this.getControlVariant(experimentId);
  }

  // Track conversion event
  trackConversion(experimentId: string, variantId: string, metric: string, value: number = 1): void {
    this.analytics.track('experiment_conversion', {
      experiment: experimentId,
      variant: variantId,
      metric,
      value
    });
  }

  // Get experiment results
  async getResults(experimentId: string): Promise<ExperimentResults> {
    const experiment = this.experiments.get(experimentId);

    // Fetch analytics data
    const data = await this.analytics.getExperimentData(experimentId);

    // Calculate statistics
    return this.calculateStatistics(data, experiment!);
  }

  private calculateStatistics(data: any, experiment: Experiment): ExperimentResults {
    const results: ExperimentResults = {
      experimentId: experiment.id,
      variants: [],
      winner: null,
      confidence: null
    };

    for (const variant of experiment.variants) {
      const variantData = data.variants[variant.id];

      results.variants.push({
        variantId: variant.id,
        sampleSize: variantData.users,
        conversions: variantData.conversions,
        conversionRate: variantData.conversions / variantData.users,
        mean: variantData.mean,
        stdDev: variantData.stdDev,
        confidenceInterval: this.calculateConfidenceInterval(variantData)
      });
    }

    // Determine winner
    if (this.hasSignificantResult(results, experiment.statisticalConfig)) {
      results.winner = this.findWinner(results.variants);
      results.confidence = this.calculateConfidence(results, experiment.statisticalConfig);
    }

    return results;
  }
}
```

### Progressive Rollout

```typescript
class ProgressiveRollout {
  private flagService: FeatureFlagService;
  private metricsService: MetricsService;

  async rollout(
    flagKey: string,
    config: RolloutPlan
  ): Promise<void> {
    const stages = [
      { percentage: 1, duration: 1000 * 60 * 60 },      // 1% for 1 hour
      { percentage: 5, duration: 1000 * 60 * 60 * 2 },  // 5% for 2 hours
      { percentage: 10, duration: 1000 * 60 * 60 * 4 }, // 10% for 4 hours
      { percentage: 25, duration: 1000 * 60 * 60 * 8 }, // 25% for 8 hours
      { percentage: 50, duration: 1000 * 60 * 60 * 24 }, // 50% for 24 hours
      { percentage: 100, duration: 0 }                   // 100%
    ];

    for (const stage of stages) {
      // Update rollout percentage
      await this.flagService.updateFlag(flagKey, {
        targeting: [{
          conditions: [],
          rollout: { percentage: stage.percentage }
        }]
      });

      // Wait for duration
      if (stage.duration > 0) {
        await this.sleep(stage.duration);

        // Check metrics before proceeding
        const health = await this.checkHealth(flagKey);

        if (!health.healthy) {
          // Rollback
          await this.flagService.killSwitch(flagKey);
          throw new Error(`Rollout paused: ${health.reason}`);
        }
      }
    }
  }

  private async checkHealth(flagKey: string): Promise<HealthStatus> {
    const metrics = await this.metricsService.getRecent(flagKey);

    // Check error rate
    if (metrics.errorRate > 0.01) { // 1% error rate
      return { healthy: false, reason: `High error rate: ${metrics.errorRate}` };
    }

    // Check latency
    if (metrics.p95Latency > metrics.baseline.p95Latency * 1.5) {
      return { healthy: false, reason: `High latency: ${metrics.p95Latency}` };
    }

    return { healthy: true };
  }
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
feature_flag_phase_mapping:
  phase_4_requirements:
    outputs:
      - feature_flag_requirements
      - experiment_specs

  phase_8_development:
    actions:
      - setup_feature_flag_service
      - implement_flag_checks
      - create_ab_tests

  phase_10_optimization:
    actions:
      - analyze_experiments
      - progressive_rollouts
      - feature_cleanup
```

## Best Practices Checklist

### Flag Design
- [ ] Clear naming convention
- [ ] Documented purpose
- [ ] Default values set
- [ ] Temporary flags marked

### Targeting
- [ ] Segments defined
- [ ] Consistent bucketing
- [ ] Edge cases handled
- [ ] Override capability

### Safety
- [ ] Kill switch ready
- [ ] Rollback plan
- [ ] Monitoring in place
- [ ] Alerts configured

## Deliverables

- Feature flag service
- Flag configuration files
- A/B test framework
- Analytics dashboard

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [LaunchDarkly Documentation](https://docs.launchdarkly.com/)
- [Unleash](https://github.com/Unleash/unleash)
- [Statsig](https://docs.statsig.com/)
- [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)
