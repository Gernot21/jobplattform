"""Iteration 3 tests: Google exchange stub, TOTP 2FA flow, onboarding."""
import os
import uuid
import pytest
import pyotp
import requests
from pymongo import MongoClient

BASE_URL = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = open("/app/backend/.env").read().split("MONGO_URL=")[1].split("\n")[0].strip().strip('"')
DB_NAME = open("/app/backend/.env").read().split("DB_NAME=")[1].split("\n")[0].strip().strip('"')

SFX = uuid.uuid4().hex[:8]
EMP_EMAIL = f"test_it3_emp_{SFX}@example.com"
EMR_EMAIL = f"test_it3_emr_{SFX}@example.com"
PWD = "Password123!"

ADMIN_EMAIL = "admin@jobportal.ch"
ADMIN_PASSWORD = "Admin123!"


def H(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def mongo():
    c = MongoClient(MONGO_URL)
    yield c[DB_NAME]
    c.close()


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def emp(s):
    r = s.post(f"{API}/auth/register", json={"email": EMP_EMAIL, "password": PWD, "role": "employee"})
    assert r.status_code == 200, r.text
    return {"token": r.json()["token"], "id": r.json()["user"]["id"]}


# ---------- Google OAuth exchange (cannot end-to-end test, only error paths) ----------
class TestGoogleExchange:
    def test_missing_session_id_returns_400(self, s):
        r = s.post(f"{API}/auth/google/exchange", json={})
        assert r.status_code == 400, r.text
        assert "session_id" in r.json().get("detail", "").lower()

    def test_empty_session_id_returns_400(self, s):
        r = s.post(f"{API}/auth/google/exchange", json={"session_id": ""})
        assert r.status_code == 400

    def test_invalid_session_id_returns_401(self, s):
        r = s.post(f"{API}/auth/google/exchange",
                   json={"session_id": "definitely-not-a-valid-session-id-xxxxx"})
        assert r.status_code == 401, r.text


# ---------- Admin legacy login (regression) ----------
class TestAdminLogin:
    def test_admin_login_still_works(self, admin_token):
        assert admin_token  # fixture asserts 200


# ---------- 2FA setup / enable / login / disable ----------
class TestTwoFA:
    def test_setup_returns_secret_and_qr(self, s, emp):
        r = s.post(f"{API}/auth/2fa/setup", headers=H(emp["token"]))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "secret" in data and len(data["secret"]) == 32
        # base32 alphabet
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in data["secret"])
        assert data["otpauth_uri"].startswith("otpauth://totp/")
        assert data["qr_data_url"].startswith("data:image/png;base64,")
        # qr base64 portion long enough
        assert len(data["qr_data_url"]) > 200
        pytest.it3_secret = data["secret"]

    def test_setup_requires_auth(self, s):
        r = s.post(f"{API}/auth/2fa/setup")
        assert r.status_code == 401

    def test_enable_with_wrong_code_401(self, s, emp):
        r = s.post(f"{API}/auth/2fa/enable", headers=H(emp["token"]), json={"code": "000000"})
        assert r.status_code == 401

    def test_enable_with_valid_code(self, s, emp):
        code = pyotp.TOTP(pytest.it3_secret).now()
        r = s.post(f"{API}/auth/2fa/enable", headers=H(emp["token"]), json={"code": code})
        assert r.status_code == 200, r.text
        assert r.json().get("enabled") is True
        # /auth/me reflects totp_enabled=true
        r2 = s.get(f"{API}/auth/me", headers=H(emp["token"]))
        assert r2.status_code == 200
        assert r2.json().get("totp_enabled") is True

    def test_login_returns_requires_2fa(self, s):
        r = s.post(f"{API}/auth/login", json={"email": EMP_EMAIL, "password": PWD})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("requires_2fa") is True
        assert body.get("challenge_token")
        assert "token" not in body or body.get("token") is None
        pytest.it3_challenge = body["challenge_token"]

    def test_2fa_login_wrong_code_401(self, s):
        r = s.post(f"{API}/auth/2fa/login", json={
            "challenge_token": pytest.it3_challenge,
            "code": "000000",
        })
        assert r.status_code == 401

    def test_2fa_login_success_returns_access_token(self, s):
        code = pyotp.TOTP(pytest.it3_secret).now()
        r = s.post(f"{API}/auth/2fa/login", json={
            "challenge_token": pytest.it3_challenge,
            "code": code,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("token")
        assert body["user"]["email"] == EMP_EMAIL
        assert body["user"]["totp_enabled"] is True

    def test_2fa_login_missing_fields_400(self, s):
        r = s.post(f"{API}/auth/2fa/login", json={"challenge_token": pytest.it3_challenge})
        assert r.status_code == 400

    def test_disable_with_wrong_code(self, s, emp):
        r = s.post(f"{API}/auth/2fa/disable", headers=H(emp["token"]), json={"code": "000000"})
        assert r.status_code == 401

    def test_disable_with_valid_code(self, s, emp):
        code = pyotp.TOTP(pytest.it3_secret).now()
        r = s.post(f"{API}/auth/2fa/disable", headers=H(emp["token"]), json={"code": code})
        assert r.status_code == 200, r.text
        assert r.json().get("enabled") is False
        r2 = s.get(f"{API}/auth/me", headers=H(emp["token"]))
        assert r2.json().get("totp_enabled") is False

    def test_disable_when_not_enabled_400(self, s, emp):
        r = s.post(f"{API}/auth/2fa/disable", headers=H(emp["token"]), json={"code": "123456"})
        assert r.status_code == 400


# ---------- Onboarding (Google user with no role) ----------
class TestOnboarding:
    def test_needs_onboarding_true_for_no_role_user(self, s, mongo):
        # Simulate Google user by inserting directly + minting a token via admin path? Instead
        # use the public model: insert a user with role=None and use create_access_token via login? No,
        # we can't login (no password). Use the helper by inserting and crafting a JWT via /auth/google
        # path is not possible without a real session. We'll simulate by inserting user and using a
        # short JWT: call a small back-channel: register an employer, then unset role via mongo, login,
        # check /auth/me.
        # 1. Register as employer (legacy)
        r = s.post(f"{API}/auth/register", json={"email": EMR_EMAIL, "password": PWD, "role": "employer"})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        uid = r.json()["user"]["id"]
        # 2. Strip role to None to simulate google new user state
        mongo.users.update_one({"id": uid}, {"$set": {"role": None}})
        # 3. /auth/me should return needs_onboarding=true
        r = s.get(f"{API}/auth/me", headers=H(token))
        assert r.status_code == 200, r.text
        assert r.json().get("needs_onboarding") is True
        assert r.json().get("role") is None
        pytest.it3_role_uid = uid
        pytest.it3_role_token = token

    def test_onboarding_invalid_role(self, s):
        r = s.post(f"{API}/auth/onboarding", headers=H(pytest.it3_role_token), json={"role": "admin"})
        assert r.status_code == 400

    def test_onboarding_sets_role(self, s):
        r = s.post(f"{API}/auth/onboarding", headers=H(pytest.it3_role_token), json={"role": "employer"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["user"]["role"] == "employer"
        assert body["user"].get("needs_onboarding") is False
        assert body.get("token")
        pytest.it3_role_token = body["token"]  # use refreshed token

    def test_onboarding_role_already_set_400(self, s):
        r = s.post(f"{API}/auth/onboarding", headers=H(pytest.it3_role_token), json={"role": "employee"})
        assert r.status_code == 400

    def test_onboarding_requires_auth(self, s):
        r = s.post(f"{API}/auth/onboarding", json={"role": "employee"})
        assert r.status_code == 401


# ---------- Cleanup ----------
class TestZZCleanup:
    def test_cleanup(self, s, admin_token, emp, mongo):
        for uid_key in ("it3_role_uid",):
            uid = getattr(pytest, uid_key, None)
            if uid:
                s.delete(f"{API}/admin/users/{uid}", headers=H(admin_token))
        s.delete(f"{API}/admin/users/{emp['id']}", headers=H(admin_token))
        mongo.login_attempts.delete_many({"identifier": {"$regex": "^test_it3_"}})
