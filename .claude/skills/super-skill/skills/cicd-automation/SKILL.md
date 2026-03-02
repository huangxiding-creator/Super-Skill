---
name: cicd-automation
description: CI/CD pipeline automation with GitHub Actions best practices. Provides modular workflow templates, security hardening, performance optimization, and deployment strategies for production-grade pipelines.
tags: [cicd, github-actions, automation, deployment, pipelines]
version: 1.0.0
source: Based on GitHub Actions best practices 2025, enterprise CI/CD patterns
integrated-with: super-skill v3.7+
---

# CI/CD Automation Skill

This skill provides comprehensive CI/CD pipeline automation patterns using GitHub Actions, enabling efficient, secure, and maintainable continuous integration and deployment workflows.

## Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD AUTOMATION LIFECYCLE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│   │  Code   │──▶│  Build  │──▶│  Test   │──▶│  Scan   │        │
│   │  Push   │   │         │   │         │   │         │        │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘        │
│        │                                          │              │
│        ▼                                          ▼              │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐        │
│   │ Package │◀──│  Audit  │◀──│  QA     │◀──│ Security│        │
│   │         │   │         │   │         │   │         │        │
│   └─────────┘   └─────────┘   └─────────┘   └─────────┘        │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────┐   ┌─────────┐   ┌─────────┐                      │
│   │ Deploy  │──▶│ Monitor │──▶│ Rollback│ (if needed)          │
│   │         │   │         │   │         │                      │
│   └─────────┘   └─────────┘   └─────────┘                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Design

### Modular & Reusable Workflows

```yaml
# .github/workflows/ci-template.yml
name: CI Template
on:
  workflow_call:
    inputs:
      node-version:
        required: true
        type: string
      run-e2e:
        required: false
        type: boolean
        default: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm run build
```

### Smart Triggering

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'package.json'
      - '.github/workflows/**'
    paths-ignore:
      - '**.md'
      - 'docs/**'

  pull_request:
    branches: [main]

  schedule:
    - cron: '0 6 * * 1'  # Weekly security scan
```

## Performance Optimization

### Caching Strategies

```yaml
jobs:
  build:
    steps:
      # Dependency caching
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: |
            ~/.npm
            node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-

      # Build caching
      - name: Cache build output
        uses: actions/cache@v4
        with:
          path: |
            .next/cache
            dist
          key: ${{ runner.os }}-build-${{ github.sha }}
          restore-keys: |
            ${{ runner.os }}-build-
```

### Matrix Builds

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        node: [18, 20, 22]
        exclude:
          - os: macos-latest
            node: 18
      fail-fast: false
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
```

### Timeout Controls

```yaml
jobs:
  build:
    timeout-minutes: 30
    steps:
      - name: Long running task
        timeout-minutes: 10
        run: npm run build
```

## Security Best Practices

### Secrets Management

```yaml
jobs:
  deploy:
    steps:
      # NEVER hardcode secrets
      - name: Deploy to production
        env:
          API_KEY: ${{ secrets.PRODUCTION_API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          # Use secrets securely
          echo "Deploying with secure credentials"
```

### Pin Actions to Versions

```yaml
# GOOD: Pin to specific version with SHA
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1

# ACCEPTABLE: Pin to semantic version
- uses: actions/checkout@v4.1.1

# AVOID: Unstable latest tag
- uses: actions/checkout@latest  # DON'T USE
```

### Workflow Protection

```yaml
# CODEOWNERS file for workflow protection
# .github/CODEOWNERS
.github/workflows/ @security-team @devops-lead

# Require review for workflow changes
# In repository settings:
# - Branch protection for main
# - Require PR reviews
# - Require status checks
```

### OIDC Authentication

```yaml
# Use OIDC instead of stored secrets for cloud auth
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions
          aws-region: us-east-1
```

## Pipeline Structure

### Continuous Integration

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    needs: [lint, type-check]
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:coverage

  security:
    runs-on: ubuntu-latest
    needs: [lint, type-check]
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
      - uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
```

### Continuous Deployment

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          # Staging deployment
          npm run deploy:staging

  integration-tests:
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: npm run test:integration

  deploy-production:
    runs-on: ubuntu-latest
    needs: integration-tests
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          # Production deployment with blue-green
          npm run deploy:production
```

## Deployment Strategies

### Blue-Green Deployment

```yaml
jobs:
  deploy:
    steps:
      - name: Blue-Green Deploy
        run: |
          # Deploy to inactive environment
          ENV=$(get_inactive_env)
          deploy_to $ENV

          # Run smoke tests
          run_smoke_tests $ENV

          # Switch traffic
          switch_traffic $ENV

          # Monitor for issues
          monitor_deployment
```

### Canary Release

```yaml
jobs:
  canary:
    steps:
      - name: Canary Deploy
        run: |
          # Deploy to 10% of traffic
          set_canary_weight 10

          # Monitor metrics
          if metrics_healthy; then
            # Gradually increase
            set_canary_weight 25
            set_canary_weight 50
            set_canary_weight 100
          else
            # Rollback
            set_canary_weight 0
            exit 1
          fi
```

### Automatic Rollback

```yaml
jobs:
  deploy:
    steps:
      - name: Deploy with Rollback
        run: |
          # Store current version
          CURRENT_VERSION=$(get_current_version)

          # Deploy new version
          deploy_new_version

          # Wait for health checks
          sleep 60

          # Check application health
          if ! health_check; then
            echo "Health check failed, rolling back"
            rollback_to $CURRENT_VERSION
            exit 1
          fi
```

## Monitoring & Notifications

### Status Badges

```markdown
<!-- README.md -->
[![CI](https://github.com/user/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/user/repo/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/user/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/user/repo)
```

### Slack Notifications

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author,action
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Integration with Super-Skill

### Phase Integration

```yaml
cicd_phase_mapping:
  phase_7_initialization:
    actions:
      - create_ci_workflow
      - setup_branch_protection
      - configure_secrets

  phase_8_development:
    actions:
      - run_automated_tests
      - lint_and_type_check
      - security_scan

  phase_11_deployment:
    actions:
      - build_production
      - deploy_to_staging
      - run_integration_tests
      - deploy_to_production
```

### Automated Workflow Generation

```python
def generate_ci_workflow(project_type: str) -> dict:
    """
    Generate CI workflow based on project type.
    """
    templates = {
        "nextjs": NEXTJS_CI_TEMPLATE,
        "react": REACT_CI_TEMPLATE,
        "node": NODE_CI_TEMPLATE,
        "python": PYTHON_CI_TEMPLATE
    }

    return templates.get(project_type, DEFAULT_CI_TEMPLATE)

def generate_cd_workflow(
    deployment_target: str,
    strategy: str = "blue-green"
) -> dict:
    """
    Generate CD workflow based on deployment target.
    """
    strategies = {
        "blue-green": BLUE_GREEN_TEMPLATE,
        "canary": CANARY_TEMPLATE,
        "rolling": ROLLING_TEMPLATE
    }

    return {
        "deployment_target": deployment_target,
        "strategy": strategies[strategy],
        "rollback_enabled": True
    }
```

## Best Practices Checklist

### Workflow Design
- [ ] Modular, reusable workflows
- [ ] Smart path-based triggering
- [ ] Proper timeout controls
- [ ] Matrix builds for cross-platform
- [ ] Fail-fast disabled for matrix

### Security
- [ ] Actions pinned to SHA or version
- [ ] Secrets properly managed
- [ ] OIDC for cloud authentication
- [ ] CODEOWNERS for workflow protection
- [ ] Input sanitization

### Performance
- [ ] Dependency caching enabled
- [ ] Build output caching
- [ ] Parallel job execution
- [ ] Efficient runner selection
- [ ] Conditional step execution

### Monitoring
- [ ] Status badges in README
- [ ] Slack/email notifications
- [ ] Health checks post-deployment
- [ ] Automated rollback configured
- [ ] Audit logging enabled

## Deliverables

- `.github/workflows/` directory with workflows
- CODEOWNERS file
- Branch protection rules
- Status badges
- Notification configuration

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitHub Actions Marketplace](https://github.com/marketplace/actions)
- [Security Hardening Guide](https://docs.github.com/en/actions/security-guides)
- [Reusable Workflows](https://docs.github.com/actions/using-workflows/reusing-workflows)
