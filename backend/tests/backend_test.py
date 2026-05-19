"""Backend tests for JobPortal 20-80 (pytest)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@jobportal.ch"
ADMIN_PASSWORD = "Admin123!"

# Unique suffix for this run
SFX = uuid.uuid4().hex[:8]
EMP_EMAIL = f"test_emp_{SFX}@example.com"
EMR_EMAIL = f"test_emr_{SFX}@example.com"
PWD = "Password123!"


@pytest.fixture(scope="session")
def s():
    return requests.Session()


@pytest.fixture(scope="session")
def tokens(s):
    """Register employee + employer, login admin; return tokens dict."""
    t = {}
    # Register employee
    r = s.post(f"{API}/auth/register", json={"email": EMP_EMAIL, "password": PWD, "role": "employee"})
    assert r.status_code == 200, r.text
    t["emp"] = r.json()["token"]
    t["emp_id"] = r.json()["user"]["id"]
    # Register employer
    r = s.post(f"{API}/auth/register", json={"email": EMR_EMAIL, "password": PWD, "role": "employer"})
    assert r.status_code == 200, r.text
    t["emr"] = r.json()["token"]
    t["emr_id"] = r.json()["user"]["id"]
    # Admin login
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    t["admin"] = r.json()["token"]
    return t


def H(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Auth ----------
class TestAuth:
    def test_root(self, s):
        r = s.get(f"{API}/")
        assert r.status_code == 200

    def test_register_invalid_role(self, s):
        r = s.post(f"{API}/auth/register", json={"email": f"TEST_x{SFX}@e.com", "password": PWD, "role": "admin"})
        assert r.status_code == 400

    def test_duplicate_register(self, s, tokens):
        r = s.post(f"{API}/auth/register", json={"email": EMP_EMAIL, "password": PWD, "role": "employee"})
        assert r.status_code == 409

    def test_login_wrong_password(self, s, tokens):
        r = s.post(f"{API}/auth/login", json={"email": EMP_EMAIL, "password": "wrong"})
        assert r.status_code == 401

    def test_login_success(self, s, tokens):
        r = s.post(f"{API}/auth/login", json={"email": EMP_EMAIL, "password": PWD})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "employee"

    def test_admin_login(self, tokens):
        assert tokens["admin"]

    def test_me_employee(self, s, tokens):
        r = s.get(f"{API}/auth/me", headers=H(tokens["emp"]))
        assert r.status_code == 200
        assert r.json()["role"] == "employee"
        assert r.json()["email"] == EMP_EMAIL

    def test_me_no_token(self, s):
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---------- Employee profile ----------
class TestEmployeeProfile:
    def test_put_profile_invalid_pct(self, s, tokens):
        r = s.put(f"{API}/employee/profile", headers=H(tokens["emp"]), json={
            "first_name": "A", "last_name": "B", "core_skills": "py",
            "key_experiences": "x", "looking_for": "y",
            "desired_percentage_min": 10, "desired_percentage_max": 80,
        })
        assert r.status_code == 400

    def test_put_profile_ok(self, s, tokens):
        r = s.put(f"{API}/employee/profile", headers=H(tokens["emp"]), json={
            "first_name": "Anna", "last_name": "Muster", "core_skills": "Python, FastAPI, MongoDB",
            "key_experiences": "5 years backend dev, freelance projects",
            "looking_for": "Part-time backend role with remote flexibility",
            "desired_percentage_min": 40, "desired_percentage_max": 80,
        })
        assert r.status_code == 200
        assert r.json()["first_name"] == "Anna"

    def test_get_profile(self, s, tokens):
        r = s.get(f"{API}/employee/profile", headers=H(tokens["emp"]))
        assert r.status_code == 200
        assert r.json()["last_name"] == "Muster"

    def test_employer_cant_access_employee(self, s, tokens):
        r = s.get(f"{API}/employee/profile", headers=H(tokens["emr"]))
        assert r.status_code == 403


# ---------- Employer profile + jobs ----------
class TestEmployerFlow:
    def test_put_employer_profile(self, s, tokens):
        r = s.put(f"{API}/employer/profile", headers=H(tokens["emr"]), json={
            "company_name": "TEST Corp", "company_description": "Swiss tech",
            "contact_person": "Hans", "contact_email": "hr@test.ch",
        })
        assert r.status_code == 200
        assert r.json()["company_name"] == "TEST Corp"

    def test_employee_cant_access_employer(self, s, tokens):
        r = s.get(f"{API}/employer/profile", headers=H(tokens["emp"]))
        assert r.status_code == 403

    def test_create_job_bad_pct(self, s, tokens):
        r = s.post(f"{API}/employer/jobs", headers=H(tokens["emr"]), json={
            "title": "X", "description": "Y", "percentage_min": 80, "percentage_max": 40,
        })
        # Could be 400 from manual check or 422 from Field validation
        assert r.status_code in (400, 422)

    def test_create_job(self, s, tokens):
        r = s.post(f"{API}/employer/jobs", headers=H(tokens["emr"]), json={
            "title": "Backend Engineer (Part-time)",
            "description": "Build APIs with FastAPI and MongoDB. Remote-friendly.",
            "percentage_min": 40, "percentage_max": 80, "location": "Zurich",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["title"].startswith("Backend")
        assert data["company_name"] == "TEST Corp"
        pytest.job_id = data["id"]

    def test_list_jobs(self, s, tokens):
        r = s.get(f"{API}/employer/jobs", headers=H(tokens["emr"]))
        assert r.status_code == 200
        assert any(j["id"] == pytest.job_id for j in r.json())


# ---------- Suggested + apply ----------
class TestMatchingAndApply:
    def test_suggested_jobs_llm(self, s, tokens):
        # Calls Claude — may take a few seconds
        r = s.get(f"{API}/employee/jobs/suggested", headers=H(tokens["emp"]), timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        first = data[0]
        assert "match_score" in first
        assert 0 <= first["match_score"] <= 100
        assert "match_reason" in first

    def test_apply_job(self, s, tokens):
        r = s.post(f"{API}/employee/applications", headers=H(tokens["emp"]), json={
            "job_id": pytest.job_id, "cover_letter": "I am interested",
        }, timeout=60)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "submitted"

    def test_apply_duplicate(self, s, tokens):
        r = s.post(f"{API}/employee/applications", headers=H(tokens["emp"]), json={
            "job_id": pytest.job_id, "cover_letter": "again"
        }, timeout=60)
        assert r.status_code == 409

    def test_my_applications(self, s, tokens):
        r = s.get(f"{API}/employee/applications", headers=H(tokens["emp"]))
        assert r.status_code == 200
        apps = r.json()
        assert any(a["job_id"] == pytest.job_id for a in apps)

    def test_employer_applicants(self, s, tokens):
        r = s.get(f"{API}/employer/jobs/{pytest.job_id}/applicants", headers=H(tokens["emr"]))
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["email"] == EMP_EMAIL


# ---------- Admin ----------
class TestAdmin:
    def test_non_admin_blocked(self, s, tokens):
        r = s.get(f"{API}/admin/users", headers=H(tokens["emp"]))
        assert r.status_code == 403

    def test_admin_list_users(self, s, tokens):
        r = s.get(f"{API}/admin/users", headers=H(tokens["admin"]))
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()]
        assert EMP_EMAIL in emails

    def test_admin_stats(self, s, tokens):
        r = s.get(f"{API}/admin/stats", headers=H(tokens["admin"]))
        assert r.status_code == 200
        assert r.json()["users"] >= 3

    def test_admin_block_unblock(self, s, tokens):
        r = s.post(f"{API}/admin/users/{tokens['emp_id']}/block?blocked=true", headers=H(tokens["admin"]))
        assert r.status_code == 200
        # Blocked user cannot access /me
        r2 = s.get(f"{API}/auth/me", headers=H(tokens["emp"]))
        assert r2.status_code == 403
        # Unblock
        r = s.post(f"{API}/admin/users/{tokens['emp_id']}/block?blocked=false", headers=H(tokens["admin"]))
        assert r.status_code == 200

    def test_admin_updates_lifecycle(self, s, tokens):
        # Create
        r = s.post(f"{API}/admin/updates", headers=H(tokens["admin"]), json={
            "title": "TEST Update", "content": "Hello", "environment": "test", "published": False
        })
        assert r.status_code == 200
        upd_id = r.json()["id"]
        # List
        r = s.get(f"{API}/admin/updates?environment=test", headers=H(tokens["admin"]))
        assert r.status_code == 200
        assert any(u["id"] == upd_id for u in r.json())
        # Publish
        r = s.post(f"{API}/admin/updates/{upd_id}/publish", headers=H(tokens["admin"]))
        assert r.status_code == 200
        # Visible in published
        r = s.get(f"{API}/updates/published", headers=H(tokens["emp"]))
        assert r.status_code == 200
        assert any(u["id"] == upd_id for u in r.json())
        # Delete
        r = s.delete(f"{API}/admin/updates/{upd_id}", headers=H(tokens["admin"]))
        assert r.status_code == 200

    def test_admin_cannot_delete_admin(self, s, tokens):
        # find admin id
        r = s.get(f"{API}/admin/users", headers=H(tokens["admin"]))
        admin_id = next(u["id"] for u in r.json() if u["email"] == ADMIN_EMAIL)
        r = s.delete(f"{API}/admin/users/{admin_id}", headers=H(tokens["admin"]))
        assert r.status_code == 400


# ---------- Cleanup ----------
class TestZZCleanup:
    def test_delete_job(self, s, tokens):
        r = s.delete(f"{API}/employer/jobs/{pytest.job_id}", headers=H(tokens["emr"]))
        assert r.status_code == 200

    def test_admin_delete_test_users(self, s, tokens):
        r = s.delete(f"{API}/admin/users/{tokens['emp_id']}", headers=H(tokens["admin"]))
        assert r.status_code == 200
        r = s.delete(f"{API}/admin/users/{tokens['emr_id']}", headers=H(tokens["admin"]))
        assert r.status_code == 200
