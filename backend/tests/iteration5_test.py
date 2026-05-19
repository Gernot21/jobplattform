"""Iteration 5 backend tests: CV upload now triggers Claude Sonnet 4.5 analysis
that pre-fills first_name / last_name / core_skills / key_experiences.

Acceptance criteria:
 1. POST /api/employee/cv response now includes an `analysis` dict with the 4 keys
    (values may be empty strings if LLM fails; optional `_warning` field).
 2. PDF with extractable text -> analysis is a dict with all 4 keys (graceful
    degradation: even if LLM budget is exhausted, status must still be 200 and
    `_warning='analysis_failed'` with empty strings).
 3. PDF with no extractable text (e.g. blank ~100B '%PDF-1.4...EOF') -> analysis
    contains `_warning='no_text'`.
 4. POST /api/employee/cv/analyze without a CV -> 404.
 5. POST /api/employee/cv/analyze with an existing CV -> 200 + analysis dict.
 6. POST /api/employee/cv/analyze for non-employee role -> 403.
 7. The CV bytes themselves are not modified by analysis – downloading the CV
    after `analyze` returns the same body that was uploaded.
"""
import io
import os
import uuid
import pytest
import requests
from fpdf import FPDF
from pymongo import MongoClient

# --- Environment ---
BASE_URL = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip().strip('"').rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = open("/app/backend/.env").read().split("MONGO_URL=")[1].split("\n")[0].strip().strip('"')
DB_NAME = open("/app/backend/.env").read().split("DB_NAME=")[1].split("\n")[0].strip().strip('"')

SFX = uuid.uuid4().hex[:8]
EMP_EMAIL = f"test_it5_emp_{SFX}@example.com"
EMP2_EMAIL = f"test_it5_emp2_{SFX}@example.com"  # employee with NO CV yet
EMR_EMAIL = f"test_it5_emr_{SFX}@example.com"
PWD = "Password123!"

ADMIN_EMAIL = "admin@jobportal.ch"
ADMIN_PASSWORD = "Admin123!"

ANALYSIS_KEYS = {"first_name", "last_name", "core_skills", "key_experiences"}


def H(t):
    return {"Authorization": f"Bearer {t}"}


def _build_real_cv_pdf() -> bytes:
    """Build a small but real CV PDF using fpdf2 (text is extractable by pypdf)."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, "Lebenslauf", ln=True)
    pdf.cell(0, 8, "Name: Anna Muster", ln=True)
    pdf.cell(0, 8, "Vorname: Anna", ln=True)
    pdf.cell(0, 8, "Nachname: Muster", ln=True)
    pdf.cell(0, 8, "Kernkompetenzen: Python, FastAPI, Projektleitung, Excel, Englisch C1", ln=True)
    pdf.cell(0, 8, "Berufserfahrung:", ln=True)
    pdf.cell(0, 8, "- 2019-2024 Backend Engineer bei Beispiel AG, Zurich", ln=True)
    pdf.cell(0, 8, "- 2016-2019 Junior Developer bei Demo GmbH, Bern", ln=True)
    out = pdf.output(dest="S")
    if isinstance(out, str):
        out = out.encode("latin-1")
    return bytes(out)


REAL_CV_PDF = _build_real_cv_pdf()
# Minimal nearly-empty PDF (no extractable text)
BLANK_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 300]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000055 00000 n \n0000000100 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF\n"
)


@pytest.fixture(scope="module")
def s():
    return requests.Session()


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
    return {"token": r.json()["token"], "id": r.json()["user"]["id"]}


def _assert_analysis_shape(analysis):
    assert isinstance(analysis, dict), f"analysis must be a dict, got {type(analysis)}"
    for k in ANALYSIS_KEYS:
        assert k in analysis, f"analysis missing key {k!r}: {analysis}"
        assert isinstance(analysis[k], str), f"{k} must be a string"
    # _warning is optional but if present must be a known token
    if "_warning" in analysis:
        assert analysis["_warning"] in {"no_text", "no_key", "analysis_failed"}, analysis["_warning"]


# ---------- 1. Upload with real PDF -> response shape ----------
class TestUploadAnalysisShape:
    def test_upload_real_pdf_returns_analysis(self, s, emp):
        r = s.post(
            f"{API}/employee/cv",
            headers=H(emp["token"]),
            files={"file": ("lebenslauf.pdf", REAL_CV_PDF, "application/pdf")},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["filename"] == "lebenslauf.pdf"
        assert body["size"] == len(REAL_CV_PDF)
        assert "uploaded_at" in body
        assert "analysis" in body, body
        _assert_analysis_shape(body["analysis"])

    def test_uploaded_cv_bytes_are_unmodified(self, s, emp):
        r = s.get(f"{API}/employee/cv", headers=H(emp["token"]))
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content == REAL_CV_PDF


# ---------- 2. Blank PDF -> analysis._warning='no_text' ----------
class TestBlankPdfNoText:
    def test_blank_pdf_returns_no_text_warning(self, s, emp2):
        r = s.post(
            f"{API}/employee/cv",
            headers=H(emp2["token"]),
            files={"file": ("blank.pdf", BLANK_PDF, "application/pdf")},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "analysis" in body
        a = body["analysis"]
        _assert_analysis_shape(a)
        assert a.get("_warning") == "no_text", f"expected _warning='no_text', got {a}"
        # All fields should be empty strings
        for k in ANALYSIS_KEYS:
            assert a[k] == "", f"{k} should be '' for no_text case, got {a[k]!r}"


# ---------- 3. /api/employee/cv/analyze endpoint ----------
class TestReanalyzeEndpoint:
    def test_reanalyze_employer_403(self, s, emr):
        r = s.post(f"{API}/employee/cv/analyze", headers=H(emr["token"]), timeout=30)
        assert r.status_code == 403, r.text

    def test_reanalyze_requires_auth(self, s):
        r = s.post(f"{API}/employee/cv/analyze", timeout=30)
        assert r.status_code == 401

    def test_reanalyze_without_cv_returns_404(self, s):
        """A fresh employee with no CV uploaded should get 404."""
        sfx = uuid.uuid4().hex[:8]
        email = f"test_it5_empfresh_{sfx}@example.com"
        r = s.post(f"{API}/auth/register", json={"email": email, "password": PWD, "role": "employee"})
        assert r.status_code == 200, r.text
        tok = r.json()["token"]
        uid = r.json()["user"]["id"]
        r = s.post(f"{API}/employee/cv/analyze", headers=H(tok), timeout=30)
        assert r.status_code == 404, r.text
        # cleanup
        admin = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).json()["token"]
        s.delete(f"{API}/admin/users/{uid}", headers=H(admin))

    def test_reanalyze_with_existing_cv_returns_analysis(self, s, emp):
        # emp uploaded REAL_CV_PDF in TestUploadAnalysisShape (module-scoped fixtures)
        r = s.post(f"{API}/employee/cv/analyze", headers=H(emp["token"]), timeout=90)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "analysis" in body
        _assert_analysis_shape(body["analysis"])

    def test_reanalyze_does_not_modify_cv(self, s, emp):
        """Downloading the CV after analyze must return the same original bytes."""
        r = s.get(f"{API}/employee/cv", headers=H(emp["token"]))
        assert r.status_code == 200
        assert r.content == REAL_CV_PDF

    def test_reanalyze_blank_pdf_returns_no_text(self, s, emp2):
        # emp2 has the blank PDF uploaded above
        r = s.post(f"{API}/employee/cv/analyze", headers=H(emp2["token"]), timeout=30)
        assert r.status_code == 200, r.text
        a = r.json()["analysis"]
        _assert_analysis_shape(a)
        assert a.get("_warning") == "no_text"


# ---------- 4. Cleanup ----------
class TestZZCleanup:
    def test_cleanup(self, s, admin_token, emp, emp2, emr):
        for uid in (emp["id"], emp2["id"], emr["id"]):
            s.delete(f"{API}/admin/users/{uid}", headers=H(admin_token))
