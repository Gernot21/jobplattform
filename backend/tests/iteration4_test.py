"""Iteration 4 tests: employee profile why_consider + 10-step pensum + CV upload/download/delete + employer CV access.

Uses public REACT_APP_BACKEND_URL. CV uploads hit real Emergent object storage,
so PDFs are kept tiny (~hundreds of bytes). The 15.5 MB test relies on the
server returning 413 BEFORE the storage call.
"""
import os
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = open("/app/backend/.env").read().split("MONGO_URL=")[1].split("\n")[0].strip().strip('"')
DB_NAME = open("/app/backend/.env").read().split("DB_NAME=")[1].split("\n")[0].strip().strip('"')

SFX = uuid.uuid4().hex[:8]
EMP_EMAIL = f"test_it4_emp_{SFX}@example.com"
EMP2_EMAIL = f"test_it4_emp2_{SFX}@example.com"
EMR_EMAIL = f"test_it4_emr_{SFX}@example.com"
EMR2_EMAIL = f"test_it4_emr2_{SFX}@example.com"
PWD = "Password123!"

ADMIN_EMAIL = "admin@jobportal.ch"
ADMIN_PASSWORD = "Admin123!"

# Minimal valid PDF (~200 bytes)
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 300]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000055 00000 n \n0000000100 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF\n"
)


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


@pytest.fixture(scope="module")
def emp2(s):
    r = s.post(f"{API}/auth/register", json={"email": EMP2_EMAIL, "password": PWD, "role": "employee"})
    assert r.status_code == 200, r.text
    return {"token": r.json()["token"], "id": r.json()["user"]["id"]}


@pytest.fixture(scope="module")
def emr(s):
    r = s.post(f"{API}/auth/register", json={"email": EMR_EMAIL, "password": PWD, "role": "employer"})
    assert r.status_code == 200, r.text
    tok = r.json()["token"]
    uid = r.json()["user"]["id"]
    # profile
    r = s.put(f"{API}/employer/profile", headers=H(tok), json={
        "company_name": "ItFour AG", "company_description": "Test", "contact_person": "X", "contact_email": EMR_EMAIL,
    })
    assert r.status_code == 200, r.text
    # one job
    r = s.post(f"{API}/employer/jobs", headers=H(tok), json={
        "title": "PartTime Dev", "description": "Backend python", "percentage_min": 40, "percentage_max": 80, "location": "Zurich",
    })
    assert r.status_code == 200, r.text
    job_id = r.json()["id"]
    return {"token": tok, "id": uid, "job_id": job_id}


@pytest.fixture(scope="module")
def emr2(s):
    """Second employer who has NO link to emp (used for 403 cross-employer test)."""
    r = s.post(f"{API}/auth/register", json={"email": EMR2_EMAIL, "password": PWD, "role": "employer"})
    assert r.status_code == 200, r.text
    tok = r.json()["token"]
    uid = r.json()["user"]["id"]
    r = s.put(f"{API}/employer/profile", headers=H(tok), json={
        "company_name": "Other AG", "company_description": "Test", "contact_person": "Y", "contact_email": EMR2_EMAIL,
    })
    assert r.status_code == 200, r.text
    r = s.post(f"{API}/employer/jobs", headers=H(tok), json={
        "title": "Other Job", "description": "Other", "percentage_min": 40, "percentage_max": 60, "location": "Bern",
    })
    assert r.status_code == 200, r.text
    return {"token": tok, "id": uid, "job_id": r.json()["id"]}


# ---------- 1. why_consider field persistence ----------
class TestWhyConsider:
    def test_put_profile_accepts_why_consider(self, s, emp):
        r = s.put(f"{API}/employee/profile", headers=H(emp["token"]), json={
            "first_name": "Anna", "last_name": "Muster",
            "core_skills": "Python", "key_experiences": "5y",
            "looking_for": "Part-time backend",
            "why_consider": "Ich bringe Erfahrung in Schweizer KMU mit.",
            "desired_percentage_min": 40, "desired_percentage_max": 80,
        })
        assert r.status_code == 200, r.text
        assert r.json()["why_consider"] == "Ich bringe Erfahrung in Schweizer KMU mit."

    def test_get_profile_persists_why_consider(self, s, emp):
        r = s.get(f"{API}/employee/profile", headers=H(emp["token"]))
        assert r.status_code == 200
        assert r.json().get("why_consider") == "Ich bringe Erfahrung in Schweizer KMU mit."

    def test_why_consider_optional(self, s, emp2):
        # Setting profile without why_consider should succeed (defaults to "")
        r = s.put(f"{API}/employee/profile", headers=H(emp2["token"]), json={
            "first_name": "Bea", "last_name": "Tester",
            "core_skills": "JS", "key_experiences": "x",
            "looking_for": "y",
            "desired_percentage_min": 20, "desired_percentage_max": 60,
        })
        assert r.status_code == 200, r.text
        assert r.json().get("why_consider", "") == ""


# ---------- 2. 10-step pensum validation ----------
class TestPensumSteps:
    @pytest.mark.parametrize("mn,mx", [
        (25, 80),  # not in step
        (40, 75),  # max not in step
        (15, 80),  # below range
        (40, 90),  # above range
        (33, 66),  # both off-step
    ])
    def test_invalid_steps_rejected(self, s, emp, mn, mx):
        r = s.put(f"{API}/employee/profile", headers=H(emp["token"]), json={
            "first_name": "A", "last_name": "B", "core_skills": "c",
            "key_experiences": "d", "looking_for": "e",
            "desired_percentage_min": mn, "desired_percentage_max": mx,
        })
        assert r.status_code == 400, f"{mn}/{mx} should be 400, got {r.status_code}"

    def test_min_gt_max_rejected_when_both_valid_steps(self, s, emp):
        r = s.put(f"{API}/employee/profile", headers=H(emp["token"]), json={
            "first_name": "A", "last_name": "B", "core_skills": "c",
            "key_experiences": "d", "looking_for": "e",
            "desired_percentage_min": 60, "desired_percentage_max": 40,
        })
        assert r.status_code == 400, r.text

    @pytest.mark.parametrize("mn,mx", [(20, 20), (20, 80), (40, 70), (50, 60), (30, 30), (70, 80)])
    def test_valid_step_combos_accepted(self, s, emp, mn, mx):
        r = s.put(f"{API}/employee/profile", headers=H(emp["token"]), json={
            "first_name": "Anna", "last_name": "M",
            "core_skills": "py", "key_experiences": "x", "looking_for": "y",
            "desired_percentage_min": mn, "desired_percentage_max": mx,
        })
        assert r.status_code == 200, r.text


# ---------- 3. CV upload validation ----------
class TestCVUploadValidation:
    def test_upload_requires_auth(self, s):
        r = s.post(f"{API}/employee/cv", files={"file": ("a.pdf", b"x", "application/pdf")})
        assert r.status_code == 401

    def test_upload_employer_forbidden(self, s, emr):
        r = s.post(f"{API}/employee/cv", headers=H(emr["token"]),
                   files={"file": ("a.pdf", MINIMAL_PDF, "application/pdf")})
        assert r.status_code == 403

    def test_upload_non_pdf_rejected(self, s, emp):
        r = s.post(f"{API}/employee/cv", headers=H(emp["token"]),
                   files={"file": ("a.txt", b"hello world", "text/plain")})
        assert r.status_code == 400, r.text

    def test_upload_empty_file_rejected(self, s, emp):
        r = s.post(f"{API}/employee/cv", headers=H(emp["token"]),
                   files={"file": ("a.pdf", b"", "application/pdf")})
        assert r.status_code == 400, r.text

    def test_upload_oversize_rejected_413(self, s, emp):
        # ~15.5 MB pseudo-PDF body. Server reads then checks size BEFORE storage call.
        body = b"%PDF-1.4\n" + (b"A" * (15 * 1024 * 1024 + 512 * 1024))
        r = s.post(f"{API}/employee/cv", headers=H(emp["token"]),
                   files={"file": ("big.pdf", body, "application/pdf")})
        assert r.status_code == 413, f"expected 413, got {r.status_code} body={r.text[:200]}"


# ---------- 4. CV upload happy path + GET profile reflects fields ----------
class TestCVUploadAndProfile:
    def test_upload_valid_pdf(self, s, emp):
        r = s.post(f"{API}/employee/cv", headers=H(emp["token"]),
                   files={"file": ("lebenslauf.pdf", MINIMAL_PDF, "application/pdf")})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["filename"] == "lebenslauf.pdf"
        assert body["size"] == len(MINIMAL_PDF)
        assert "uploaded_at" in body and isinstance(body["uploaded_at"], str) and len(body["uploaded_at"]) > 0

    def test_profile_reflects_cv_fields(self, s, emp):
        r = s.get(f"{API}/employee/profile", headers=H(emp["token"]))
        assert r.status_code == 200
        p = r.json()
        assert p.get("cv_filename") == "lebenslauf.pdf"
        assert p.get("cv_size") == len(MINIMAL_PDF)
        assert p.get("cv_uploaded_at")

    def test_download_own_cv(self, s, emp):
        r = s.get(f"{API}/employee/cv", headers=H(emp["token"]))
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content.startswith(b"%PDF")
        assert len(r.content) == len(MINIMAL_PDF)

    def test_download_own_cv_requires_auth(self, s):
        r = s.get(f"{API}/employee/cv")
        assert r.status_code == 401


# ---------- 5. Employer cross-access ----------
class TestEmployerCVAccess:
    def test_employer_403_before_applicant_applies(self, s, emr, emp):
        r = s.get(f"{API}/employer/applicants/{emp['id']}/cv", headers=H(emr["token"]))
        assert r.status_code == 403, r.text

    def test_employee_role_forbidden(self, s, emp2, emp):
        r = s.get(f"{API}/employer/applicants/{emp['id']}/cv", headers=H(emp2["token"]))
        assert r.status_code == 403, r.text

    def test_applicant_applies_then_employer_can_download(self, s, emr, emp):
        # emp applies to emr.job
        r = s.post(f"{API}/employee/applications", headers=H(emp["token"]),
                   json={"job_id": emr["job_id"], "cover_letter": "Hi"})
        assert r.status_code == 200, r.text
        r = s.get(f"{API}/employer/applicants/{emp['id']}/cv", headers=H(emr["token"]))
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content.startswith(b"%PDF")

    def test_unrelated_employer_still_403(self, s, emr2, emp):
        # emp only applied to emr's job, not emr2's
        r = s.get(f"{API}/employer/applicants/{emp['id']}/cv", headers=H(emr2["token"]))
        assert r.status_code == 403, r.text

    def test_employer_404_if_applicant_has_no_cv(self, s, emr, emp2):
        # emp2 applies to emr's job but has no CV uploaded
        r = s.post(f"{API}/employee/applications", headers=H(emp2["token"]),
                   json={"job_id": emr["job_id"], "cover_letter": "Hi"})
        assert r.status_code == 200, r.text
        r = s.get(f"{API}/employer/applicants/{emp2['id']}/cv", headers=H(emr["token"]))
        assert r.status_code == 404, r.text


# ---------- 6. DELETE CV ----------
class TestCVDelete:
    def test_delete_cv(self, s, emp):
        r = s.delete(f"{API}/employee/cv", headers=H(emp["token"]))
        assert r.status_code == 200, r.text
        assert r.json().get("deleted") is True

    def test_profile_no_longer_has_cv_fields(self, s, emp):
        r = s.get(f"{API}/employee/profile", headers=H(emp["token"]))
        assert r.status_code == 200
        p = r.json()
        assert not p.get("cv_filename")
        assert not p.get("cv_storage_path")

    def test_download_own_cv_404_after_delete(self, s, emp):
        r = s.get(f"{API}/employee/cv", headers=H(emp["token"]))
        assert r.status_code == 404, r.text

    def test_employer_404_after_applicant_deletes_cv(self, s, emr, emp):
        r = s.get(f"{API}/employer/applicants/{emp['id']}/cv", headers=H(emr["token"]))
        assert r.status_code == 404, r.text


# ---------- Cleanup ----------
class TestZZCleanup:
    def test_cleanup(self, s, admin_token, emp, emp2, emr, emr2):
        for uid in (emp["id"], emp2["id"], emr["id"], emr2["id"]):
            s.delete(f"{API}/admin/users/{uid}", headers=H(admin_token))
