# PRD – Teilzeit.Jobs (JobPortal 20-80)

## Original Problem Statement
Jobportal ausschliesslich für Teilzeitstellen 20%–80% mit KI-Matching. Rollen: Arbeitnehmer, Arbeitgeber, Superuser. Bilingual DE/EN. Vertrauen & Sicherheit.

## Architecture
- **Backend**: FastAPI + Motor (MongoDB async)
- **Frontend**: React 19 + React Router + Tailwind + shadcn/ui
- **AI**: Claude Sonnet 4.5 (`emergentintegrations`)
- **Payments**: Stripe Checkout (`emergentintegrations.payments.stripe.checkout`)
- **Auth**: JWT (HS256, 7d) + bcrypt (admin) + Emergent-managed Google OAuth (users) + TOTP 2FA (pyotp/qrcode)
- **Theme**: Deep blue `#0F172A` + emerald `#10B981`, Outfit + DM Sans

## User Personas
1. Arbeitnehmer – Google-Login, kostenlos
2. Arbeitgeber – Google-Login, 4 Abo-Stufen
3. Admin/Superuser – Legacy E-Mail/Passwort + 2FA möglich

## Implemented
### Iteration 1
- JWT Auth, employee/employer/admin dashboards, AI matching, admin panel
### Iteration 2
- Brute-force protection, Top-K pre-filter, Stripe subscriptions (4 tiers CHF), quota enforcement
### Iteration 3
- **Google OAuth** via Emergent-managed Auth (`/api/auth/google/exchange`)
- **Onboarding** flow für neue Google-User (Rollenauswahl employee/employer)
- **TOTP 2FA** (optional): setup → QR + Secret → enable, disable, login-challenge
- Security-Tab in allen Dashboards (employee/employer/admin)
- Landing-Page: "Mit Google fortfahren" primary, dezenter Admin-Login Link

## Tests
- 68/68 grün (30 iter-1 + 17 iter-2 + 21 iter-3). Live-LLM + Stripe-Stub + TOTP-Lifecycle abgedeckt.

## Test Credentials
- Admin: `admin@jobportal.ch` / `Admin123!`
- Google: real OAuth flow (no static credentials)

## Pricing (CHF, Arbeitgeber)
| Tier | Preis | Inserate |
|------|-------|----------|
| Starter | 0 | 5 / Jahr |
| Plus | 30 / Monat | 5 / Monat |
| Pro | 100 / Monat | 15 / Monat |
| Enterprise | 250 / Monat | unbegrenzt |

## Prioritised Backlog
### P1
- Rate-limit `/api/auth/2fa/login` (Brute-Force-Schutz auch für Challenge-Endpoint)
- server.py (~820 Zeilen) in Submodule splitten
- Pydantic-Modelle für google_exchange + 2fa_login (statt plain dict)

### P2
- E-Mail-Benachrichtigung bei neuer Bewerbung (Resend / SendGrid)
- PDF-Lebenslauf-Upload + KI-Parsing
- Stripe-Subscription-Cancel-Endpoint
- Backup-Codes für 2FA-Recovery

### P3
- LinkedIn-Login, Such-/Filter-Funktion, Stellen-Boost
- Top-Talent-Alerts für Plus/Pro/Enterprise
- GitHub + Vercel-Deployment Setup (siehe support_agent)
