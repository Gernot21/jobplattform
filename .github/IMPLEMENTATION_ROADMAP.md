# Parentjobs Web-App - Implementation Roadmap

## Project Structure
```
parentjobs/
├── frontend/                 # React 19 + TypeScript
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API calls & business logic
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript interfaces
│   │   ├── store/           # Zustand state management
│   │   ├── utils/           # Utility functions
│   │   ├── styles/          # Tailwind config
│   │   └── App.tsx
│   ├── .env.local           # Environment variables
│   └── package.json
│
├── backend/                 # Python FastAPI
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── ai/             # AI/ML services
│   │   ├── auth/           # Authentication
│   │   └── main.py         # App entry point
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

## Phase 1: Foundation (Week 1-2)
- [ ] Project setup & infrastructure
- [ ] Authentication system (OAuth + Email/Password + 2FA)
- [ ] Database schema (Supabase)
- [ ] Base API endpoints
- [ ] Frontend folder structure

## Phase 2: Core Features (Week 3-4)
- [ ] Arbeitnehmer registration & profile
- [ ] Arbeitgeber registration & job creation
- [ ] Job listing & filtering
- [ ] Job matching algorithm

## Phase 3: Advanced Features (Week 5-6)
- [ ] Chat/Messaging system
- [ ] KI-powered CV analysis
- [ ] Dashboard & analytics
- [ ] Premium subscription (Stripe)

## Phase 4: Superuser & Compliance (Week 7-8)
- [ ] Superuser admin panel
- [ ] Content moderation (KI-powered)
- [ ] Compliance & legal (GDPR/nDSG)
- [ ] Testing & optimization

## Technology Stack
- **Frontend**: React 19, TypeScript, Tailwind CSS, Radix UI, Zod
- **Backend**: Python FastAPI, Supabase PostgreSQL
- **Hosting**: Vercel (Frontend), Railway/Heroku (Backend)
- **Authentication**: Supabase Auth (OAuth + Email)
- **Payments**: Stripe API
- **AI/ML**: OpenAI API (CV analysis, job matching)
- **Email**: SendGrid or similar
- **Real-time**: Supabase Realtime (WebSockets)

## Environment Variables

### Frontend (.env.local)
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_OAUTH_CLIENT_ID=
VITE_LINKEDIN_CLIENT_ID=
VITE_STRIPE_PUBLIC_KEY=
```

### Backend (.env)
```
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_JWT_SECRET=
STRIPE_SECRET_KEY=
OPENAI_API_KEY=
DATABASE_URL=
JWT_SECRET=
```

## Key Features Checklist

### Authentication
- [x] Design spec
- [ ] Supabase setup
- [ ] OAuth integration (Google, LinkedIn, Xing)
- [ ] Email/Password flow
- [ ] 2FA implementation
- [ ] Password reset flow

### Arbeitnehmer (Employee)
- [ ] Profile creation
- [ ] CV upload & AI analysis
- [ ] Job recommendations with AI matching
- [ ] Job search & filtering
- [ ] Application submission
- [ ] Chat with employers
- [ ] Premium profile boost

### Arbeitgeber (Employer)
- [ ] Company profile
- [ ] Job posting creation
- [ ] CV upload & PDF parsing
- [ ] Applicant management
- [ ] Chat with candidates
- [ ] Dashboard & analytics
- [ ] Subscription management

### Superuser (Admin)
- [ ] User management
- [ ] Content moderation
- [ ] Dashboard & statistics
- [ ] Settings management
- [ ] Feedback management

### Compliance
- [ ] GDPR compliance
- [ ] nDSG compliance (Swiss)
- [ ] Terms of Service
- [ ] Privacy Policy
- [ ] Content policies (violence, weapons, abuse detection)

## Design System
- **Colors**: Green & white tones (trust, security)
- **Typography**: Modern, clean
- **Components**: Radix UI based
- **Responsive**: Mobile-first
- **Accessibility**: WCAG 2.1 AA

---

Last Updated: 2026-05-25
Status: In Progress - Phase 1
