"""AI Chatbot API — integrates with ML knowledge base and optionally OpenAI."""

from fastapi import APIRouter, Header
from pydantic import BaseModel
from typing import Optional, List
from app.services.ml_service import ml_service
from app.core.config import settings
import logging, os

logger = logging.getLogger(__name__)
router = APIRouter()

_conversation_history: dict = {}  # session_id -> messages


class ChatMessage(BaseModel):
    session_id: str
    message: str
    tenant_id: Optional[str] = "tenant_acme"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    kb_results: list = []
    suggested_actions: list = []
    source: str = "kb"


CANNED_RESPONSES = {
    "password": "To reset your password, visit the self-service portal at /reset or contact your IT admin. For account lockouts, a 15-minute wait usually resolves it automatically.",
    "vpn": "VPN issues are often caused by: (1) Expired certificates – reinstall the VPN client. (2) Firewall blocking port 443. (3) Incorrect server address. Please try reconnecting and if it persists, submit a ticket.",
    "slow": "Slow performance can be caused by high CPU/memory usage, background updates, or network congestion. Try restarting your device first. If it persists, run Task Manager to identify resource-heavy processes.",
    "printer": "Printer offline issues: (1) Check if printer is powered on and connected. (2) Remove and re-add the printer in Settings > Printers. (3) Update the driver from the manufacturer's website.",
    "email": "Email sync issues: (1) Check your internet connection. (2) Verify Outlook is not in Offline mode (Send/Receive tab). (3) Remove and re-add your account. (4) Check available disk space.",
    "access": "For access requests, your manager must submit an approval via the IT portal. Standard turnaround is 1 business day. For emergency access, contact the IT hotline.",
    "install": "Software installations require admin approval. Submit a software request ticket and your IT team will install it within 24 hours. Self-service approved software is available in the Software Center.",
}


def _rule_based_reply(message: str) -> str:
    msg_lower = message.lower()
    for keyword, response in CANNED_RESPONSES.items():
        if keyword in msg_lower:
            return response
    return None


async def _openai_reply(message: str, history: list, kb_context: str) -> str:
    """Call OpenAI GPT with KB context injected as system prompt."""
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        system = f"""You are OpsDesk AI, an intelligent IT support assistant.
Use the following knowledge base context to answer the user's question accurately:

{kb_context}

If the answer isn't in the knowledge base, provide helpful general IT support guidance.
Keep responses concise (2-4 sentences) and actionable. Always suggest creating a ticket if the issue needs human attention."""

        messages = [{"role": "system", "content": system}]
        for h in history[-6:]:  # last 3 exchanges
            messages.append(h)
        messages.append({"role": "user", "content": message})

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return None


@router.post("/message", response_model=ChatResponse)
async def chat(payload: ChatMessage):
    """
    AI chatbot endpoint.
    Flow: KB search → OpenAI (if configured) → rule-based → fallback
    """
    session_id = payload.session_id
    message = payload.message.strip()

    if session_id not in _conversation_history:
        _conversation_history[session_id] = []

    # 1. Search knowledge base
    kb_results = ml_service.search_knowledge_base(message, top_k=3)
    kb_context = "\n\n".join(
        f"[{r.get('category','?')}] {r.get('text_clean','')[:300]}"
        for r in kb_results
    ) if kb_results else "No relevant articles found."

    # 2. Try OpenAI if configured
    reply = None
    source = "kb"
    if settings.OPENAI_API_KEY:
        reply = await _openai_reply(message, _conversation_history[session_id], kb_context)
        if reply:
            source = "openai"

    # 3. Rule-based fallback
    if not reply:
        reply = _rule_based_reply(message)
        if reply:
            source = "rule_based"

    # 4. KB-based reply
    if not reply and kb_results:
        best = kb_results[0]
        reply = f"Based on similar tickets ({best.get('category','IT')} category): {best.get('text_clean','')[:200]}..."
        source = "kb"

    # 5. Final fallback
    if not reply:
        reply = (
            "I don't have a specific answer for that in my knowledge base. "
            "I recommend creating a support ticket so our team can assist you directly. "
            "You can do that by clicking 'New Ticket' in the top navigation."
        )
        source = "fallback"

    # Update history
    _conversation_history[session_id].append({"role": "user", "content": message})
    _conversation_history[session_id].append({"role": "assistant", "content": reply})

    # Suggested actions
    suggested_actions = []
    if source == "fallback":
        suggested_actions.append({"label": "Create a Ticket", "action": "create_ticket"})
    if kb_results:
        suggested_actions.append({"label": "View Similar Tickets", "action": "view_kb"})

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        kb_results=kb_results[:2],
        suggested_actions=suggested_actions,
        source=source,
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    _conversation_history.pop(session_id, None)
    return {"cleared": True}
