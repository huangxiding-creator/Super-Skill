# feature-flags — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
