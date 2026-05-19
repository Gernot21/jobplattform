from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
import asyncio
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_challenge_token,
    decode_token,
    get_current_user_factory,
    check_lockout,
    record_failed_attempt,
    clear_attempts,
)
from models import (
    RegisterIn,
    LoginIn,
    UserOut,
    EmployeeProfileIn,
    EmployerProfileIn,
    JobIn,
    JobOut,
    ApplicationIn,
    SystemUpdateIn,
    _uuid,
    _now,
)
from matching import compute_match
from cv_analyzer import analyze_cv
from subscriptions import TIERS, default_subscription, quota_status, period_key
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionRequest,
)
from twofa import generate_secret, provisioning_uri, qr_data_url, verify_code
from storage import init_storage, put_object, get_object, APP_NAME
import httpx
from fastapi import UploadFile, File
from fastapi.responses import Response

# MongoDB
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# App + Router
app = FastAPI(title="JobPortal 20-80")
api = APIRouter(prefix="/api")

# Auth dependency
get_current_user = None  # set below


# ------------------ Helpers ------------------
def _strip(doc: dict) -> dict:
    if not doc:
        return doc
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


async def _get_user_or_404(user_id: str) -> dict:
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ------------------ Auth Routes ------------------
@api.post("/auth/register")
async def register(payload: RegisterIn):
    if payload.role not in ("employee", "employer"):
        raise HTTPException(400, "Role must be employee or employer")
    email = payload.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(409, "Email already registered")
    user_doc = {
        "id": _uuid(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "created_at": _now(),
        "blocked": False,
    }
    await db.users.insert_one(dict(user_doc))
    token = create_access_token(user_doc["id"], email, payload.role)
    return {
        "token": token,
        "user": {
            "id": user_doc["id"],
            "email": email,
            "role": payload.role,
            "created_at": user_doc["created_at"],
            "blocked": False,
        },
    }


@api.post("/auth/login")
async def login(payload: LoginIn, request: Request):
    """Email/password login. UI exposes this only for admins; kept enabled for legacy + integration tests."""
    email = payload.email.lower()
    identifier = email
    await check_lockout(db, identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        await record_failed_attempt(db, identifier)
        raise HTTPException(401, "Invalid email or password")
    if user.get("blocked"):
        raise HTTPException(403, "Account is blocked")
    await clear_attempts(db, identifier)

    if user.get("totp_enabled"):
        return {
            "requires_2fa": True,
            "challenge_token": create_challenge_token(user["id"]),
        }

    token = create_access_token(user["id"], user["email"], user["role"])
    return {
        "token": token,
        "user": _public_user(user),
    }


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "totp_enabled": bool(user.get("totp_enabled", False)),
        "needs_onboarding": user.get("role") is None,
        "created_at": user.get("created_at"),
        "blocked": user.get("blocked", False),
    }


# ----- Google OAuth exchange (Emergent-managed) -----
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


@api.post("/auth/google/exchange")
async def google_exchange(payload: dict):
    """Exchange Emergent session_id (from URL fragment) for our JWT.

    Body: { "session_id": "..." }
    If user is new or has no role yet, returns needs_onboarding=true.
    If user has 2FA enabled, returns requires_2fa + challenge_token.
    """
    session_id = (payload or {}).get("session_id")
    if not session_id:
        raise HTTPException(400, "session_id required")

    async with httpx.AsyncClient(timeout=10.0) as cli:
        r = await cli.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id})
        if r.status_code != 200:
            raise HTTPException(401, "Invalid or expired Google session")
        data = r.json()

    email = (data.get("email") or "").lower()
    name = data.get("name") or ""
    picture = data.get("picture") or ""
    google_id = data.get("id") or ""
    if not email:
        raise HTTPException(400, "Email missing from Google session")

    user = await db.users.find_one({"email": email})
    if not user:
        user = {
            "id": _uuid(),
            "email": email,
            "role": None,  # selected during onboarding
            "name": name,
            "picture": picture,
            "google_id": google_id,
            "auth_provider": "google",
            "totp_enabled": False,
            "totp_secret": None,
            "created_at": _now(),
            "blocked": False,
        }
        await db.users.insert_one(dict(user))
    else:
        # Update profile info on every login
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture, "google_id": google_id, "auth_provider": user.get("auth_provider") or "google"}},
        )
        user = await db.users.find_one({"email": email})

    if user.get("blocked"):
        raise HTTPException(403, "Account is blocked")

    if user.get("totp_enabled"):
        return {
            "requires_2fa": True,
            "challenge_token": create_challenge_token(user["id"]),
            "needs_onboarding": user.get("role") is None,
        }

    token = create_access_token(user["id"], user["email"], user.get("role") or "")
    return {"token": token, "user": _public_user(user)}


# ----- 2FA second step -----
@api.post("/auth/2fa/login")
async def twofa_login(payload: dict):
    """Verify TOTP code with challenge token. Returns full access token on success."""
    challenge = (payload or {}).get("challenge_token")
    code = (payload or {}).get("code")
    if not challenge or not code:
        raise HTTPException(400, "challenge_token and code required")
    data = decode_token(challenge)
    if data.get("type") != "2fa_challenge":
        raise HTTPException(401, "Invalid challenge token")
    user = await db.users.find_one({"id": data["sub"]})
    if not user or not user.get("totp_enabled"):
        raise HTTPException(400, "2FA not enabled")
    if not verify_code(user.get("totp_secret"), code):
        raise HTTPException(401, "Invalid 2FA code")
    token = create_access_token(user["id"], user["email"], user.get("role") or "")
    return {"token": token, "user": _public_user(user)}


# ============ Protected routes are registered at startup ============
api2 = APIRouter(prefix="/api")


@app.on_event("startup")
async def on_startup():
    global get_current_user
    get_current_user = await get_current_user_factory(db)

    # Indexes
    await db.users.create_index("email", unique=True)
    await db.jobs.create_index("employer_id")
    await db.applications.create_index([("job_id", 1), ("employee_id", 1)], unique=True)

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@jobportal.ch").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": _uuid(),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "created_at": _now(),
            "blocked": False,
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )

    # Mount real routes
    _mount_routes()
    app.include_router(api2)

    # Object storage init (non-fatal if it fails – uploads will just error)
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.warning("Storage init failed (uploads disabled): %s", e)


def _mount_routes():
    """Mount all protected routes using the now-initialised auth dependency."""

    @api2.get("/")
    async def root():
        return {"status": "ok", "service": "JobPortal 20-80"}

    @api2.get("/auth/me")
    async def auth_me(user: dict = Depends(get_current_user)):
        return _public_user(user)

    # ---- Onboarding (set role for Google users) ----
    @api2.post("/auth/onboarding")
    async def onboarding(payload: dict, user: dict = Depends(get_current_user)):
        role = (payload or {}).get("role")
        if role not in ("employee", "employer"):
            raise HTTPException(400, "Role must be employee or employer")
        if user.get("role") in ("employee", "employer", "admin"):
            raise HTTPException(400, "Role already set")
        await db.users.update_one({"id": user["id"]}, {"$set": {"role": role}})
        fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
        token = create_access_token(fresh["id"], fresh["email"], role)
        return {"token": token, "user": _public_user(fresh)}

    # ---- 2FA management ----
    @api2.post("/auth/2fa/setup")
    async def twofa_setup(user: dict = Depends(get_current_user)):
        """Generate (and persist as pending) a TOTP secret and QR code."""
        if user.get("totp_enabled"):
            raise HTTPException(400, "2FA already enabled")
        secret = generate_secret()
        # Persist pending secret on user (NOT enabled yet)
        await db.users.update_one({"id": user["id"]}, {"$set": {"totp_secret_pending": secret}})
        uri = provisioning_uri(secret, user["email"])
        return {"secret": secret, "otpauth_uri": uri, "qr_data_url": qr_data_url(uri)}

    @api2.post("/auth/2fa/enable")
    async def twofa_enable(payload: dict, user: dict = Depends(get_current_user)):
        code = (payload or {}).get("code")
        full = await db.users.find_one({"id": user["id"]})
        secret = full.get("totp_secret_pending")
        if not secret:
            raise HTTPException(400, "Run /auth/2fa/setup first")
        if not verify_code(secret, code):
            raise HTTPException(401, "Invalid 2FA code")
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$set": {"totp_enabled": True, "totp_secret": secret},
                "$unset": {"totp_secret_pending": ""},
            },
        )
        return {"enabled": True}

    @api2.post("/auth/2fa/disable")
    async def twofa_disable(payload: dict, user: dict = Depends(get_current_user)):
        code = (payload or {}).get("code")
        full = await db.users.find_one({"id": user["id"]})
        if not full.get("totp_enabled"):
            raise HTTPException(400, "2FA not enabled")
        if not verify_code(full.get("totp_secret"), code):
            raise HTTPException(401, "Invalid 2FA code")
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$set": {"totp_enabled": False},
                "$unset": {"totp_secret": "", "totp_secret_pending": ""},
            },
        )
        return {"enabled": False}

    # -------- Employee profile --------
    @api2.get("/employee/profile")
    async def emp_get_profile(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        prof = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        return prof or {}

    @api2.put("/employee/profile")
    async def emp_put_profile(payload: EmployeeProfileIn, user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        allowed_steps = {20, 30, 40, 50, 60, 70, 80}
        if (payload.desired_percentage_min not in allowed_steps
                or payload.desired_percentage_max not in allowed_steps):
            raise HTTPException(400, "Pensum must be one of 20,30,40,50,60,70,80")
        if payload.desired_percentage_min > payload.desired_percentage_max:
            raise HTTPException(400, "min must be <= max")
        existing = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        doc = {
            "id": existing["id"] if existing else _uuid(),
            "user_id": user["id"],
            **payload.model_dump(),
            "updated_at": _now(),
        }
        # Preserve CV fields if present
        if existing:
            for k in ("cv_filename", "cv_size", "cv_uploaded_at", "cv_storage_path"):
                if k in existing and k not in doc:
                    doc[k] = existing[k]
        await db.employee_profiles.update_one(
            {"user_id": user["id"]},
            {"$set": doc},
            upsert=True,
        )
        return doc

    # ---- Employee CV upload (PDF max 15 MB) ----
    MAX_CV_BYTES = 15 * 1024 * 1024

    @api2.post("/employee/cv")
    async def upload_cv(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        if (file.content_type or "").lower() != "application/pdf":
            raise HTTPException(400, "Only PDF files are accepted")
        data = await file.read()
        if len(data) == 0:
            raise HTTPException(400, "Empty file")
        if len(data) > MAX_CV_BYTES:
            raise HTTPException(413, "File exceeds 15 MB limit")
        path = f"{APP_NAME}/cv/{user['id']}/{_uuid()}.pdf"
        try:
            result = put_object(path, data, "application/pdf")
        except Exception as e:
            logger.exception("CV upload failed: %s", e)
            raise HTTPException(502, "Storage temporarily unavailable")
        storage_path = result.get("path", path)
        await db.employee_profiles.update_one(
            {"user_id": user["id"]},
            {"$set": {
                "cv_filename": file.filename or "lebenslauf.pdf",
                "cv_size": len(data),
                "cv_uploaded_at": _now(),
                "cv_storage_path": storage_path,
            }},
            upsert=True,
        )
        # Trigger AI analysis (best-effort; does not block error on LLM failure)
        analysis = await analyze_cv(data)
        return {
            "filename": file.filename,
            "size": len(data),
            "uploaded_at": _now(),
            "analysis": analysis,
        }

    @api2.post("/employee/cv/analyze")
    async def reanalyze_cv(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        prof = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if not prof or not prof.get("cv_storage_path"):
            raise HTTPException(404, "No CV uploaded")
        try:
            data, _ = get_object(prof["cv_storage_path"])
        except Exception as e:
            logger.exception("CV download for analysis failed: %s", e)
            raise HTTPException(502, "Storage temporarily unavailable")
        analysis = await analyze_cv(data)
        return {"analysis": analysis}

    @api2.delete("/employee/cv")
    async def delete_cv(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        await db.employee_profiles.update_one(
            {"user_id": user["id"]},
            {"$unset": {
                "cv_filename": "",
                "cv_size": "",
                "cv_uploaded_at": "",
                "cv_storage_path": "",
            }},
        )
        return {"deleted": True}

    @api2.get("/employee/cv")
    async def download_own_cv(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        prof = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if not prof or not prof.get("cv_storage_path"):
            raise HTTPException(404, "No CV uploaded")
        try:
            data, ctype = get_object(prof["cv_storage_path"])
        except Exception as e:
            logger.exception("CV download failed: %s", e)
            raise HTTPException(502, "Storage temporarily unavailable")
        return Response(content=data, media_type="application/pdf", headers={
            "Content-Disposition": f'inline; filename="{prof.get("cv_filename","lebenslauf.pdf")}"',
        })

    @api2.get("/employer/applicants/{employee_id}/cv")
    async def employer_download_cv(employee_id: str, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        # Only allow access if the employee has applied to one of THIS employer's jobs
        my_job_ids = [j["id"] for j in await db.jobs.find({"employer_id": user["id"]}, {"_id": 0, "id": 1}).to_list(500)]
        app_doc = await db.applications.find_one({
            "employee_id": employee_id,
            "job_id": {"$in": my_job_ids},
        }, {"_id": 0})
        if not app_doc:
            raise HTTPException(403, "Applicant has not applied to your jobs")
        prof = await db.employee_profiles.find_one({"user_id": employee_id}, {"_id": 0})
        if not prof or not prof.get("cv_storage_path"):
            raise HTTPException(404, "No CV available")
        try:
            data, ctype = get_object(prof["cv_storage_path"])
        except Exception as e:
            logger.exception("CV download failed: %s", e)
            raise HTTPException(502, "Storage temporarily unavailable")
        return Response(content=data, media_type="application/pdf", headers={
            "Content-Disposition": f'inline; filename="{prof.get("cv_filename","lebenslauf.pdf")}"',
        })
    @api2.get("/employer/profile")
    async def empr_get_profile(user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        prof = await db.employer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        return prof or {}

    @api2.put("/employer/profile")
    async def empr_put_profile(payload: EmployerProfileIn, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        existing = await db.employer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        doc = {
            "id": existing["id"] if existing else _uuid(),
            "user_id": user["id"],
            **payload.model_dump(),
            "updated_at": _now(),
        }
        await db.employer_profiles.update_one(
            {"user_id": user["id"]},
            {"$set": doc},
            upsert=True,
        )
        return doc

    # -------- Jobs CRUD --------
    async def _get_or_create_subscription(user_id: str) -> dict:
        sub = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
        if not sub:
            sub = default_subscription(user_id)
            await db.subscriptions.insert_one(dict(sub))
        # Period rollover refresh
        tier = TIERS[sub["tier_id"]]
        cur_key = period_key(tier["period"])
        if sub.get("current_period_key") != cur_key:
            sub["current_period_key"] = cur_key
            sub["postings_used"] = 0
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {"current_period_key": cur_key, "postings_used": 0}},
            )
        return sub

    @api2.post("/employer/jobs", response_model=JobOut)
    async def create_job(payload: JobIn, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        if not (20 <= payload.percentage_min <= payload.percentage_max <= 80):
            raise HTTPException(400, "Percentage must be within 20-80 and min<=max")
        profile = await db.employer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if not profile:
            raise HTTPException(400, "Please create the employer profile first")
        # Quota check
        sub = await _get_or_create_subscription(user["id"])
        status = quota_status(sub)
        if not status["can_post"]:
            raise HTTPException(
                402,
                f"Inserate-Kontingent für '{status['tier']['name']}' erreicht "
                f"({sub['postings_used']}/{status['tier']['max_postings']}). "
                f"Bitte Abo upgraden.",
            )
        doc = {
            "id": _uuid(),
            "employer_id": user["id"],
            "company_name": profile.get("company_name", ""),
            **payload.model_dump(),
            "created_at": _now(),
        }
        await db.jobs.insert_one(dict(doc))
        # Bump usage
        await db.subscriptions.update_one(
            {"user_id": user["id"]},
            {"$inc": {"postings_used": 1}, "$set": {"updated_at": _now()}},
        )
        doc.pop("_id", None)
        return doc

    @api2.get("/employer/jobs")
    async def list_my_jobs(user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        jobs = await db.jobs.find({"employer_id": user["id"]}, {"_id": 0}).to_list(500)
        return jobs

    @api2.delete("/employer/jobs/{job_id}")
    async def delete_job(job_id: str, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        res = await db.jobs.delete_one({"id": job_id, "employer_id": user["id"]})
        if res.deleted_count == 0:
            raise HTTPException(404, "Job not found")
        await db.applications.delete_many({"job_id": job_id})
        return {"deleted": True}

    @api2.get("/employer/jobs/{job_id}/applicants")
    async def list_applicants(job_id: str, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        job = await db.jobs.find_one({"id": job_id, "employer_id": user["id"]}, {"_id": 0})
        if not job:
            raise HTTPException(404, "Job not found")
        apps = await db.applications.find({"job_id": job_id}, {"_id": 0}).to_list(500)
        # enrich
        result = []
        for a in apps:
            prof = await db.employee_profiles.find_one({"user_id": a["employee_id"]}, {"_id": 0})
            usr = await db.users.find_one({"id": a["employee_id"]}, {"_id": 0, "password_hash": 0})
            result.append({**a, "profile": prof or {}, "email": usr["email"] if usr else ""})
        result.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return result

    # -------- Employee: jobs feed & apply --------
    @api2.get("/employee/jobs/suggested")
    async def suggested_jobs(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        profile = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if not profile:
            return []
        all_jobs = await db.jobs.find({}, {"_id": 0}).to_list(500)
        candidates = [
            j for j in all_jobs
            if not (j["percentage_max"] < profile["desired_percentage_min"]
                    or j["percentage_min"] > profile["desired_percentage_max"])
        ]
        # Top-K pre-filter: cheap keyword overlap to limit LLM cost
        TOP_K = 15

        def _tokens(text: str) -> set:
            import re
            return {w for w in re.findall(r"[\wäöüÄÖÜßéèà]+", (text or "").lower()) if len(w) > 2}

        profile_tokens = (
            _tokens(profile.get("looking_for", ""))
            | _tokens(profile.get("core_skills", ""))
            | _tokens(profile.get("key_experiences", ""))
        )

        def _overlap(job):
            jt = _tokens(job.get("title", "")) | _tokens(job.get("description", ""))
            if not profile_tokens or not jt:
                return 0
            return len(profile_tokens & jt)

        candidates.sort(key=_overlap, reverse=True)
        candidates = candidates[:TOP_K]

        results = await asyncio.gather(*[compute_match(profile, j) for j in candidates])
        applied_set = {a["job_id"] for a in await db.applications.find(
            {"employee_id": user["id"]}, {"_id": 0, "job_id": 1}).to_list(500)}
        out = []
        for job, match in zip(candidates, results):
            out.append({
                **job,
                "match_score": match["score"],
                "match_reason": match["reason"],
                "match_highlights": match["highlights"],
                "already_applied": job["id"] in applied_set,
            })
        out.sort(key=lambda x: x["match_score"], reverse=True)
        return out

    @api2.post("/employee/applications")
    async def apply(payload: ApplicationIn, user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        job = await db.jobs.find_one({"id": payload.job_id}, {"_id": 0})
        if not job:
            raise HTTPException(404, "Job not found")
        existing = await db.applications.find_one({"job_id": payload.job_id, "employee_id": user["id"]})
        if existing:
            raise HTTPException(409, "Already applied")
        profile = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        match = await compute_match(profile or {}, job) if profile else {"score": 0}
        doc = {
            "id": _uuid(),
            "job_id": payload.job_id,
            "employee_id": user["id"],
            "cover_letter": payload.cover_letter or "",
            "match_score": match["score"],
            "status": "submitted",
            "applied_at": _now(),
        }
        await db.applications.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api2.get("/employee/applications")
    async def my_applications(user: dict = Depends(get_current_user)):
        if user["role"] != "employee":
            raise HTTPException(403, "Employee only")
        apps = await db.applications.find({"employee_id": user["id"]}, {"_id": 0}).to_list(500)
        out = []
        for a in apps:
            job = await db.jobs.find_one({"id": a["job_id"]}, {"_id": 0})
            out.append({**a, "job": job or {}})
        out.sort(key=lambda x: x.get("applied_at", ""), reverse=True)
        return out

    # -------- Subscriptions & Stripe --------
    @api2.get("/tiers")
    async def list_tiers():
        return list(TIERS.values())

    @api2.get("/employer/subscription")
    async def get_subscription(user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        sub = await _get_or_create_subscription(user["id"])
        return quota_status(sub)

    @api2.post("/employer/checkout")
    async def create_checkout(payload: dict, request: Request, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        tier_id = payload.get("tier_id")
        origin_url = payload.get("origin_url", "").rstrip("/")
        if tier_id not in TIERS or tier_id == "tier_1":
            raise HTTPException(400, "Invalid tier")
        if not origin_url:
            raise HTTPException(400, "origin_url required")
        tier = TIERS[tier_id]

        api_key = os.environ["STRIPE_API_KEY"]
        host_url = str(request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

        success_url = f"{origin_url}/employer?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/employer?cancelled=1"
        metadata = {
            "user_id": user["id"],
            "tier_id": tier_id,
            "purpose": "employer_subscription",
        }
        req = CheckoutSessionRequest(
            amount=float(tier["price"]),
            currency=tier["currency"],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
        )
        session = await stripe.create_checkout_session(req)
        await db.payment_transactions.insert_one({
            "id": _uuid(),
            "session_id": session.session_id,
            "user_id": user["id"],
            "tier_id": tier_id,
            "amount": float(tier["price"]),
            "currency": tier["currency"],
            "metadata": metadata,
            "payment_status": "pending",
            "status": "initiated",
            "created_at": _now(),
        })
        return {"url": session.url, "session_id": session.session_id}

    @api2.get("/payments/status/{session_id}")
    async def payment_status(session_id: str, request: Request, user: dict = Depends(get_current_user)):
        tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if not tx:
            raise HTTPException(404, "Transaction not found")
        if tx["user_id"] != user["id"]:
            raise HTTPException(403, "Forbidden")

        # Already finalised? Just return.
        if tx["payment_status"] == "paid":
            return {"payment_status": "paid", "status": "complete", "tier_id": tx["tier_id"]}

        api_key = os.environ["STRIPE_API_KEY"]
        host_url = str(request.base_url)
        stripe = StripeCheckout(api_key=api_key, webhook_url=f"{host_url}api/webhook/stripe")
        try:
            result = await stripe.get_checkout_status(session_id)
        except Exception as e:
            logger.warning("Stripe status lookup failed for %s: %s", session_id, e)
            return {
                "payment_status": tx.get("payment_status", "pending"),
                "status": tx.get("status", "initiated"),
                "tier_id": tx["tier_id"],
            }

        new_status = result.status
        new_pay = result.payment_status
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": new_status, "payment_status": new_pay, "updated_at": _now()}},
        )
        # Activate subscription only once
        if new_pay == "paid" and tx["payment_status"] != "paid":
            await db.subscriptions.update_one(
                {"user_id": tx["user_id"]},
                {"$set": {
                    "tier_id": tx["tier_id"],
                    "current_period_key": period_key(TIERS[tx["tier_id"]]["period"]),
                    "postings_used": 0,
                    "updated_at": _now(),
                }},
                upsert=True,
            )
        return {"payment_status": new_pay, "status": new_status, "tier_id": tx["tier_id"]}

    # -------- Admin --------
    def _require_admin(user: dict):
        if user.get("role") != "admin":
            raise HTTPException(403, "Admin only")
        return user

    @api2.get("/admin/users")
    async def admin_list_users(user: dict = Depends(get_current_user)):
        _require_admin(user)
        users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
        return users

    @api2.post("/admin/users/{user_id}/block")
    async def admin_block_user(user_id: str, blocked: bool = True, user: dict = Depends(get_current_user)):
        _require_admin(user)
        res = await db.users.update_one({"id": user_id}, {"$set": {"blocked": blocked}})
        if res.matched_count == 0:
            raise HTTPException(404, "User not found")
        return {"blocked": blocked}

    @api2.delete("/admin/users/{user_id}")
    async def admin_delete_user(user_id: str, user: dict = Depends(get_current_user)):
        _require_admin(user)
        target = await db.users.find_one({"id": user_id})
        if not target:
            raise HTTPException(404, "User not found")
        if target.get("role") == "admin":
            raise HTTPException(400, "Cannot delete admin")
        await db.users.delete_one({"id": user_id})
        await db.employee_profiles.delete_many({"user_id": user_id})
        await db.employer_profiles.delete_many({"user_id": user_id})
        await db.jobs.delete_many({"employer_id": user_id})
        await db.applications.delete_many({"employee_id": user_id})
        return {"deleted": True}

    @api2.get("/admin/stats")
    async def admin_stats(user: dict = Depends(get_current_user)):
        _require_admin(user)
        return {
            "users": await db.users.count_documents({}),
            "employees": await db.users.count_documents({"role": "employee"}),
            "employers": await db.users.count_documents({"role": "employer"}),
            "jobs": await db.jobs.count_documents({}),
            "applications": await db.applications.count_documents({}),
        }

    @api2.get("/admin/updates")
    async def admin_list_updates(environment: Optional[str] = None, user: dict = Depends(get_current_user)):
        _require_admin(user)
        q = {}
        if environment:
            q["environment"] = environment
        updates = await db.system_updates.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
        return updates

    @api2.post("/admin/updates")
    async def admin_create_update(payload: SystemUpdateIn, user: dict = Depends(get_current_user)):
        _require_admin(user)
        if payload.environment not in ("test", "production"):
            raise HTTPException(400, "environment must be test or production")
        doc = {
            "id": _uuid(),
            **payload.model_dump(),
            "created_at": _now(),
        }
        await db.system_updates.insert_one(dict(doc))
        doc.pop("_id", None)
        return doc

    @api2.delete("/admin/updates/{update_id}")
    async def admin_delete_update(update_id: str, user: dict = Depends(get_current_user)):
        _require_admin(user)
        res = await db.system_updates.delete_one({"id": update_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Update not found")
        return {"deleted": True}

    @api2.post("/admin/updates/{update_id}/publish")
    async def admin_publish_update(update_id: str, user: dict = Depends(get_current_user)):
        _require_admin(user)
        res = await db.system_updates.update_one(
            {"id": update_id},
            {"$set": {"published": True, "environment": "production"}},
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Update not found")
        return {"published": True}

    # Public: list published prod updates (visible to all logged-in users)
    @api2.get("/updates/published")
    async def list_published_updates(user: dict = Depends(get_current_user)):
        updates = await db.system_updates.find(
            {"published": True, "environment": "production"},
            {"_id": 0},
        ).sort("created_at", -1).to_list(50)
        return updates

    # Public Stripe webhook (no auth)
    @api2.post("/webhook/stripe")
    async def stripe_webhook(request: Request):
        api_key = os.environ["STRIPE_API_KEY"]
        host_url = str(request.base_url)
        stripe = StripeCheckout(api_key=api_key, webhook_url=f"{host_url}api/webhook/stripe")
        body = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        try:
            evt = await stripe.handle_webhook(body, signature)
        except Exception as e:
            logger.exception("Webhook error: %s", e)
            raise HTTPException(400, "Invalid webhook")
        tx = await db.payment_transactions.find_one({"session_id": evt.session_id}, {"_id": 0})
        if not tx:
            return {"ok": True}
        if evt.payment_status == "paid" and tx["payment_status"] != "paid":
            await db.payment_transactions.update_one(
                {"session_id": evt.session_id},
                {"$set": {"payment_status": "paid", "status": "complete", "updated_at": _now()}},
            )
            await db.subscriptions.update_one(
                {"user_id": tx["user_id"]},
                {"$set": {
                    "tier_id": tx["tier_id"],
                    "current_period_key": period_key(TIERS[tx["tier_id"]]["period"]),
                    "postings_used": 0,
                    "updated_at": _now(),
                }},
                upsert=True,
            )
        return {"ok": True}


# Mount the initial (auth) router
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown():
    client.close()
