"""Knowledge Base API — semantic search over resolved tickets."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.ml_service import ml_service

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.get("/search")
async def search_knowledge_base(
    q: str = Query(..., min_length=2),
    top_k: int = Query(5, ge=1, le=20),
):
    """Semantic search over the knowledge base."""
    results = ml_service.search_knowledge_base(q, top_k=top_k)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/articles")
async def list_articles():
    """Return sample KB articles (generated from resolved tickets)."""
    return {
        "articles": [
            {
                "id": 1, "title": "How to reset your password",
                "category": "Access Management",
                "body": "Visit the self-service portal or contact IT admin.",
                "view_count": 342, "helpful_count": 298,
            },
            {
                "id": 2, "title": "VPN troubleshooting guide",
                "category": "VPN",
                "body": "Reinstall the VPN client, check firewall settings.",
                "view_count": 215, "helpful_count": 180,
            },
            {
                "id": 3, "title": "Outlook sync issues",
                "category": "Email",
                "body": "Disable Offline Mode, re-add account, check disk space.",
                "view_count": 190, "helpful_count": 165,
            },
        ]
    }
