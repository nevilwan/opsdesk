"""Ticket CRUD + AI-powered operations API."""

from fastapi import APIRouter, Query, HTTPException, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.services.ticket_service import ticket_service
from app.services.ml_service import ml_service

router = APIRouter()

# Demo tenant for local dev
DEFAULT_TENANT = "tenant_acme"


def get_tenant(x_tenant_id: Optional[str] = Header(None)) -> str:
    return x_tenant_id or DEFAULT_TENANT


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateTicketRequest(BaseModel):
    subject: str
    description: str = ""
    priority: str = "medium"
    category: Optional[str] = None
    requester_email: str = ""
    requester_name: str = ""
    department: str = ""
    language: str = "en"
    source: str = "api"
    tags: List[str] = []


class UpdateTicketRequest(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_agent: Optional[str] = None
    resolution_notes: Optional[str] = None
    satisfaction_score: Optional[int] = None
    tags: Optional[List[str]] = None


class AddCommentRequest(BaseModel):
    body: str
    author: str = "agent"
    is_internal: bool = False


class ClassifyRequest(BaseModel):
    subject: str
    description: str = ""


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_ticket(
    payload: CreateTicketRequest,
    x_tenant_id: Optional[str] = Header(None)
):
    """
    Create a new ticket. Automatically:
    - Classifies the ticket using ML
    - Routes to the best available agent
    - Predicts resolution time
    - Scores SLA risk
    - Assigns A/B test group
    """
    tenant_id = get_tenant(x_tenant_id)
    ticket = ticket_service.create_ticket(payload.dict(), tenant_id)
    return {"success": True, "ticket": ticket}


@router.get("")
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    x_tenant_id: Optional[str] = Header(None),
):
    """List tickets with filtering and pagination."""
    tenant_id = get_tenant(x_tenant_id)
    return ticket_service.list_tickets(
        tenant_id, status=status, priority=priority,
        category=category, assigned_agent=agent,
        page=page, page_size=page_size
    )


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, x_tenant_id: Optional[str] = Header(None)):
    tenant_id = get_tenant(x_tenant_id)
    t = ticket_service.get_ticket(ticket_id, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    payload: UpdateTicketRequest,
    x_tenant_id: Optional[str] = Header(None),
):
    tenant_id = get_tenant(x_tenant_id)
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    t = ticket_service.update_ticket(ticket_id, updates, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return t


@router.post("/{ticket_id}/escalate")
async def escalate_ticket(
    ticket_id: str,
    reason: str = "",
    x_tenant_id: Optional[str] = Header(None),
):
    tenant_id = get_tenant(x_tenant_id)
    t = ticket_service.escalate_ticket(ticket_id, tenant_id, reason)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"success": True, "ticket": t}


@router.post("/{ticket_id}/comments")
async def add_comment(
    ticket_id: str,
    payload: AddCommentRequest,
    x_tenant_id: Optional[str] = Header(None),
):
    comment = ticket_service.add_comment(
        ticket_id, payload.body, payload.author, payload.is_internal
    )
    return comment


@router.get("/{ticket_id}/comments")
async def get_comments(ticket_id: str):
    return ticket_service.get_comments(ticket_id)


@router.get("/{ticket_id}/events")
async def get_events(ticket_id: str):
    return ticket_service.get_events(ticket_id)


@router.get("/{ticket_id}/explain")
async def explain_routing(ticket_id: str, x_tenant_id: Optional[str] = Header(None)):
    """Return SHAP-style explanation for why this ticket was routed as it was."""
    tenant_id = get_tenant(x_tenant_id)
    t = ticket_service.get_ticket(ticket_id, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
    explanation = ml_service.explain_routing(t["category"], t["priority"])
    return explanation


@router.post("/classify")
async def classify_ticket(payload: ClassifyRequest):
    """
    AI endpoint: classify a ticket before creating it.
    Returns category predictions with confidence scores.
    """
    result = ml_service.classify_ticket(payload.subject, payload.description)
    return result


@router.post("/seed-demo")
async def seed_demo(
    count: int = Query(50, ge=10, le=200),
    x_tenant_id: Optional[str] = Header(None),
):
    """Seed demo ticket data for testing the dashboard."""
    tenant_id = get_tenant(x_tenant_id)
    ids = ticket_service.seed_demo_data(tenant_id, count)
    return {"seeded": len(ids), "tenant_id": tenant_id}
