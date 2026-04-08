"""Analytics API routes."""

from fastapi import APIRouter, Query, Header
from typing import Optional
from app.services.ticket_service import ticket_service
from app.services.ml_service import ml_service

router = APIRouter()
DEFAULT_TENANT = "tenant_acme"


@router.get("/dashboard")
async def get_dashboard(
    days: int = Query(30, ge=1, le=365),
    x_tenant_id: Optional[str] = Header(None),
):
    """Full dashboard analytics: summary, trends, agent perf, SLA, A/B test results."""
    tenant_id = x_tenant_id or DEFAULT_TENANT
    return ticket_service.get_analytics(tenant_id, days=days)


@router.get("/model-performance")
async def get_model_performance():
    """Return ML model versions and performance metrics."""
    return ml_service.get_model_versions()


@router.get("/sla")
async def get_sla_analytics(
    days: int = Query(30),
    x_tenant_id: Optional[str] = Header(None),
):
    tenant_id = x_tenant_id or DEFAULT_TENANT
    analytics = ticket_service.get_analytics(tenant_id, days=days)
    return {
        "sla_compliance_rate": analytics["summary"]["sla_compliance_rate"],
        "sla_breached_count": analytics["summary"]["sla_breached"],
        "total_tickets": analytics["summary"]["total_tickets"],
        "by_priority": analytics["distributions"]["by_priority"],
    }


@router.get("/ab-test")
async def get_ab_test_results(x_tenant_id: Optional[str] = Header(None)):
    """A/B test comparison: rule-based vs ML routing."""
    from app.services.ticket_service import _ab_results
    rule = [r for r in _ab_results if r.get("group") == "rule_based"]
    ml = [r for r in _ab_results if r.get("group") == "ml_routing"]
    return {
        "rule_based": {"count": len(rule)},
        "ml_routing": {"count": len(ml)},
        "total_experiments": len(_ab_results),
        "recommendation": "ml_routing" if len(ml) > 0 else "rule_based",
    }
