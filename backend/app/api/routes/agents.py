"""Agents API."""
from fastapi import APIRouter
router = APIRouter()

AGENTS = [
    {"id": "a1", "name": "Alice Johnson", "specialties": ["Software", "Email"], "active_tickets": 5, "availability": "online"},
    {"id": "a2", "name": "Bob Martinez", "specialties": ["Network", "VPN"], "active_tickets": 3, "availability": "online"},
    {"id": "a3", "name": "Carol White", "specialties": ["Hardware", "Printing"], "active_tickets": 7, "availability": "busy"},
    {"id": "a4", "name": "David Lee", "specialties": ["Database"], "active_tickets": 2, "availability": "online"},
    {"id": "a5", "name": "Emma Brown", "specialties": ["Cloud"], "active_tickets": 4, "availability": "away"},
    {"id": "a6", "name": "Frank Davis", "specialties": ["Security", "Access Management"], "active_tickets": 6, "availability": "online"},
]

@router.get("")
async def list_agents():
    return AGENTS

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    for a in AGENTS:
        if a["id"] == agent_id:
            return a
    return {"error": "not found"}
