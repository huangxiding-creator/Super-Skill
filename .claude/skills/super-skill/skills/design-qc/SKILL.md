---
name: design-qc
description: Automated visual regression testing with sectioned screenshot capture and AI-powered UI evaluation. Auto-detects dev server, captures screenshots across viewports and routes, estimates token cost per screenshot.
---

# Design QC: Visual Regression Testing

Inspired by [OpenWolf](https://github.com/cytostack/openwolf) design QC system. Automated screenshot capture and AI-powered UI evaluation.

## When to Use

- After UI changes (Phase 8 development)
- During QA testing (Phase 9)
- Before deployment (Phase 11)
- After CSS/style changes (Phase 10 optimization)

## When NOT to Use

- Backend-only projects
- API-only services
- Library/package development
- Projects without a dev server

## How It Works

### Step 1: Dev Server Detection

Auto-detect running dev servers on common ports:

| Port | Framework |
|------|-----------|
| 3000 | Next.js, CRA |
| 5173 | Vite |
| 8080 | Webpack, Go |
| 4200 | Angular |
| 8000 | Django, Python |
| 4000 | GraphQL, Remix |
| 4173 | Vite preview |

If no server found, attempts to start from `package.json` scripts:
- `npm run dev` / `yarn dev` / `pnpm dev` / `bun dev`
- 30-second readiness timeout with polling

### Step 2: Route Detection

Auto-detect routes from project structure:

| Directory | Framework | Route Source |
|-----------|-----------|-------------|
| `pages/` | Next.js Pages | File-based routing |
| `app/` | Next.js App | File-based routing |
| `src/routes/` | Remix, SvelteKit | File-based routing |
| `src/pages/` | CRA, Gatsby | React Router |

Falls back to: `/` (homepage only)

### Step 3: Sectioned Screenshot Capture

Instead of one massive screenshot, captures viewport-height sections:

```
Page (3000px total height)
├── Section 1 (0px - 900px)    → ~2500 tokens
├── Section 2 (900px - 1800px) → ~2500 tokens
└── Section 3 (1800px - 2700px)→ ~2500 tokens

Max 8 sections per route (20,000 tokens max)
```

### Step 4: Multi-Viewport Capture

| Viewport | Dimensions | Purpose |
|----------|------------|---------|
| Desktop | 1280×800 | Primary layout |
| Tablet | 768×1024 | Responsive breakpoint |
| Mobile | 375×812 | Mobile layout |

### Step 5: AI Evaluation

Each screenshot is evaluated for:

| Criteria | Weight | Check |
|----------|--------|-------|
| Layout integrity | 30% | Elements positioned correctly |
| Visual consistency | 25% | Consistent spacing, fonts, colors |
| Responsiveness | 20% | Proper adaptation to viewport |
| Content clarity | 15% | Readable text, proper hierarchy |
| Accessibility basics | 10% | Contrast, visible focus states |

### Output Format

Screenshots saved to `.claude/designqc-report.json`:

```json
{
  "timestamp": "2026-05-06T12:00:00Z",
  "url": "http://localhost:3000",
  "routes": ["/", "/dashboard", "/settings"],
  "viewports": ["desktop", "tablet", "mobile"],
  "screenshots": [
    {
      "route": "/",
      "viewport": "desktop",
      "sections": 3,
      "tokens_estimated": 7500,
      "issues": ["Header overlaps on mobile viewport"]
    }
  ],
  "summary": {
    "total_screenshots": 9,
    "total_tokens": 22500,
    "issues_found": 1,
    "severity": "low"
  }
}
```

## Hook Integration

### Post-Write Hook (CSS/UI files only)
When editing `.css`, `.scss`, `.tsx`, `.jsx` files with style changes:
1. Check if dev server is running
2. If running, capture screenshot of affected route
3. Compare with previous capture
4. Flag visual regressions

### Stop Hook
1. If UI files were edited during session
2. Run full Design QC scan
3. Include results in session summary

## Phase Integration

| Phase | Design QC Action |
|-------|-----------------|
| Phase 8 | Post-write screenshots for UI changes |
| Phase 9 | Full visual regression scan |
| Phase 10 | Before/after optimization comparison |
| Phase 11 | Pre-deployment visual verification |

## Token Budget

| Scenario | Routes | Viewports | Sections | Total Tokens |
|----------|--------|-----------|----------|-------------|
| Quick check | 1 | 1 | 2 | ~5,000 |
| Standard | 3 | 2 | 3 | ~45,000 |
| Comprehensive | 5+ | 3 | 4 | ~150,000 |

**Recommendation**: Use quick check during development, standard for QA, comprehensive before deployment.

## Rules

1. **Max 8 sections per route** — hard limit to prevent token overflow
2. **Max 5 routes per scan** — unless explicitly requested
3. **Desktop-first** — always capture desktop, optional tablet/mobile
4. **Screenshots are ephemeral** — don't persist full images, only metadata
5. **Dev server must be running** — can't start if port conflicts exist
6. **Estimate tokens before capture** — warn if budget exceeds 50,000 tokens
