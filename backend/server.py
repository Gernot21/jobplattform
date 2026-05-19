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
    get_current_user_factory,
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
async def login(payload: LoginIn):
    email = payload.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    if user.get("blocked"):
        raise HTTPException(403, "Account is blocked")
    token = create_access_token(user["id"], user["email"], user["role"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user.get("created_at"),
            "blocked": user.get("blocked", False),
        },
    }


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


def _mount_routes():
    """Mount all protected routes using the now-initialised auth dependency."""

    @api2.get("/")
    async def root():
        return {"status": "ok", "service": "JobPortal 20-80"}

    @api2.get("/auth/me", response_model=UserOut)
    async def auth_me(user: dict = Depends(get_current_user)):
        return UserOut(**user)

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
        if not (20 <= payload.desired_percentage_min <= payload.desired_percentage_max <= 80):
            raise HTTPException(400, "Percentage must be within 20-80 and min<=max")
        existing = await db.employee_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        doc = {
            "id": existing["id"] if existing else _uuid(),
            "user_id": user["id"],
            **payload.model_dump(),
            "updated_at": _now(),
        }
        await db.employee_profiles.update_one(
            {"user_id": user["id"]},
            {"$set": doc},
            upsert=True,
        )
        return doc

    # -------- Employer profile --------
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
    @api2.post("/employer/jobs", response_model=JobOut)
    async def create_job(payload: JobIn, user: dict = Depends(get_current_user)):
        if user["role"] != "employer":
            raise HTTPException(403, "Employer only")
        if not (20 <= payload.percentage_min <= payload.percentage_max <= 80):
            raise HTTPException(400, "Percentage must be within 20-80 and min<=max")
        profile = await db.employer_profiles.find_one({"user_id": user["id"]}, {"_id": 0})
        if not profile:
            raise HTTPException(400, "Please create the employer profile first")
        doc = {
            "id": _uuid(),
            "employer_id": user["id"],
            "company_name": profile.get("company_name", ""),
            **payload.model_dump(),
            "created_at": _now(),
        }
        await db.jobs.insert_one(dict(doc))
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
        # Pull jobs that overlap with desired percentage
        all_jobs = await db.jobs.find({}, {"_id": 0}).to_list(200)
        # Filter percentage overlap
        candidates = [
            j for j in all_jobs
            if not (j["percentage_max"] < profile["desired_percentage_min"]
                    or j["percentage_min"] > profile["desired_percentage_max"])
        ]
        # Compute matching in parallel
        results = await asyncio.gather(*[compute_match(profile, j) for j in candidates])
        out = []
        applied_set = {a["job_id"] for a in await db.applications.find(
            {"employee_id": user["id"]}, {"_id": 0, "job_id": 1}).to_list(500)}
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
