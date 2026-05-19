# PRD – Teilzeit.Jobs (JobPortal 20-80)

## Original Problem Statement (verbatim)
Erstelle ein Jobportal. Auf dieser Plattform werden ausschliesslich Jobs im Bereich zwischen 20% und 80% angeboten und gesucht. Das Design soll Vertrauen und Sicherheit ausstrahlen. KI-Matching, drei Rollen (Arbeitnehmer/Arbeitgeber/Superuser), bilingual.

## Architecture
- **Backend**: FastAPI + Motor (MongoDB async), JWT auth, bcrypt password hashing
- **Frontend**: React 19 + React Router + Tailwind + shadcn/ui, axios w/ Bearer token, i18n provider (DE/EN)
- **AI**: Claude Sonnet 4.5 via `emergentintegrations` library (model `claude-sonnet-4-5-20250929`), session-based prompts returning a JSON match payload
- **Theme**: Deep blue `#0F172A` + emerald `#10B981`, Outfit + DM Sans

## User Personas
1. **Arbeitnehmer (employee)** – sucht Teilzeitstelle 20–80%
2. **Arbeitgeber (employer)** – schreibt Teilzeitstellen aus, sieht Bewerber inkl. Match-Score
3. **Superuser / Admin** – verwaltet Profile, Updates (Test- vs. Produktivumgebung), sieht Statistiken

## Core Requirements (static)
- Stellenfilter strikt 20–80% (Validation auf Backend & Frontend)
- KI-Matching: gewichtet (50% looking_for, 30% core_skills, 20% key_experiences)
- Role-based access (employee/employer/admin)
- Bilingual DE/EN mit Language Switcher
- Trust signals (Badges, verschlüsselt, DSGVO)

## Implemented (2026-02)
- Auth: register, login, /auth/me mit Bearer JWT; Admin-Seeding idempotent
- Employee: Profil CRUD, suggested jobs (KI-gematcht), apply, applications list
- Employer: Firmenprofil CRUD, Jobs CRUD, Bewerber-Unterreiter mit Match-Score
- Admin: User-Liste, block/unblock, delete, Stats, Updates (test/prod, publish), Updates-Feed
- 30/30 Backend-Tests grün inkl. Live-Claude-Call

## Test Credentials
- Admin: `admin@jobportal.ch` / `Admin123!` (auto-seeded)

## Prioritised Backlog
### P1
- Brute-force-Schutz auf /auth/login (5 Versuche → 15 min Lockout)
- Frontend-E2E-Tests
- Top-K Pre-Filter vor LLM-Call (Kostenoptimierung)

### P2
- Refresh-Token + httpOnly Cookies
- E-Mail-Notifications bei neuer Bewerbung
- Stripe Payments für Premium-Arbeitgeber

### P3
- LinkedIn-Login
- Resume-Upload (PDF) + AI-Parsing
- Suche / Filter / Tags
