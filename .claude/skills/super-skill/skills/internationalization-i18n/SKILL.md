---
name: internationalization-i18n
description: Internationalization (i18n) and localization (l10n) patterns for multi-language support. Covers translation management, date/number formatting, RTL support, and locale detection.
tags: [i18n, l10n, internationalization, localization, translation, rtl]
version: 1.0.0
source: Based on i18next, FormatJS, ICU Message Format best practices
integrated-with: super-skill v3.7+
---

# Internationalization (i18n) Skill

This skill provides comprehensive internationalization and localization patterns for building multi-language applications.

## i18n Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               INTERNATIONALIZATION STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRANSLATION MANAGEMENT                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Translation files   • Pluralization    • Interpolation│    │
│  │ • i18next            • FormatJS         • ICU messages  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  FORMATTING                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Date/time          • Numbers          • Currency      │    │
│  │ • Intl API           • FormatJS         • Locale-aware  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  DIRECTION & LAYOUT                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • RTL support        • Text direction    • Mirroring    │    │
│  │ • CSS logical        • Flex/Grid         • Icons        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  LOCALE MANAGEMENT                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Detection          • Fallback         • Negotiation   │    │
│  │ • Browser/URL/Store  • Default locale   • User pref     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## i18next Setup

### Configuration

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ar'],

    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator'],
      caches: ['localStorage', 'cookie'],
      cookieMinutes: 43200, // 30 days
    },

    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    ns: ['common', 'auth', 'dashboard'],
    defaultNS: 'common',

    interpolation: {
      escapeValue: false, // React escapes by default
    },

    react: {
      useSuspense: true,
    },
  });

export default i18n;
```

### Translation Files

```json
// locales/en/common.json
{
  "welcome": "Welcome, {{name}}!",
  "items": {
    "one": "{{count}} item",
    "other": "{{count}} items"
  },
  "notifications": {
    "unread_one": "You have {{count}} unread notification",
    "unread_other": "You have {{count}} unread notifications"
  },
  "actions": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "submit": "Submit"
  },
  "errors": {
    "required": "This field is required",
    "invalid_email": "Please enter a valid email address",
    "password_length": "Password must be at least {{min}} characters"
  },
  "dates": {
    "today": "Today",
    "yesterday": "Yesterday",
    "this_week": "This week",
    "last_week": "Last week"
  }
}

// locales/ar/common.json (RTL language)
{
  "welcome": "مرحباً، {{name}}!",
  "items": {
    "zero": "لا توجد عناصر",
    "one": "{{count}} عنصر",
    "two": "{{count}} عنصرين",
    "few": "{{count}} عناصر",
    "many": "{{count}} عنصر",
    "other": "{{count}} عنصر"
  },
  "actions": {
    "save": "حفظ",
    "cancel": "إلغاء",
    "delete": "حذف",
    "submit": "إرسال"
  }
}
```

### React Usage

```tsx
import { useTranslation, Trans } from 'react-i18next';

function UserProfile({ user }: UserProfileProps) {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div>
      <h1>{t('welcome', { name: user.name })}</h1>

      <p>
        <Trans i18nKey="notifications.unread" count={user.unreadCount}>
          You have {{ count: user.unreadCount }} unread notifications
        </Trans>
      </p>

      <select
        value={i18n.language}
        onChange={(e) => changeLanguage(e.target.value)}
        aria-label={t('language_selector')}
      >
        <option value="en">English</option>
        <option value="es">Español</option>
        <option value="fr">Français</option>
        <option value="ar">العربية</option>
      </select>
    </div>
  );
}

// Pluralization
function CartSummary({ itemCount }: { itemCount: number }) {
  const { t } = useTranslation();

  return (
    <div>
      <p>{t('items', { count: itemCount })}</p>
    </div>
  );
}
```

## Date & Number Formatting

### Intl API

```typescript
// Date formatting
function formatDate(date: Date, locale: string = 'en'): string {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
}

// Relative time
function formatRelativeTime(value: number, unit: Intl.RelativeTimeFormatUnit, locale: string = 'en'): string {
  const formatter = new Intl.RelativeTimeFormat(locale, {
    numeric: 'auto',
  });
  return formatter.format(value, unit);
}

// Number formatting
function formatNumber(number: number, locale: string = 'en'): string {
  return new Intl.NumberFormat(locale).format(number);
}

// Currency formatting
function formatCurrency(
  amount: number,
  currency: string,
  locale: string = 'en'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
}

// Compact number (e.g., 1M, 1K)
function formatCompactNumber(number: number, locale: string = 'en'): string {
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(number);
}

// Usage examples
formatDate(new Date(), 'en');        // "March 2, 2026"
formatDate(new Date(), 'de');        // "2. März 2026"
formatDate(new Date(), 'ja');        // "2026年3月2日"

formatRelativeTime(-1, 'day', 'en'); // "yesterday"
formatRelativeTime(2, 'week', 'es'); // "dentro de 2 semanas"

formatNumber(1234567.89, 'en');      // "1,234,567.89"
formatNumber(1234567.89, 'de');      // "1.234.567,89"

formatCurrency(99.99, 'USD', 'en');  // "$99.99"
formatCurrency(99.99, 'EUR', 'de');  // "99,99 €"
formatCurrency(99.99, 'JPY', 'ja');  // "￥100"

formatCompactNumber(1234567, 'en');  // "1.2M"
```

## RTL Support

### CSS Logical Properties

```css
/* Use logical properties for RTL support */
.container {
  /* Physical (avoid) */
  /* margin-left: 16px; */
  /* padding-right: 24px; */

  /* Logical (prefer) */
  margin-inline-start: 16px;
  padding-inline-end: 24px;

  /* Text alignment */
  text-align: start; /* start/end instead of left/right */

  /* Border radius */
  border-start-start-radius: 8px;
  border-start-end-radius: 8px;
}

/* Flexbox direction */
.flex-container {
  display: flex;
  flex-direction: row; /* Auto-flips in RTL */
  gap: 16px;
}

/* Grid with logical properties */
.grid-container {
  display: grid;
  grid-template-columns: auto 1fr auto;
  justify-items: start;
}
```

### RTL-Specific Styles

```css
/* Component with RTL support */
.card {
  padding: 16px;
  border-radius: 8px;
}

.card-icon {
  margin-inline-end: 12px;
}

.card-arrow {
  /* Arrow that flips direction */
  transform: rotate(0deg);
}

[dir="rtl"] .card-arrow {
  transform: rotate(180deg);
}

/* Icons that shouldn't flip */
.no-flip {
  transform: scaleX(1);
}

[dir="rtl"] .no-flip {
  transform: scaleX(-1);
}
```

### React RTL Detection

```tsx
import { useTranslation } from 'react-i18next';

function useDirection() {
  const { i18n } = useTranslation();
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];

  return {
    isRTL: rtlLanguages.includes(i18n.language),
    dir: rtlLanguages.includes(i18n.language) ? 'rtl' : 'ltr',
  };
}

function App() {
  const { dir } = useDirection();

  return (
    <div dir={dir}>
      <Header />
      <Main />
      <Footer />
    </div>
  );
}
```

## Server-Side i18n

### Next.js Setup

```typescript
// next-i18next.config.js
module.exports = {
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ar'],
    localeDetection: true,
  },
  reloadOnPrerender: process.env.NODE_ENV === 'development',
};

// pages/_app.tsx
import { appWithTranslation } from 'next-i18next';

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}

export default appWithTranslation(MyApp);

// pages/index.tsx
import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';

export const getServerSideProps: GetServerSideProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale ?? 'en', ['common', 'home'])),
    },
  };
};

function HomePage() {
  const { t } = useTranslation('home');

  return (
    <div>
      <h1>{t('title')}</h1>
      <p>{t('description')}</p>
    </div>
  );
}

export default HomePage;
```

## Integration with Super-Skill

### Phase Integration

```yaml
i18n_phase_mapping:
  phase_4_requirements:
    outputs:
      - supported_locales_list
      - translation_requirements

  phase_5_design:
    outputs:
      - translation_file_structure
      - rtl_layout_guidelines

  phase_8_development:
    actions:
      - setup_i18n_framework
      - create_translation_files
      - implement_locale_switcher
      - add_formatting_utilities

  phase_9_qa:
    actions:
      - verify_translations
      - test_rtl_layouts
      - check_formatting
```

## Best Practices Checklist

### Translation
- [ ] All strings externalized
- [ ] Pluralization handled
- [ ] Interpolation used
- [ ] Context variations covered

### Formatting
- [ ] Date formatting locale-aware
- [ ] Number formatting correct
- [ ] Currency symbols right
- [ ] Time zones handled

### RTL Support
- [ ] Logical CSS properties used
- [ ] Layout direction flips
- [ ] Icons mirrored correctly
- [ ] Forms work RTL

## Deliverables

- i18n configuration
- Translation files
- Formatting utilities
- RTL stylesheets

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [i18next Documentation](https://www.i18next.com/)
- [FormatJS](https://formatjs.io/)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
- [MDN Intl API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
