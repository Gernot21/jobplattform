from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str  # "employee" or "employer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: EmailStr
    role: Optional[str] = None
    name: Optional[str] = ""
    picture: Optional[str] = ""
    totp_enabled: Optional[bool] = False
    needs_onboarding: Optional[bool] = False
    created_at: Optional[str] = None
    blocked: Optional[bool] = False


# ---------- Employee Profile ----------
class EmployeeProfileIn(BaseModel):
    first_name: str
    last_name: str
    core_skills: str
    key_experiences: str
    looking_for: str
    why_consider: Optional[str] = ""
    desired_percentage_min: int = 20
    desired_percentage_max: int = 80


class EmployeeProfileOut(EmployeeProfileIn):
    id: str
    user_id: str
    updated_at: str
    cv_filename: Optional[str] = None
    cv_size: Optional[int] = None
    cv_uploaded_at: Optional[str] = None


# ---------- Employer Profile ----------
class EmployerProfileIn(BaseModel):
    company_name: str
    company_description: str
    contact_person: str
    contact_email: EmailStr


class EmployerProfileOut(EmployerProfileIn):
    id: str
    user_id: str
    updated_at: str


# ---------- Jobs ----------
class JobIn(BaseModel):
    title: str
    description: str
    percentage_min: int = Field(ge=20, le=80)
    percentage_max: int = Field(ge=20, le=80)
    location: Optional[str] = ""


class JobOut(JobIn):
    id: str
    employer_id: str
    company_name: Optional[str] = ""
    created_at: str


# ---------- Applications ----------
class ApplicationIn(BaseModel):
    job_id: str
    cover_letter: Optional[str] = ""


class ApplicationOut(BaseModel):
    id: str
    job_id: str
    employee_id: str
    cover_letter: Optional[str] = ""
    match_score: Optional[float] = 0.0
    status: str = "submitted"
    applied_at: str


# ---------- System Updates (Admin) ----------
class SystemUpdateIn(BaseModel):
    title: str
    content: str
    environment: str = "test"  # "test" or "production"
    published: bool = False


class SystemUpdateOut(SystemUpdateIn):
    id: str
    created_at: str
