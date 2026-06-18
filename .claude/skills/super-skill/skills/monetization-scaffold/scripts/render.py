"""Monetization scaffold renderer (IdeaForge / Super-Skill V4.0).

Turns the pricing/tiers from BUSINESS_MODEL.md into a deploy-ready, billable
scaffold: Dockerfile, docker-compose, Stripe Checkout (+webhook+tiers), CI/CD,
env template, and a one-command deploy script. Operationalizes the user's
Insight 3 ("变现就绪前置到设计阶段").

Pure-stdlib, no network. ``render(manifest, out_dir)`` writes files and returns
the list of paths. Idempotent: overwrites.
"""
from __future__ import annotations

import json
import os
import stat
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Mapping, Sequence

SUPPORTED_STACKS = ("node", "python", "static")
SUPPORTED_TARGETS = ("vercel", "railway", "fly")


@dataclass(frozen=True)
class Tier:
    name: str
    price: float          # 0 = free
    currency: str = "usd"
    interval: str = "month"   # month | year | one_time
    limits: str = ""

    @property
    def is_free(self) -> bool:
        return self.price <= 0


@dataclass
class Manifest:
    product_name: str
    stack: str = "node"              # node | python | static
    deploy_target: str = "vercel"    # vercel | railway | fly
    tiers: List[Tier] = field(default_factory=list)
    webhook_port: int = 4242
    currency: str = "usd"

    def validate(self) -> None:
        if self.stack not in SUPPORTED_STACKS:
            raise ValueError(f"stack must be one of {SUPPORTED_STACKS}")
        if self.deploy_target not in SUPPORTED_TARGETS:
            raise ValueError(f"deploy_target must be one of {SUPPORTED_TARGETS}")
        if not self.tiers:
            raise ValueError("at least one tier required (use a free tier if needed)")


def _env_template(m: Manifest) -> str:
    return f"""# Monetization-ready env (fill before deploy)
# --- App ---
PRODUCT_NAME="{m.product_name}"
PORT={m.webhook_port}
NODE_ENV=production

# --- Stripe (get from https://dashboard.stripe.com/apikeys) ---
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_CURRENCY={m.currency}

# --- Database ---
DATABASE_URL=postgresql://user:pass@localhost:5432/{m.product_name.lower().replace(' ','_')}

# --- Deploy target: {m.deploy_target} ---
{(_VERCEL_ENV if m.deploy_target=='vercel' else _RAILWAY_ENV if m.deploy_target=='railway' else _FLY_ENV)}
"""


_VIMAL = ""
_VERCEL_ENV = "# VERCEL_PROJECT_ID=prj_xxx\n# VERCEL_ORG_ID=team_xxx\n# VERCEL_TOKEN=ptk_xxx"
_RAILWAY_ENV = "# RAILWAY_TOKEN=rlw_xxx\n# RAILWAY_SERVICE_ID=svc_xxx"
_FLY_ENV = "# FLY_API_TOKEN=FlyV1_xxx\n# FLY_APP_NAME="


def _dockerfile(m: Manifest) -> str:
    if m.stack == "python":
        return _DOCKERFILE_PY
    if m.stack == "static":
        return _DOCKERFILE_STATIC
    return _DOCKERFILE_NODE


_DOCKERFILE_NODE = """\
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev || npm install
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 4242
CMD ["node", "server.js"]
"""

_DOCKERFILE_PY = """\
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 4242
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "4242"]
"""

_DOCKERFILE_STATIC = """\
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""


def _docker_compose(m: Manifest) -> str:
    return f"""services:
  app:
    build: .
    ports:
      - "{m.webhook_port}:{m.webhook_port}"
    env_file: .env
    depends_on: [db]
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: {m.product_name.lower().replace(' ', '_')}
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes: [pgdata:/var/lib/postgresql/data]
volumes:
  pgdata:
"""


def _stripe_tiers(m: Manifest) -> str:
    """Emit a tiers config the Stripe integration reads (price → tier)."""
    out = []
    for t in m.tiers:
        out.append({
            "name": t.name,
            "price": t.price,
            "currency": t.currency,
            "interval": t.interval,
            "limits": t.limits,
            "is_free": t.is_free,
        })
    return json.dumps({"product": m.product_name, "currency": m.currency, "tiers": out},
                      ensure_ascii=False, indent=2)


def _stripe_server(m: Manifest) -> str:
    return """\
// Stripe Checkout + webhook handler (Node, Stripe SDK). Reads tiers from tiers.json.
const Stripe = require('stripe');
const express = require('express');
const tiers = require('./tiers.json');

const app = express();
app.use(express.json());

// Stripe needs the raw body to verify the webhook signature.
app.post('/webhook', express.raw({type: 'application/json'}),
  (req, res) => {
    const sig = req.headers['stripe-signature'];
    let event;
    try {
      event = Stripe(process.env.STRIPE_SECRET_KEY).webhooks.constructEvent(
        req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
    } catch (err) {
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }
    // Handle: checkout.session.completed, customer.subscription.updated/deleted
    console.log('stripe event', event.type, event.id);
    // TODO: provision/deprovision the customer's tier in your DB.
    res.json({received: true});
  });

app.post('/create-checkout-session', express.json(), async (req, res) => {
  const tierName = req.body.tier;
  const tier = tiers.tiers.find(t => t.name === tierName);
  if (!tier || tier.is_free) return res.status(400).json({error: 'invalid tier'});
  const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
  const session = await stripe.checkout.sessions.create({
    mode: tier.interval === 'one_time' ? 'payment' : 'subscription',
    line_items: [{price_data: {
      currency: tier.currency, unit_amount: Math.round(tier.price * 100),
      product_data: {name: `${tiers.product} — ${tier.name}`},
      recurring: tier.interval === 'one_time' ? undefined : {interval: tier.interval},
    }, quantity: 1}],
    success_url: `${req.headers.origin}/?paid=${tier.name}`,
    cancel_url: `${req.headers.origin}/?canceled=1`,
  });
  res.json({url: session.url});
});

app.listen(process.env.PORT || 4242, () => console.log('billing on', process.env.PORT || 4242));
"""


def _checkout_html(m: Manifest) -> str:
    buttons = "\n".join(
        f'    <button onclick="buy(\'{t.name}\')">{t.name} — {("$"+str(t.price)) if not t.is_free else "Free"}{("/"+t.interval) if not t.is_free and t.interval!="one_time" else ""}</button>'
        for t in m.tiers
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{m.product_name} — Billing</title></head>
<body>
  <h1>{m.product_name}</h1>
  <div id="tiers">
{buttons}
  </div>
  <p id="msg"></p>
  <script>
    async function buy(tier) {{
      const r = await fetch('/create-checkout-session', {{method:'POST',
        headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{tier}})}});
      const {{url, error}} = await r.json();
      if (url) window.location = url; else document.getElementById('msg').textContent = error || 'failed';
    }}
  </script>
</body></html>
"""


def _ci_workflow(m: Manifest) -> str:
    return f"""name: CI + Deploy
on:
  push: {{branches: [main]}}
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {{node-version: '20'}}
      - run: npm ci
      - run: npm test --if-present
      - run: npm run build --if-present
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to {m.deploy_target}
        run: ./deploy.sh
        env:
          {('VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}' if m.deploy_target=='vercel' else 'RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}' if m.deploy_target=='railway' else 'FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}')}
"""


def _deploy_script(m: Manifest) -> str:
    if m.deploy_target == "vercel":
        body = (
            'npx vercel link --yes --token "$VERCEL_TOKEN"\n'
            'npx vercel pull --yes --token "$VERCEL_TOKEN"\n'
            'npx vercel build --prod --token "$VERCEL_TOKEN"\n'
            'npx vercel deploy --prebuilt --prod --token "$VERCEL_TOKEN"\n'
        )
    elif m.deploy_target == "railway":
        body = (
            'railway up --service "$RAILWAY_SERVICE_ID"\n'
        )
    else:  # fly
        body = (
            'flyctl deploy --app "${{FLY_APP_NAME:-}}" --token "$FLY_API_TOKEN" || flyctl deploy\n'
        )
    return f"""#!/usr/bin/env bash
# One-command deploy ({m.deploy_target}). Run AFTER filling .env.
set -e
{body}
echo "Deployed. Wire https://<your-domain>/webhook into Stripe dashboard webhooks."
"""


def render(manifest: Mapping, out_dir: str) -> List[str]:
    """Render the scaffold from a manifest dict. Returns paths written."""
    m = Manifest(
        product_name=str(manifest.get("product_name", "my-product")),
        stack=str(manifest.get("stack", "node")),
        deploy_target=str(manifest.get("deploy_target", "vercel")),
        tiers=[Tier(**t) if isinstance(t, dict) else t for t in manifest.get("tiers", [])],
        webhook_port=int(manifest.get("webhook_port", 4242)),
        currency=str(manifest.get("currency", "usd")),
    )
    m.validate()
    os.makedirs(out_dir, exist_ok=True)
    stripe_dir = os.path.join(out_dir, "stripe")
    wf_dir = os.path.join(out_dir, ".github", "workflows")
    os.makedirs(stripe_dir, exist_ok=True)
    os.makedirs(wf_dir, exist_ok=True)

    files: Dict[str, str] = {
        "Dockerfile": _dockerfile(m),
        "docker-compose.yml": _docker_compose(m),
        ".env.example": _env_template(m),
        ".gitignore": ".env\nnode_modules/\ndist/\n__pycache__/\n",
        "stripe/tiers.json": _stripe_tiers(m),
        "stripe/server.js": _stripe_server(m),
        "stripe/checkout.html": _checkout_html(m),
        ".github/workflows/ci.yml": _ci_workflow(m),
        "deploy.sh": _deploy_script(m),
    }
    written: List[str] = []
    for rel, content in files.items():
        p = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(p)
    # make deploy.sh executable where the FS supports it
    try:
        os.chmod(os.path.join(out_dir, "deploy.sh"), os.stat(os.path.join(out_dir, "deploy.sh")).st_mode | stat.S_IEXEC)
    except OSError:
        pass
    return written


if __name__ == "__main__":
    # CLI: render.py <manifest.json> <out_dir>
    if len(sys.argv) < 3:
        sys.stderr.write("usage: render.py <manifest.json> <out_dir>\n")
        sys.exit(2)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        mf = json.load(f)
    paths = render(mf, sys.argv[2])
    print(json.dumps({"written": [os.path.relpath(p, sys.argv[2]) for p in paths],
                      "count": len(paths)}, ensure_ascii=False, indent=2))
