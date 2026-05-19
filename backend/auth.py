import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request, Depends

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_current_user_factory(db):
    async def _get_current_user(request: Request) -> dict:
        token = _extract_token(request)
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.get("blocked"):
            raise HTTPException(status_code=403, detail="Account blocked")
        return user
    return _get_current_user


def require_roles(*roles: str):
    def _checker(user: dict):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _checker


# ----- Brute-force protection -----
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


async def check_lockout(db, identifier: str):
    rec = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if not rec:
        return
    if rec.get("locked_until"):
        locked_until = datetime.fromisoformat(rec["locked_until"])
        if locked_until > datetime.now(timezone.utc):
            secs = int((locked_until - datetime.now(timezone.utc)).total_seconds())
            raise HTTPException(429, f"Too many failed attempts. Try again in {secs}s.")


async def record_failed_attempt(db, identifier: str):
    rec = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0}) or {"identifier": identifier, "count": 0}
    rec["count"] = rec.get("count", 0) + 1
    if rec["count"] >= MAX_ATTEMPTS:
        rec["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
        rec["count"] = 0
    await db.login_attempts.update_one(
        {"identifier": identifier}, {"$set": rec}, upsert=True
    )


async def clear_attempts(db, identifier: str):
    await db.login_attempts.delete_one({"identifier": identifier})
