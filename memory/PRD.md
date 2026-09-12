# Hackster.ai — Product Notes

## Vision / Mission
"Your biohacking buddy." Keep users on track to improve health & wellness with frequency healing and natural modalities that work short- and long-term. **No habit-forming recommendations.** "Do the work and stay free in the personal health revolution."

## Core existing features
- AI Questionnaire (`/questionnaire`) → GPT recommendations (products, labs) + top-3 matched practitioners.
- Raphael AI wellness chatbot (F.R.E.E.D.O.M. method) at `/chat`.
- Marketplace + "My Stack" (shareable), Community, Coach onboarding.

## Affiliate System — Phase 1 (BUILT & TESTED — 23/23)
Backend (`/app/backend/server.py`):
- Vendor model extended: `fulfillment_type` (affiliate | practitioner_order), network-agnostic `tracking_param`/`tracking_value`/`subid_param`, `add_to_cart_pattern`, `network`. Standard Process & Apex Energetics = practitioner_order.
- `GET /api/go/{product_id}` tracked redirect (302 or `?format=json`) → logs `AffiliateClick` (+est commission) and injects per-click subID.
- `POST /api/stack/checkout` → groups selected items by vendor; affiliate vendors get tracked checkout_url/add_to_cart_url, practitioner vendors flagged. Vendor resolves by id OR slug.
- `POST /api/practitioner-orders` + admin queue `GET/PUT /api/admin/practitioner-orders`.
- `POST /api/affiliate/conversion` webhook stub (mark converted).
- Admin CRUD (role=admin, `require_admin`): `/api/admin/vendors`, `/api/admin/products`.
- `GET /api/admin/affiliate/analytics` (clicks, conversions, est commission by vendor, top products, recent).

Frontend:
- `/app/frontend/src/AdminPanel.js` → `/admin` (Analytics, Products, Vendors & Affiliate, Practitioner Orders). Admin-gated.
- `/app/frontend/src/StackCheckout.js` → one-click "Buy Stack" modal (accept/decline → grouped-by-vendor handoff + practitioner request form + FTC disclosure).
- Public "Find a Coach" nav removed; practitioners surface via questionnaire recommendation.

## Accounts (seeded, idempotent)
- Admin: lzook@plzcompany.com / HacksterAdmin2025!
- Demo member: demo@hackster.ai / Demo12345! (has a mixed-vendor "My Wellness Stack")

## Roadmap / backlog (from owner)
1. **Admin-managed practitioners** in the recommendation engine — add/edit practitioners with back-office payment/subscription status; users only SEE recommendations (via results + Raphael chatbot), directory not public.
2. **Wholesale vs affiliate product sourcing** — products are affiliate link OR wholesale account; log source cleanly in Admin.
3. **Content / education library** — curated content feeding questionnaire results + Raphael chatbot responses (frequency healing, natural modalities).
4. Enforce **no habit-forming** guardrail in Raphael prompt + product flag.
5. Affiliate network signup pending → tracking is network-agnostic; set per-vendor tracking param/value when accounts are live.

## Known minor issues (pre-existing, out of scope)
- `GET /api/coach/recommendations` returns 500 (AI coach dashboard saved-recs) — unrelated to affiliate work.
