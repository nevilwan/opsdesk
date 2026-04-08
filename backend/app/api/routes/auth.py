"""Auth API — JWT-based authentication."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.config import settings
import hashlib, json

router = APIRouter()

# Demo users (replace with DB lookup in production)
DEMO_USERS = {
    "admin@opsdesk.ai": {"password": "admin123", "name": "Admin User", "role": "admin", "tenant_id": "tenant_acme"},
    "agent@opsdesk.ai": {"password": "agent123", "name": "Agent Smith", "role": "agent", "tenant_id": "tenant_acme"},
    "viewer@opsdesk.ai": {"password": "viewer123", "name": "View Only", "role": "viewer", "tenant_id": "tenant_acme"},
}


class LoginRequest(BaseModel):
    email: str
    password: str


def _make_token(payload: dict) -> str:
    """Simplified JWT-like token (replace with python-jose in production)."""
    import base64
    data = json.dumps({**payload, "exp": (datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)).isoformat()})
    return base64.b64encode(data.encode()).decode()


@router.post("/login")
async def login(payload: LoginRequest):
    user = DEMO_USERS.get(payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _make_token({"email": payload.email, "role": user["role"], "tenant_id": user["tenant_id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": payload.email, "name": user["name"], "role": user["role"], "tenant_id": user["tenant_id"]},
    }


@router.get("/me")
async def me():
    return {"user": "demo", "role": "admin", "tenant_id": "tenant_acme"}
