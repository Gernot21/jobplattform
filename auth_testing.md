# Auth Testing Playbook

## Google Auth Flow
1. Login button → redirects to https://auth.emergentagent.com/?redirect={origin}/auth/callback
2. After Google auth: lands at /auth/callback#session_id=XXX
3. Frontend extracts session_id, POSTs to /api/auth/google/exchange
4. Backend calls Emergent /auth/v1/env/oauth/session-data with X-Session-ID
5. Backend creates/finds user, returns JWT token + needs_onboarding flag
6. If needs_onboarding → redirect to /onboarding (role selection)
7. If 2FA enabled → return {requires_2fa, challenge_token} instead of full token; user submits TOTP

## Test Credentials (Legacy email/password – ADMIN ONLY)
- admin@jobportal.ch / Admin123!

## Test Identities (Google)
- No password-based credentials for Google flows.
- For local testing, create a user_session document via mongosh and inject session cookie.

## Manual API Tests
```bash
# Exchange (requires real Emergent session_id obtained via Google flow)
curl -X POST $API/api/auth/google/exchange \
  -H "Content-Type: application/json" \
  -d '{"session_id":"..."}'

# 2FA setup (Bearer)
curl -X POST $API/api/auth/2fa/setup -H "Authorization: Bearer $TOKEN"
curl -X POST $API/api/auth/2fa/enable -H "Authorization: Bearer $TOKEN" -d '{"code":"123456"}'
```
