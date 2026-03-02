---
name: testing-automation
description: Comprehensive testing automation including unit tests, integration tests, E2E tests, and mutation testing. Provides TDD workflows, test generation, and coverage analysis.
tags: [testing, tdd, e2e, mutation, coverage, playwright, jest]
version: 1.0.0
source: Based on Jest, Playwright, PITest, and industry testing best practices
integrated-with: super-skill v3.7+
---

# Testing Automation Skill

This skill provides comprehensive testing automation capabilities including unit tests, integration tests, E2E tests, mutation testing, and test-driven development workflows.

## Testing Pyramid

```
┌─────────────────────────────────────────────────────────────────┐
│                     TESTING PYRAMID                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                          E2E Tests                              │
│                        ┌─────────┐                              │
│                        │  10%    │  • Full user journeys       │
│                        │         │  • Browser automation       │
│                        └─────────┘  • Slow, expensive          │
│                                                                  │
│                    Integration Tests                            │
│                  ┌───────────────────┐                          │
│                  │       20%         │  • API endpoints         │
│                  │                   │  • Database operations   │
│                  └───────────────────┘  • External services     │
│                                                                  │
│                        Unit Tests                               │
│              ┌───────────────────────────────┐                  │
│              │            70%                │  • Functions     │
│              │                               │  • Components    │
│              └───────────────────────────────┘  • Fast, isolated│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Unit Testing

### Jest Configuration

```typescript
// jest.config.ts
import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',

  // Coverage settings
  collectCoverage: true,
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  coverageReporters: ['text', 'lcov', 'html'],

  // Test patterns
  testMatch: ['**/__tests__/**/*.test.ts', '**/*.spec.ts'],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { useESM: true }]
  },

  // Setup files
  setupFilesAfterEnv: ['./jest.setup.ts'],

  // Performance
  maxWorkers: '50%',
  testTimeout: 10000
};

export default config;
```

### Test Patterns

```typescript
// Test structure: AAA (Arrange, Act, Assert)
describe('UserService', () => {
  describe('createUser', () => {
    it('should create a user with valid data', async () => {
      // Arrange
      const mockRepo = {
        create: jest.fn().mockResolvedValue({ id: '1', email: 'test@example.com' })
      };
      const service = new UserService(mockRepo);
      const input = { email: 'test@example.com', name: 'Test User' };

      // Act
      const result = await service.createUser(input);

      // Assert
      expect(result).toEqual({
        id: '1',
        email: 'test@example.com'
      });
      expect(mockRepo.create).toHaveBeenCalledWith(input);
    });

    it('should throw ValidationError for invalid email', async () => {
      // Arrange
      const service = new UserService(mockRepo);
      const input = { email: 'invalid-email', name: 'Test' };

      // Act & Assert
      await expect(service.createUser(input))
        .rejects.toThrow(ValidationError);
    });
  });
});

// Parameterized tests
describe('EmailValidator', () => {
  const testCases = [
    { email: 'valid@example.com', expected: true },
    { email: 'invalid', expected: false },
    { email: 'no@domain', expected: false },
    { email: 'user@sub.domain.com', expected: true }
  ];

  test.each(testCases)(
    'should return $expected for $email',
    ({ email, expected }) => {
      expect(isValidEmail(email)).toBe(expected);
    }
  );
});

// Mocking patterns
jest.mock('../lib/external-api', () => ({
  fetchData: jest.fn()
}));

// Spy patterns
it('should call logger with correct message', () => {
  const loggerSpy = jest.spyOn(logger, 'info');

  service.doSomething();

  expect(loggerSpy).toHaveBeenCalledWith('Operation completed');
});
```

### React Testing

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('should render login form', () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('should submit form with valid data', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  it('should show validation errors', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={mockOnSubmit} />);

    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });
});
```

## Integration Testing

### API Testing

```typescript
import request from 'supertest';
import app from '../app';
import { setupTestDB, teardownTestDB } from './setup';

describe('User API', () => {
  beforeAll(async () => {
    await setupTestDB();
  });

  afterAll(async () => {
    await teardownTestDB();
  });

  describe('GET /api/users', () => {
    it('should return list of users', async () => {
      const response = await request(app)
        .get('/api/users')
        .set('Accept', 'application/json')
        .expect('Content-Type', /json/)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should support pagination', async () => {
      const response = await request(app)
        .get('/api/users')
        .query({ page: 2, limit: 10 })
        .expect(200);

      expect(response.body.meta.pagination.page).toBe(2);
    });
  });

  describe('POST /api/users', () => {
    it('should create a new user', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'new@example.com',
          name: 'New User'
        })
        .expect(201);

      expect(response.body.data.email).toBe('new@example.com');
    });

    it('should reject invalid email', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'invalid',
          name: 'Test'
        })
        .expect(400);

      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });
  });
});
```

### Database Testing

```typescript
import { PrismaClient } from '@prisma/client';
import { UserService } from '../services/user.service';

describe('UserService Integration', () => {
  let prisma: PrismaClient;
  let userService: UserService;

  beforeAll(() => {
    prisma = new PrismaClient({
      datasources: {
        db: { url: process.env.TEST_DATABASE_URL }
      }
    });
    userService = new UserService(prisma);
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    // Clean database before each test
    await prisma.user.deleteMany();
  });

  it('should create and retrieve user', async () => {
    const created = await userService.create({
      email: 'test@example.com',
      name: 'Test User'
    });

    const found = await userService.findById(created.id);

    expect(found).toEqual(created);
  });

  it('should enforce unique email', async () => {
    await userService.create({
      email: 'test@example.com',
      name: 'Test User'
    });

    await expect(
      userService.create({
        email: 'test@example.com',
        name: 'Another User'
      })
    ).rejects.toThrow();
  });
});
```

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

## TDD Workflow

### Red-Green-Refactor

```markdown
## TDD Cycle

### 1. RED - Write failing test
```typescript
describe('PasswordValidator', () => {
  it('should require at least 8 characters', () => {
    const result = validatePassword('short');
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Password must be at least 8 characters');
  });
});
```

### 2. GREEN - Write minimal code to pass
```typescript
function validatePassword(password: string): ValidationResult {
  if (password.length < 8) {
    return {
      valid: false,
      errors: ['Password must be at least 8 characters']
    };
  }
  return { valid: true, errors: [] };
}
```

### 3. REFACTOR - Improve code quality
```typescript
const MIN_PASSWORD_LENGTH = 8;

function validatePassword(password: string): ValidationResult {
  const errors: string[] = [];

  if (password.length < MIN_PASSWORD_LENGTH) {
    errors.push(`Password must be at least ${MIN_PASSWORD_LENGTH} characters`);
  }

  return {
    valid: errors.length === 0,
    errors
  };
}
```

### 4. REPEAT - Add more tests
```typescript
it('should require at least one uppercase letter', () => {
  const result = validatePassword('alllowercase');
  expect(result.valid).toBe(false);
});
```
```

## Integration with Super-Skill

### Phase Integration

```yaml
testing_phase_mapping:
  phase_8_development:
    actions:
      - write_unit_tests_tdd
      - implement_code_to_pass_tests
      - refactor_with_test_coverage

  phase_9_qa:
    actions:
      - run_full_test_suite
      - analyze_coverage_gaps
      - run_mutation_tests
      - execute_e2e_tests

  phase_10_optimization:
    actions:
      - optimize_slow_tests
      - improve_mutation_score
      - increase_coverage
```

## Best Practices Checklist

### Unit Tests
- [ ] Tests are isolated
- [ ] Mocks are appropriate
- [ ] Edge cases covered
- [ ] Tests are readable
- [ ] Coverage > 80%

### Integration Tests
- [ ] Database cleaned between tests
- [ ] External services mocked
- [ ] Tests are repeatable
- [ ] Environment isolated

### E2E Tests
- [ ] Critical flows covered
- [ ] Page objects used
- [ ] Retries configured
- [ ] Screenshots on failure

### Mutation Testing
- [ ] Mutation score > 70%
- [ ] All mutants analyzed
- [ ] Edge case tests added

## Deliverables

- Test suite configuration
- Unit tests with > 80% coverage
- Integration tests
- E2E tests for critical flows
- Mutation testing report

---

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
