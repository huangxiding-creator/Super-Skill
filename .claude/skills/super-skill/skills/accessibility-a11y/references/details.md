# accessibility-a11y — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## Keyboard Navigation

### Focus Management

```css
/* Visible focus indicator */
:focus {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

:focus:not(:focus-visible) {
  outline: none;
}

:focus-visible {
  outline: 2px solid #007bff;
  outline-offset: 2px;
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -100px;
  left: 0;
  padding: 1rem;
  background: #007bff;
  color: white;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}

/* Visually hidden but accessible */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus trap container */
.focus-trap:focus {
  outline: none;
}
```

### Focus Trap Implementation

```typescript
function useFocusTrap(containerRef: RefObject<HTMLElement>, isActive: boolean) {
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    firstElement?.focus();

    return () => container.removeEventListener('keydown', handleKeyDown);
  }, [isActive, containerRef]);
}
```

## Automated Testing

### Jest + axe-core

```typescript
import { configureAxe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

// Configure axe for tests
const axe = configureAxe({
  rules: {
    // Disable specific rules if needed
    'color-contrast': { enabled: false }
  }
});

describe('Accessibility Tests', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<MyComponent />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('form should be accessible', async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container, {
      rules: {
        'label': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });
});
```

### Playwright Accessibility Tests

```typescript
import { test, expect } from '@playwright/test';

test.describe('Accessibility', () => {
  test('homepage should be accessible', async ({ page }) => {
    await page.goto('/');

    // Run axe accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('keyboard navigation should work', async ({ page }) => {
    await page.goto('/');

    // Tab through focusable elements
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Home' })).toBeFocused();

    // Test skip link
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    await expect(page.getByRole('main')).toBeFocused();
  });

  test('modal should trap focus', async ({ page }) => {
    await page.goto('/');
    await page.click('button[aria-label="Open dialog"]');

    // Verify modal is open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Verify focus is trapped
    const modal = page.getByRole('dialog');
    const focusableCount = await modal.locator('button, [href], input, select, textarea').count();

    for (let i = 0; i < focusableCount + 2; i++) {
      await page.keyboard.press('Tab');
    }

    // Focus should still be within modal
    await expect(page.getByRole('dialog')).toContainText(
      await page.evaluate(() => document.activeElement?.textContent || '')
    );
  });
});
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)
- [Deque University](https://dequeuniversity.com/)
