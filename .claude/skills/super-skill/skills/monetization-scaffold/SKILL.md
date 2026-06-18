---
name: monetization-scaffold
description: IdeaForge V4.0 / Phase 11. Generate a deploy-ready, billable scaffold (Dockerfile, docker-compose, Stripe Checkout+webhook+tiers, CI/CD, .env template, one-command deploy) from the BUSINESS_MODEL pricing. Use at deployment so CC's output is "deploy → billable", not "MVP, monetize later".
---

# monetization-scaffold — Deploy-Ready + Billable, by Construction

Operationalizes the user's Insight 3: **"变现就绪前置到设计阶段，而非开发后补足"**. The pricing decided in `BUSINESS_MODEL.md` becomes real Stripe tiers the moment the code is scaffolded — no separate "add billing later" phase.

## What it generates

Given a manifest (`product_name`, `stack ∈ {node,python,static}`, `deploy_target ∈ {vercel,railway,fly}`, `tiers[]`, `currency`), `render.py` writes:

```
Dockerfile                      # stack-specific (node/python/static)
docker-compose.yml              # app + postgres
.env.example                    # Stripe keys, DB url, deploy target creds
.gitignore
stripe/tiers.json               # the pricing, machine-readable (from BUSINESS_MODEL)
stripe/server.js                # Checkout session creator + webhook verifier
stripe/checkout.html            # tier buttons → /create-checkout-session
.github/workflows/ci.yml        # build+test+deploy on push to main
deploy.sh                       # one-command deploy (vercel/railway/flyctl)
```

## How to run

```bash
# manifest.json mirrors BUSINESS_MODEL.md pricing
python scripts/render.py manifest.json ./scaffold-out
```

The LLM derives `manifest.json` from `BUSINESS_MODEL.md` (product name, stack from ARCHITECTURE, tiers from the pricing table, deploy target from the deployment decision).

## Honesty / boundary

- **Generates a scaffold + one-command deploy script** the user runs with **their own** Stripe keys + cloud credentials.
- Does **not** deploy or handle live payments itself — it doesn't hold secrets and shouldn't.

## Files

- [scripts/render.py](scripts/render.py) — renderer (stdlib-only, idempotent)
- [scripts/test_render.py](scripts/test_render.py) — 8 tests, all green

## Integration

- **Consumes**: [proposal-forge](../proposal-forge/SKILL.md) `BUSINESS_MODEL.md` (pricing/tiers)
- **Part of**: Phase 11 (Deployment) enhancement — output is SaaS-ready
