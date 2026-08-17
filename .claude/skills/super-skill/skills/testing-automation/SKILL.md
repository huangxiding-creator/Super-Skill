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

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `E2E Testing with Playwright`, `Mutation Testing`, `Test Coverage`, `Version History`, `References`.
