"""Iteration 2 focused tests: subscription tiers, quotas, brute-force, Stripe checkout, top-K."""
import os
import uuid
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = open("/app/backend/.env").read().split("MONGO_URL=")[1].split("\n")[0].strip().strip('"')
DB_NAME = open("/app/backend/.env").read().split("DB_NAME=")[1].split("\n")[0].strip().strip('"')

SFX = uuid.uuid4().hex[:8]
EMR_EMAIL = f"test_it2_emr_{SFX}@example.com"
EMP_EMAIL = f"test_it2_emp_{SFX}@example.com"
BF_EMAIL = f"test_it2_bf_{SFX}@example.com"  # for brute-force isolated lockout
PWD = "Password123!"

ADMIN_EMAIL = "admin@jobportal.ch"
ADMIN_PASSWORD = "Admin123!"


def H(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def mongo():
    c = MongoClient(MONGO_URL)
    yield c[DB_NAME]
    c.close()


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def emr(s):
    r = s.post(f"{API}/auth/register", json={"email": EMR_EMAIL, "password": PWD, "role": "employer"})
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    uid = r.json()["user"]["id"]
    # Create employer profile (required for posting jobs)
    rp = s.put(f"{API}/employer/profile", headers=H(token), json={
        "company_name": "TEST IT2 Corp",
        "company_description": "Iter2 test",
        "contact_person": "QA",
        "contact_email": "qa@test.ch",
    })
    assert rp.status_code == 200, rp.text
    return {"token": token, "id": uid}


@pytest.fixture(scope="module")
def emp(s):
    r = s.post(f"{API}/auth/register", json={"email": EMP_EMAIL, "password": PWD, "role": "employee"})
    assert r.status_code == 200, r.text
    return {"token": r.json()["token"], "id": r.json()["user"]["id"]}


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ---------------- Tiers ----------------
class TestTiers:
    def test_list_tiers(self, s):
        r = s.get(f"{API}/tiers")
        assert r.status_code == 200
        tiers = r.json()
        assert isinstance(tiers, list)
        ids = {t["id"]: t for t in tiers}
        assert set(ids.keys()) == {"tier_1", "tier_2", "tier_3", "tier_4"}
        # tier_1 free 5/year
        assert ids["tier_1"]["price"] == 0.0
        assert ids["tier_1"]["max_postings"] == 5
        assert ids["tier_1"]["period"] == "year"
        # tier_2 30 CHF 5/month
        assert ids["tier_2"]["price"] == 30.0
        assert ids["tier_2"]["currency"].lower() == "chf"
        assert ids["tier_2"]["max_postings"] == 5
        assert ids["tier_2"]["period"] == "month"
        # tier_3 100 CHF 15/month
        assert ids["tier_3"]["price"] == 100.0
        assert ids["tier_3"]["max_postings"] == 15
        assert ids["tier_3"]["period"] == "month"
        # tier_4 250 CHF unlimited/month
        assert ids["tier_4"]["price"] == 250.0
        assert ids["tier_4"]["max_postings"] == -1
        assert ids["tier_4"]["period"] == "month"


# ---------------- Subscription / Quota ----------------
class TestSubscription:
    def test_default_subscription(self, s, emr):
        r = s.get(f"{API}/employer/subscription", headers=H(emr["token"]))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["tier"]["id"] == "tier_1"
        assert data["postings_used"] == 0
        assert data["remaining"] == 5
        assert data["can_post"] is True

    def test_non_employer_subscription_forbidden(self, s, emp):
        r = s.get(f"{API}/employer/subscription", headers=H(emp["token"]))
        assert r.status_code == 403

    def test_job_increments_postings_used(self, s, emr):
        r = s.post(f"{API}/employer/jobs", headers=H(emr["token"]), json={
            "title": "QA Job 1",
            "description": "Some desc with Python and FastAPI keywords for testing.",
            "percentage_min": 40, "percentage_max": 80, "location": "Bern",
        })
        assert r.status_code == 200, r.text
        r2 = s.get(f"{API}/employer/subscription", headers=H(emr["token"]))
        assert r2.status_code == 200
        assert r2.json()["postings_used"] == 1
        assert r2.json()["remaining"] == 4

    def test_tier1_quota_exhausted_returns_402(self, s, emr):
        # Already have 1 job; create 4 more to reach 5 (the max for tier_1)
        for i in range(2, 6):
            r = s.post(f"{API}/employer/jobs", headers=H(emr["token"]), json={
                "title": f"QA Job {i}",
                "description": "Filler description for tier_1 quota test.",
                "percentage_min": 40, "percentage_max": 80,
            })
            assert r.status_code == 200, f"Job {i} create failed: {r.text}"
        # Now 5/5 used; 6th must 402
        r = s.post(f"{API}/employer/jobs", headers=H(emr["token"]), json={
            "title": "QA Job 6 - over quota",
            "description": "Should fail with 402",
            "percentage_min": 40, "percentage_max": 80,
        })
        assert r.status_code == 402, f"Expected 402, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "upgraden" in detail.lower(), f"Expected 'upgraden' in detail, got: {detail}"


# ---------------- Brute-force ----------------
class TestBruteForce:
    def test_register_bf_user(self, s):
        r = s.post(f"{API}/auth/register", json={"email": BF_EMAIL, "password": PWD, "role": "employee"})
        assert r.status_code == 200, r.text

    def test_brute_force_lockout(self, s, mongo):
        # Pre-cleanup any prior attempts for this identifier across IPs
        mongo.login_attempts.delete_many({"identifier": BF_EMAIL})
        # 5 failed logins
        for i in range(5):
            r = s.post(f"{API}/auth/login", json={"email": BF_EMAIL, "password": "wrong"})
            assert r.status_code == 401, f"Attempt {i+1} expected 401, got {r.status_code}"
        # 6th should be 429
        r = s.post(f"{API}/auth/login", json={"email": BF_EMAIL, "password": "wrong"})
        assert r.status_code == 429, f"Expected 429, got {r.status_code}: {r.text}"
        assert "try again in" in r.json().get("detail", "").lower()

    def test_successful_login_clears_counter(self, s, mongo):
        # Clear lock from previous test
        mongo.login_attempts.delete_many({"identifier": BF_EMAIL})
        # 3 failed attempts
        for _ in range(3):
            r = s.post(f"{API}/auth/login", json={"email": BF_EMAIL, "password": "wrong"})
            assert r.status_code == 401
        # Successful login
        r = s.post(f"{API}/auth/login", json={"email": BF_EMAIL, "password": PWD})
        assert r.status_code == 200
        # No login_attempts doc should remain
        rec = mongo.login_attempts.find_one({"identifier": BF_EMAIL})
        assert rec is None, f"Expected attempts cleared, found: {rec}"


# ---------------- Stripe Checkout ----------------
class TestCheckout:
    def test_checkout_tier1_rejected(self, s, emr):
        r = s.post(f"{API}/employer/checkout", headers=H(emr["token"]), json={
            "tier_id": "tier_1", "origin_url": "https://example.com",
        })
        assert r.status_code == 400

    def test_checkout_missing_origin_url(self, s, emr):
        r = s.post(f"{API}/employer/checkout", headers=H(emr["token"]), json={
            "tier_id": "tier_2",
        })
        assert r.status_code == 400

    def test_checkout_non_employer_forbidden(self, s, emp):
        r = s.post(f"{API}/employer/checkout", headers=H(emp["token"]), json={
            "tier_id": "tier_2", "origin_url": "https://example.com",
        })
        assert r.status_code == 403

    def test_checkout_invalid_tier(self, s, emr):
        r = s.post(f"{API}/employer/checkout", headers=H(emr["token"]), json={
            "tier_id": "tier_999", "origin_url": "https://example.com",
        })
        assert r.status_code == 400

    def test_checkout_creates_session_and_tx(self, s, emr, mongo):
        r = s.post(f"{API}/employer/checkout", headers=H(emr["token"]), json={
            "tier_id": "tier_2", "origin_url": "https://example.com",
        }, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "url" in data and data["url"].startswith("http")
        assert "session_id" in data and data["session_id"]
        # Persisted as pending
        tx = mongo.payment_transactions.find_one({"session_id": data["session_id"]})
        assert tx is not None
        assert tx["payment_status"] == "pending"
        assert tx["user_id"] == emr["id"]
        assert tx["tier_id"] == "tier_2"
        pytest.it2_session_id = data["session_id"]

    def test_payment_status_owner(self, s, emr):
        sid = getattr(pytest, "it2_session_id", None)
        if not sid:
            pytest.skip("No session id from previous test")
        r = s.get(f"{API}/payments/status/{sid}", headers=H(emr["token"]), timeout=30)
        assert r.status_code == 200, r.text
        assert "payment_status" in r.json()

    def test_payment_status_other_user_forbidden(self, s, emp):
        sid = getattr(pytest, "it2_session_id", None)
        if not sid:
            pytest.skip("No session id from previous test")
        r = s.get(f"{API}/payments/status/{sid}", headers=H(emp["token"]), timeout=30)
        assert r.status_code == 403


# ---------------- Suggested jobs / Top-K ----------------
class TestSuggestedTopK:
    def test_suggested_returns_at_most_15(self, s, emp):
        # Create employee profile first
        rp = s.put(f"{API}/employee/profile", headers=H(emp["token"]), json={
            "first_name": "Test", "last_name": "TopK",
            "core_skills": "Python FastAPI MongoDB",
            "key_experiences": "Backend engineering experience",
            "looking_for": "Part-time backend role",
            "desired_percentage_min": 40, "desired_percentage_max": 80,
        })
        assert rp.status_code == 200
        # The employer in this iteration already created 5 jobs; there may be others in DB.
        r = s.get(f"{API}/employee/jobs/suggested", headers=H(emp["token"]), timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) <= 15, f"Top-K must cap at 15, got {len(data)}"
        if data:
            assert "match_score" in data[0]


# ---------------- Cleanup ----------------
class TestZZCleanup:
    def test_cleanup(self, s, admin_token, emr, emp, mongo):
        # Delete bf user (find id)
        u = mongo.users.find_one({"email": BF_EMAIL})
        if u:
            s.delete(f"{API}/admin/users/{u['id']}", headers=H(admin_token))
        # Delete emr + emp
        s.delete(f"{API}/admin/users/{emr['id']}", headers=H(admin_token))
        s.delete(f"{API}/admin/users/{emp['id']}", headers=H(admin_token))
        # Cleanup login_attempts and stale payment_transactions
        mongo.login_attempts.delete_many({"identifier": {"$regex": "^test_it2_"}})
        mongo.payment_transactions.delete_many({"user_id": emr["id"]})
