# PRD – Teilzeit.Jobs (JobPortal 20-80)

## Original Problem Statement
Jobportal ausschliesslich für Teilzeitstellen 20%–80% mit KI-Matching. Rollen: Arbeitnehmer, Arbeitgeber, Superuser. Bilingual DE/EN. Vertrauen & Sicherheit. Hosting via GitHub + Vercel + MongoDB.

## Architecture
- **Backend**: FastAPI + Motor (MongoDB async), JWT auth, bcrypt
- **Frontend**: React 19 + React Router + Tailwind + shadcn/ui
- **AI**: Claude Sonnet 4.5 via `emergentintegrations` (model `claude-sonnet-4-5-20250929`)
- **Payments**: Stripe Checkout via `emergentintegrations.payments.stripe.checkout`
- **Theme**: Deep blue `#0F172A` + emerald `#10B981`, Outfit + DM Sans

## User Personas
1. Arbeitnehmer – kostenlos, Teilzeitsuche
2. Arbeitgeber – 4 Abostufen, KI-Matching für Bewerber
3. Admin/Superuser – Profile + Updates + Statistiken

## Pricing (CHF, Arbeitgeber)
| Tier | Preis | Inserate |
|------|-------|----------|
| Starter | 0 | 5 / Jahr |
| Plus | 30 / Monat | 5 / Monat |
| Pro | 100 / Monat | 15 / Monat |
| Enterprise | 250 / Monat | unbegrenzt |

Reset automatisch am 1. des Monats (bzw. Jahres bei Starter). Bei Erreichen → HTTP 402 + Upgrade-Prompt im UI.

## Implemented (2026-02)
### Iteration 1
- JWT Auth (register/login/me), Admin-Seeding idempotent
- Employee: Profil, KI-Matches, Bewerbungen
- Employer: Firmenprofil, Jobs CRUD, Bewerber-Liste (sortiert nach Match-Score)
- Admin: User-Verwaltung (block/delete), Updates (test/prod, publish), Statistiken
- Bilingual DE/EN, Trust badges, strict 20–80% validation

### Iteration 2
- Brute-Force-Schutz (5 Fehlversuche/E-Mail → 15 min Lockout)
- Top-K Pre-Filter (15 Jobs per Keyword-Overlap) vor jedem LLM-Call
- Stripe Subscriptions (4 Tiers, CHF), Webhook + Status-Polling
- Quota-Enforcement im Job-Create-Endpoint (HTTP 402)
- Frontend: Pricing-Tab + Subscription-Banner + Quota-Progress-Bar
- Graceful Fallback bei Stripe-Status-Errors

### Tests
- 47/47 grün (30 iter-1 + 17 iter-2). Live-LLM + Stripe-Test-Stub abgedeckt.

## Test Credentials
- Admin: `admin@jobportal.ch` / `Admin123!`

## Prioritised Backlog
### P1
- Stripe-Webhook in Produktion mit echtem Stripe-Account verbinden (Dashboard-Konfiguration)
- Server.py in Module splitten (auth/employer/employee/admin/payments routers)
- POST /api/employer/checkout: dict → Pydantic Model

### P2
- E-Mail-Benachrichtigung bei neuer Bewerbung (Resend / SendGrid)
- PDF-Lebenslauf-Upload + AI-Parsing
- Stripe-Subscription-Cancel-Endpoint

### P3
- LinkedIn-Login, Such-/Filter-Funktion, Stellen-Boost-Feature für Pro/Enterprise
- GitHub-Push + Vercel-Frontend-Deployment (siehe support_agent)

## Deployment Notes (für Nutzer)
- GitHub-Push aus Emergent: über UI "Save to GitHub" verfügbar
- Vercel: Frontend nur (React build); Backend bleibt auf Emergent / dediziertem Host
- MongoDB: Atlas (cloud) für Produktion empfohlen
