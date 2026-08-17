---
name: accessibility-a11y
description: WCAG accessibility compliance patterns and testing. Covers semantic HTML, ARIA attributes, keyboard navigation, screen reader support, and accessibility testing automation.
tags: [accessibility, a11y, wcag, aria, screen-reader]
version: 1.0.0
source: Based on WCAG 2.1, WAI-ARIA, Deque axe-core best practices
integrated-with: super-skill v3.7+
---
# Accessibility (A11y) Skill

This skill provides comprehensive WCAG accessibility compliance patterns, covering semantic HTML, ARIA attributes, keyboard navigation, screen reader support, and automated testing.

## WCAG Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                 WCAG 2.1 PRINCIPLES (POUR)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PERCEIVABLE                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Alt text for images    • Color contrast              │    │
│  │ • Captions for video     • No audio-only content       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  OPERABLE                                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Keyboard navigation    • Sufficient time             │    │
│  │ • No seizure triggers    • Skip navigation links       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  UNDERSTANDABLE                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Readable content       • Predictable behavior        │    │
│  │ • Input assistance       • Error identification        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ROBUST                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Valid HTML             • Compatible with AT          │    │
│  │ • ARIA landmarks         • Name, Role, Value           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Semantic HTML

### Proper Document Structure

```html
<!-- Page structure with landmarks -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Page Title | Site Name</title>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header role="banner">
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="/" aria-current="page">Home</a></li>
        <li><a href="/about">About</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
    </nav>
  </header>

  <main id="main-content" role="main">
    <h1>Page Heading</h1>

    <section aria-labelledby="section-heading">
      <h2 id="section-heading">Section Heading</h2>
      <!-- Content -->
    </section>

    <aside role="complementary" aria-label="Related links">
      <!-- Sidebar content -->
    </aside>
  </main>

  <footer role="contentinfo">
    <p>&copy; 2026 Site Name. All rights reserved.</p>
  </footer>
</body>
</html>
```

### Accessible Forms

```html
<!-- Form with proper labels and error handling -->
<form aria-labelledby="form-title" novalidate>
  <h2 id="form-title">Create Account</h2>

  <!-- Text input with label -->
  <div class="form-group">
    <label for="email">
      Email <span aria-hidden="true">*</span>
      <span class="visually-hidden">required</span>
    </label>
    <input
      type="email"
      id="email"
      name="email"
      required
      aria-required="true"
      aria-describedby="email-error email-hint"
      autocomplete="email"
    >
    <p id="email-hint" class="hint">
      We'll never share your email.
    </p>
    <p id="email-error" class="error" role="alert" aria-live="polite">
      <!-- Error message injected here -->
    </p>
  </div>

  <!-- Password with requirements -->
  <div class="form-group">
    <label for="password">Password <span aria-hidden="true">*</span></label>
    <input
      type="password"
      id="password"
      name="password"
      required
      aria-required="true"
      aria-describedby="password-requirements"
      autocomplete="new-password"
    >
    <ul id="password-requirements" class="requirements">
      <li>At least 8 characters</li>
      <li>One uppercase letter</li>
      <li>One number</li>
    </ul>
  </div>

  <!-- Checkbox with description -->
  <div class="form-group">
    <input type="checkbox" id="terms" name="terms" required aria-required="true">
    <label for="terms">
      I agree to the <a href="/terms">Terms of Service</a>
    </label>
  </div>

  <!-- Radio group -->
  <fieldset>
    <legend>Preferred contact method</legend>
    <div class="radio-group" role="radiogroup" aria-labelledby="contact-legend">
      <input type="radio" id="contact-email" name="contact" value="email" checked>
      <label for="contact-email">Email</label>

      <input type="radio" id="contact-phone" name="contact" value="phone">
      <label for="contact-phone">Phone</label>

      <input type="radio" id="contact-mail" name="contact" value="mail">
      <label for="contact-mail">Mail</label>
    </div>
  </fieldset>

  <button type="submit">Create Account</button>
</form>
```

## ARIA Patterns

### Custom Components

```tsx
// Accessible Modal Dialog
function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocus.current = document.activeElement as HTMLElement;
      modalRef.current?.focus();
      document.body.style.overflow = 'hidden';
    } else {
      previousFocus.current?.focus();
      document.body.style.overflow = '';
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
      ref={modalRef}
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key === 'Escape') onClose();
      }}
    >
      <div className="modal-backdrop" onClick={onClose} aria-hidden="true" />

      <div className="modal-content">
        <h2 id="modal-title">{title}</h2>
        <div id="modal-description">{children}</div>
        <button onClick={onClose} aria-label="Close dialog">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    </div>
  );
}

// Accessible Tabs
function Tabs({ tabs, defaultTab = 0 }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    let newIndex = index;

    switch (e.key) {
      case 'ArrowLeft':
        newIndex = index === 0 ? tabs.length - 1 : index - 1;
        break;
      case 'ArrowRight':
        newIndex = index === tabs.length - 1 ? 0 : index + 1;
        break;
      case 'Home':
        newIndex = 0;
        break;
      case 'End':
        newIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    e.preventDefault();
    setActiveTab(newIndex);
    tabRefs.current[newIndex]?.focus();
  };

  return (
    <div className="tabs">
      <div role="tablist" aria-label="Content sections">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(el) => { tabRefs.current[index] = el; }}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={activeTab === index}
            aria-controls={`panel-${tab.id}`}
            tabIndex={activeTab === index ? 0 : -1}
            onClick={() => setActiveTab(index)}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab, index) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={activeTab !== index}
          tabIndex={0}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}

// Accessible Dropdown Menu
function DropdownMenu({ trigger, items }: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(0);
  const menuRef = useRef<HTMLUListElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusIndex((prev) => (prev + 1) % items.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusIndex((prev) => (prev - 1 + items.length) % items.length);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        items[focusIndex].onClick();
        setIsOpen(false);
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div className="dropdown">
      <button
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
      >
        {trigger}
      </button>

      {isOpen && (
        <ul
          ref={menuRef}
          role="menu"
          onKeyDown={handleKeyDown}
          onBlur={() => setIsOpen(false)}
        >
          {items.map((item, index) => (
            <li role="none" key={item.id}>
              <button
                role="menuitem"
                tabIndex={index === focusIndex ? 0 : -1}
                onClick={item.onClick}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

## Integration with Super-Skill

### Phase Integration

```yaml
a11y_phase_mapping:
  phase_5_design:
    outputs:
      - accessibility_requirements
      - color_contrast_report

  phase_8_development:
    actions:
      - implement_aria_patterns
      - add_keyboard_navigation
      - create_accessible_forms

  phase_9_qa:
    actions:
      - run_automated_a11y_tests
      - perform_keyboard_testing
      - screen_reader_testing
```

## Checklist

### Content
- [ ] All images have alt text
- [ ] Headings are properly nested
- [ ] Links have descriptive text
- [ ] Color is not sole indicator

### Navigation
- [ ] Skip links present
- [ ] Logical tab order
- [ ] Focus visible
- [ ] Focus trapped in modals

### Forms
- [ ] All inputs have labels
- [ ] Error messages linked
- [ ] Required fields marked
- [ ] Instructions provided

### Testing
- [ ] Automated a11y tests pass
- [ ] Keyboard navigation works
- [ ] Screen reader tested
- [ ] Color contrast verified

## Deliverables

- Accessible component library
- A11y test suite
- WCAG compliance report
- Screen reader testing guide

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `Keyboard Navigation`, `Automated Testing`, `Version History`, `References`.
