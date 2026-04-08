"""Webhooks — receive tickets from email/Slack/Zapier."""

from fastapi import APIRouter, Header, Request
from typing import Optional
from app.services.ticket_service import ticket_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/email")
async def receive_email_ticket(request: Request, x_tenant_id: Optional[str] = Header(None)):
    """Simulate receiving a ticket via email webhook (Sendgrid/Mailgun format)."""
    body = await request.json()
    tenant_id = x_tenant_id or "tenant_acme"
    ticket = ticket_service.create_ticket({
        "subject": body.get("subject", "Email ticket"),
        "description": body.get("text", body.get("html", "")),
        "requester_email": body.get("from", ""),
        "requester_name": body.get("from_name", ""),
        "source": "email",
    }, tenant_id)
    logger.info(f"Email webhook → ticket {ticket['id']}")
    return {"ticket_id": ticket["id"], "status": "created"}


@router.post("/generic")
async def receive_generic_webhook(request: Request, x_tenant_id: Optional[str] = Header(None)):
    """Generic webhook — receives JSON payload and creates a ticket."""
    body = await request.json()
    tenant_id = x_tenant_id or "tenant_acme"
    ticket = ticket_service.create_ticket({
        "subject": body.get("subject", body.get("title", "Webhook ticket")),
        "description": body.get("description", body.get("body", "")),
        "priority": body.get("priority", "medium"),
        "category": body.get("category"),
        "requester_email": body.get("email", ""),
        "source": "webhook",
    }, tenant_id)
    return {"ticket_id": ticket["id"], "status": "created"}
