# testing-automation — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## E2E Testing with Playwright

### Configuration

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry'
  },

  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' }
    },
    {
      name: 'firefox',
      use: { browserName: 'firefox' }
    },
    {
      name: 'webkit',
      use: { browserName: 'webkit' }
    }
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI
  }
});
```

### E2E Test Patterns

```typescript
import { test, expect, Page } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test('should register a new user successfully', async ({ page }) => {
    await page.goto('/register');

    // Fill form
    await page.fill('[name="email"]', 'newuser@example.com');
    await page.fill('[name="password"]', 'SecurePassword123!');
    await page.fill('[name="confirmPassword"]', 'SecurePassword123!');

    // Submit
    await page.click('button[type="submit"]');

    // Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('.welcome-message')).toContainText('Welcome');
  });

  test('should show error for duplicate email', async ({ page }) => {
    // Create user first
    await page.goto('/register');
    await page.fill('[name="email"]', 'existing@example.com');
    await page.fill('[name="password"]', 'Password123!');
    await page.fill('[name="confirmPassword"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Logout
    await page.click('[data-testid="logout"]');

    // Try to register again
    await page.goto('/register');
    await page.fill('[name="email"]', 'existing@example.com');
    await page.fill('[name="password"]', 'Password123!');
    await page.fill('[name="confirmPassword"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Verify error
    await expect(page.locator('.error-message')).toContainText('already exists');
  });
});

// Page Object Model
class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.fill('[name="email"]', email);
    await this.page.fill('[name="password"]', password);
    await this.page.click('button[type="submit"]');
  }

  async expectError(message: string) {
    await expect(this.page.locator('.error')).toContainText(message);
  }
}

test('should login with valid credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password123');
  await expect(page).toHaveURL(/\/dashboard/);
});
```

## Mutation Testing

### Configuration

```javascript
// stryker.conf.js
module.exports = {
  mutator: 'typescript',
  packageManager: 'npm',
  reporters: ['html', 'clear-text', 'progress'],
  testRunner: 'jest',
  coverageAnalysis: 'off',

  mutate: {
    include: ['src/**/*.ts'],
    exclude: ['src/**/*.spec.ts', 'src/**/*.test.ts']
  },

  thresholds: {
    high: 80,
    low: 60,
    break: 70
  }
};
```

### Mutation Testing Concepts

```typescript
// Original code
function calculateDiscount(price: number, memberLevel: string): number {
  if (memberLevel === 'gold') {
    return price * 0.8;  // 20% discount
  }
  if (memberLevel === 'silver') {
    return price * 0.9;  // 10% discount
  }
  return price;  // No discount
}

// Tests that should catch mutations
describe('calculateDiscount', () => {
  it('should give 20% discount for gold members', () => {
    expect(calculateDiscount(100, 'gold')).toBe(80);  // Catches price * 0.9
  });

  it('should give 10% discount for silver members', () => {
    expect(calculateDiscount(100, 'silver')).toBe(90);  // Catches price * 0.8
  });

  it('should give no discount for regular members', () => {
    expect(calculateDiscount(100, 'regular')).toBe(100);  // Catches early returns
  });

  it('should handle edge cases', () => {
    expect(calculateDiscount(0, 'gold')).toBe(0);  // Catches division issues
    expect(calculateDiscount(100, 'unknown')).toBe(100);  // Catches default handling
  });
});
```

## Test Coverage

### Coverage Configuration

```typescript
// Coverage thresholds
const coverageConfig = {
  global: {
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80
  },
  './src/services/': {
    branches: 90,  // Higher for critical services
    functions: 90,
    lines: 90,
    statements: 90
  },
  './src/utils/': {
    branches: 100,  // 100% for utilities
    functions: 100,
    lines: 100,
    statements: 100
  }
};

// Coverage reporters
const reporters = [
  'text',           // Console output
  'lcov',           // For SonarQube
  'html',           // Visual report
  'json-summary',   // For badges
  'json'            // For CI
];
```

### Coverage Analysis

```typescript
// Script to analyze coverage gaps
interface CoverageGap {
  file: string;
  line: number;
  type: 'branch' | 'statement' | 'function';
  description: string;
}

async function analyzeCoverageGaps(
  coverageReport: CoverageReport
): Promise<CoverageGap[]> {
  const gaps: CoverageGap[] = [];

  for (const [file, coverage] of Object.entries(coverageReport)) {
    // Find uncovered branches
    for (const branch of coverage.branches) {
      if (!branch.covered) {
        gaps.push({
          file,
          line: branch.line,
          type: 'branch',
          description: `Uncovered branch at line ${branch.line}`
        });
      }
    }

    // Find uncovered functions
    for (const fn of coverage.functions) {
      if (!fn.covered) {
        gaps.push({
          file,
          line: fn.line,
          type: 'function',
          description: `Uncovered function: ${fn.name}`
        });
      }
    }
  }

  return gaps.sort((a, b) => a.file.localeCompare(b.file));
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Testing Library](https://testing-library.com/)
- [Stryker Mutator](https://stryker-mutator.io/)
- [Martin Fowler on TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
