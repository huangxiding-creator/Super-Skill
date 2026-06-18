<!--
BUSINESS_MODEL.md template (IdeaForge / Super-Skill V4.0).
Monetization DNA, front-loaded into design (user Insight 3).
Pricing is DATA-BACKED via pricing.py from competitor prices.
-->
# BUSINESS MODEL: {{product_name}}

## Pricing model
- **Model**: {{subscription|usage|one_time|freemium}} (suggested by positioning "{{positioning}}")
- **Recommended price**: **{{recommended_price}}**
- **Bands (from {{n}} competitors)**: p25 {{p25}} · median {{p50}} · p75 {{p75}}
- **Rationale**: {{pricing_rationale}}

## Tiers (if subscription/SaaS)
| Tier | Price | Limits | Target |
|---|---|---|---|
| Free | ¥0 | {{free_limits}} | hobbyist / trial |
| Pro | {{pro_price}} | {{pro_limits}} | core persona |
| Team | {{team_price}} | {{team_limits}} | small org |

## Acquisition
- **Primary channel**: {{acq_channel}} (CAC estimate {{cac}})
- **Content/SEO lever**: {{seo_lever}}
- **Distribution wedge**: {{wedge}}

## Compliance cost estimate
- GDPR: {{gdpr_cost_note}}
- 等保/数据安全: {{cn_compliance_note}}
- Net: {{compliance_tldr}}

## Billing implementation (for monetization-scaffold)
- Provider: Stripe Checkout (recommended) — placement: {{placement}}
- Webhook events to handle: `checkout.session.completed`, `customer.subscription.updated/deleted`
- Tracking fields (埋点): {{tracking_fields}}

## Unit economics (best estimate)
- COGS per user: {{cogs}}
- Gross margin: {{margin}}%
- Break-even users: {{break_even}}

## Open assumptions
{{#pricing_assumptions}}
- {{.}}
{{/pricing_assumptions}}
