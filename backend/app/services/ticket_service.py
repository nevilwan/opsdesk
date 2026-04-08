"""
OpsDesk AI — Ticket Service
Business logic for ticket lifecycle management.
Handles creation, routing, SLA tracking, escalation, and analytics.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
import random

from app.services.ml_service import ml_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory store (replace with PostgreSQL via SQLAlchemy in production)
_tickets: Dict[str, dict] = {}
_events: List[dict] = []
_comments: List[dict] = []
_ab_results: List[dict] = []

SLA_HOURS = {
    "critical": settings.SLA_CRITICAL_HOURS,
    "high": settings.SLA_HIGH_HOURS,
    "medium": settings.SLA_MEDIUM_HOURS,
    "low": settings.SLA_LOW_HOURS,
}


def generate_ticket_id() -> str:
    return f"TKT-{random.randint(10000, 99999)}"


def _log_event(ticket_id: str, event_type: str, actor: str, payload: dict = None):
    _events.append({
        "ticket_id": ticket_id,
        "event_type": event_type,
        "actor": actor,
        "payload": payload or {},
        "created_at": datetime.utcnow().isoformat(),
    })


class TicketService:

    def create_ticket(self, data: dict, tenant_id: str, use_ab: bool = False) -> dict:
        """
        Create a new ticket with full AI processing:
        - ML classification
        - Intelligent routing
        - Resolution time prediction
        - SLA risk scoring
        - A/B test group assignment
        """
        ticket_id = generate_ticket_id()
        now = datetime.utcnow()

        subject = data.get("subject", "")
        description = data.get("description", "")
        priority = data.get("priority", "medium")
        category_override = data.get("category")

        # A/B test assignment (50/50 split)
        ab_group = "rule_based" if random.random() < 0.5 else "ml_routing"

        # AI Classification
        if category_override:
            classification = {
                "category": category_override,
                "confidence": 1.0,
                "method": "manual",
                "top_predictions": [],
            }
        else:
            classification = ml_service.classify_ticket(
                subject, description,
                use_ab_variant=(ab_group == "ml_routing")
            )

        category = classification["category"]

        # AI Routing
        routing = ml_service.route_ticket(
            category, priority,
            department=data.get("department", ""),
            use_ml=(ab_group == "ml_routing"),
        )

        # Resolution prediction
        resolution_pred = ml_service.predict_resolution_time(
            category, priority, f"{subject} {description}"
        )

        # SLA risk scoring
        sla_risk = ml_service.score_sla_risk(
            category, priority, len(f"{subject} {description}")
        )

        # SLA deadline
        sla_hours = SLA_HOURS.get(priority.lower(), 24)
        sla_deadline = now + timedelta(hours=sla_hours)

        # Explainability
        explanation = ml_service.explain_routing(category, priority)

        ticket = {
            "id": ticket_id,
            "tenant_id": tenant_id,
            "subject": subject,
            "description": description,
            "category": category,
            "priority": priority,
            "status": "open",
            "requester_email": data.get("requester_email", ""),
            "requester_name": data.get("requester_name", ""),
            "department": data.get("department", ""),
            "assigned_agent": routing["assigned_agent"],
            "language": data.get("language", "en"),
            "source": data.get("source", "api"),
            "tags": data.get("tags", []),

            # AI metadata
            "ai_category": classification["category"],
            "ai_category_confidence": classification["confidence"],
            "ai_classification_method": classification["method"],
            "ai_predicted_resolution_hours": resolution_pred["predicted_hours"],
            "ai_sla_risk": sla_risk,
            "routing_method": routing["routing_method"],
            "routing_confidence": routing.get("confidence"),
            "explanation": explanation,

            # SLA
            "sla_target_hours": sla_hours,
            "sla_deadline": sla_deadline.isoformat(),
            "sla_breached": False,
            "escalated": routing.get("escalate", False),
            "escalation_count": 1 if routing.get("escalate") else 0,

            # A/B
            "ab_test_group": ab_group,

            # Timestamps
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "first_response_at": None,
            "resolved_at": None,
            "resolution_hours": None,
            "satisfaction_score": None,
        }

        _tickets[ticket_id] = ticket
        _log_event(ticket_id, "created", data.get("requester_email", "system"), {
            "category": category,
            "priority": priority,
            "routing_method": routing["routing_method"],
        })

        # Track A/B result placeholder
        _ab_results.append({
            "ticket_id": ticket_id,
            "group": ab_group,
            "routing_method": routing["routing_method"],
            "category": category,
            "priority": priority,
            "created_at": now.isoformat(),
        })

        logger.info(f"Ticket {ticket_id} created — category={category} agent={routing['assigned_agent']} ab={ab_group}")
        return ticket

    def get_ticket(self, ticket_id: str, tenant_id: str) -> Optional[dict]:
        t = _tickets.get(ticket_id)
        if t and t["tenant_id"] == tenant_id:
            return t
        return None

    def list_tickets(self, tenant_id: str, status: str = None,
                     priority: str = None, category: str = None,
                     assigned_agent: str = None, page: int = 1,
                     page_size: int = 25) -> dict:
        results = [
            t for t in _tickets.values()
            if t["tenant_id"] == tenant_id
            and (not status or t["status"] == status)
            and (not priority or t["priority"] == priority)
            and (not category or t["category"] == category)
            and (not assigned_agent or t.get("assigned_agent") == assigned_agent)
        ]
        results.sort(key=lambda x: x["created_at"], reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        page_items = results[start:start + page_size]
        return {"tickets": page_items, "total": total, "page": page, "page_size": page_size}

    def update_ticket(self, ticket_id: str, updates: dict,
                      tenant_id: str, actor: str = "system") -> Optional[dict]:
        t = self.get_ticket(ticket_id, tenant_id)
        if not t:
            return None

        now = datetime.utcnow()
        old_status = t["status"]

        # Apply updates
        allowed = ["subject", "description", "category", "priority",
                   "status", "assigned_agent", "tags", "resolution_notes",
                   "satisfaction_score", "department"]
        for k, v in updates.items():
            if k in allowed:
                t[k] = v
        t["updated_at"] = now.isoformat()

        # Handle status transitions
        new_status = updates.get("status")
        if new_status == "resolved" and old_status != "resolved":
            t["resolved_at"] = now.isoformat()
            created = datetime.fromisoformat(t["created_at"])
            t["resolution_hours"] = round((now - created).total_seconds() / 3600, 2)
            sla_target = t.get("sla_target_hours", 24)
            t["sla_breached"] = t["resolution_hours"] > sla_target
            _log_event(ticket_id, "resolved", actor, {"resolution_hours": t["resolution_hours"]})

        elif new_status == "in_progress" and not t.get("first_response_at"):
            t["first_response_at"] = now.isoformat()
            created = datetime.fromisoformat(t["created_at"])
            t["first_response_hours"] = round((now - created).total_seconds() / 3600, 2)
            _log_event(ticket_id, "first_response", actor)

        if "assigned_agent" in updates:
            _log_event(ticket_id, "assigned", actor, {"agent": updates["assigned_agent"]})

        if "priority" in updates:
            _log_event(ticket_id, "priority_changed", actor, {
                "from": t.get("priority"), "to": updates["priority"]
            })

        return t

    def escalate_ticket(self, ticket_id: str, tenant_id: str, reason: str = "") -> Optional[dict]:
        t = self.get_ticket(ticket_id, tenant_id)
        if not t:
            return None
        t["escalated"] = True
        t["escalation_count"] = t.get("escalation_count", 0) + 1
        t["status"] = "escalated"
        t["updated_at"] = datetime.utcnow().isoformat()
        # Re-route to senior agent
        if t["priority"] not in ("critical",):
            t["priority"] = "high"
        t["assigned_agent"] = "Frank Davis"  # senior agent
        _log_event(ticket_id, "escalated", "system", {"reason": reason})
        return t

    def add_comment(self, ticket_id: str, body: str, author: str,
                    is_internal: bool = False) -> dict:
        comment = {
            "id": len(_comments) + 1,
            "ticket_id": ticket_id,
            "author": author,
            "body": body,
            "is_internal": is_internal,
            "created_at": datetime.utcnow().isoformat(),
        }
        _comments.append(comment)
        # Set first response time if not set
        t = _tickets.get(ticket_id)
        if t and not t.get("first_response_at") and not is_internal:
            t["first_response_at"] = comment["created_at"]
            created = datetime.fromisoformat(t["created_at"])
            now = datetime.utcnow()
            t["first_response_hours"] = round((now - created).total_seconds() / 3600, 2)
        return comment

    def get_comments(self, ticket_id: str) -> List[dict]:
        return [c for c in _comments if c["ticket_id"] == ticket_id]

    def get_events(self, ticket_id: str) -> List[dict]:
        return [e for e in _events if e["ticket_id"] == ticket_id]

    def check_sla_breaches(self) -> List[str]:
        """Background task: check and mark SLA breaches."""
        now = datetime.utcnow()
        breached = []
        for tid, t in _tickets.items():
            if t["status"] in ("resolved", "closed"):
                continue
            deadline_str = t.get("sla_deadline")
            if deadline_str:
                deadline = datetime.fromisoformat(deadline_str)
                if now > deadline and not t.get("sla_breached"):
                    t["sla_breached"] = True
                    _log_event(tid, "sla_breached", "system")
                    breached.append(tid)
        return breached

    def get_analytics(self, tenant_id: str, days: int = 30) -> dict:
        """Compute real-time analytics for dashboard."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        tenant_tickets = [
            t for t in _tickets.values()
            if t["tenant_id"] == tenant_id
            and datetime.fromisoformat(t["created_at"]) >= cutoff
        ]

        if not tenant_tickets:
            return self._empty_analytics()

        total = len(tenant_tickets)
        resolved = [t for t in tenant_tickets if t["status"] in ("resolved", "closed")]
        open_t = [t for t in tenant_tickets if t["status"] == "open"]
        in_progress = [t for t in tenant_tickets if t["status"] == "in_progress"]
        escalated = [t for t in tenant_tickets if t.get("escalated")]
        sla_breached = [t for t in tenant_tickets if t.get("sla_breached")]

        res_hours = [t["resolution_hours"] for t in resolved if t.get("resolution_hours")]
        avg_res = round(sum(res_hours) / len(res_hours), 2) if res_hours else 0

        frt = [t.get("first_response_hours", 0) for t in tenant_tickets if t.get("first_response_hours")]
        avg_frt = round(sum(frt) / len(frt), 2) if frt else 0

        scores = [t["satisfaction_score"] for t in tenant_tickets if t.get("satisfaction_score")]
        avg_csat = round(sum(scores) / len(scores), 2) if scores else 0

        # Category distribution
        cat_dist = defaultdict(int)
        for t in tenant_tickets:
            cat_dist[t["category"]] += 1

        # Priority distribution
        pri_dist = defaultdict(int)
        for t in tenant_tickets:
            pri_dist[t["priority"]] += 1

        # Agent performance
        agent_perf = defaultdict(lambda: {"tickets": 0, "resolved": 0, "avg_hours": []})
        for t in tenant_tickets:
            agent = t.get("assigned_agent", "Unassigned")
            agent_perf[agent]["tickets"] += 1
            if t["status"] in ("resolved", "closed") and t.get("resolution_hours"):
                agent_perf[agent]["resolved"] += 1
                agent_perf[agent]["avg_hours"].append(t["resolution_hours"])

        agent_stats = []
        for agent, d in agent_perf.items():
            avg_h = round(sum(d["avg_hours"]) / len(d["avg_hours"]), 2) if d["avg_hours"] else 0
            agent_stats.append({
                "agent": agent,
                "total_tickets": d["tickets"],
                "resolved": d["resolved"],
                "resolution_rate": round(d["resolved"] / d["tickets"], 3) if d["tickets"] else 0,
                "avg_resolution_hours": avg_h,
            })

        # Daily trend (last 7 days)
        daily = defaultdict(int)
        for t in tenant_tickets:
            day = t["created_at"][:10]
            daily[day] += 1
        trend = sorted([{"date": k, "count": v} for k, v in daily.items()], key=lambda x: x["date"])

        # A/B test results
        ab_data = [r for r in _ab_results]
        rule_group = [r for r in ab_data if r.get("group") == "rule_based"]
        ml_group = [r for r in ab_data if r.get("group") == "ml_routing"]

        # Cost simulation ($15 per ticket fully resolved, $8 AI-assisted)
        cost_per_ticket = 8 if total > 0 else 0
        total_cost = total * cost_per_ticket

        return {
            "summary": {
                "total_tickets": total,
                "open": len(open_t),
                "in_progress": len(in_progress),
                "resolved": len(resolved),
                "escalated": len(escalated),
                "sla_breached": len(sla_breached),
                "sla_compliance_rate": round(1 - len(sla_breached) / total, 3) if total else 1.0,
            },
            "performance": {
                "avg_resolution_hours": avg_res,
                "avg_first_response_hours": avg_frt,
                "avg_csat_score": avg_csat,
                "resolution_rate": round(len(resolved) / total, 3) if total else 0,
            },
            "distributions": {
                "by_category": dict(cat_dist),
                "by_priority": dict(pri_dist),
            },
            "agent_performance": agent_stats,
            "trend": trend,
            "ab_test": {
                "rule_based_count": len(rule_group),
                "ml_routing_count": len(ml_group),
            },
            "cost_analysis": {
                "cost_per_ticket": cost_per_ticket,
                "total_cost_usd": total_cost,
                "period_days": days,
            },
        }

    def _empty_analytics(self) -> dict:
        return {
            "summary": {"total_tickets": 0, "open": 0, "in_progress": 0,
                        "resolved": 0, "escalated": 0, "sla_breached": 0,
                        "sla_compliance_rate": 1.0},
            "performance": {"avg_resolution_hours": 0, "avg_first_response_hours": 0,
                            "avg_csat_score": 0, "resolution_rate": 0},
            "distributions": {"by_category": {}, "by_priority": {}},
            "agent_performance": [],
            "trend": [],
            "ab_test": {"rule_based_count": 0, "ml_routing_count": 0},
            "cost_analysis": {"cost_per_ticket": 0, "total_cost_usd": 0, "period_days": 30},
        }

    def seed_demo_data(self, tenant_id: str, count: int = 50):
        """Seed demo tickets for UI testing."""
        import random
        from datetime import timedelta

        categories = ["Network", "Hardware", "Software", "Security", "Email", "VPN"]
        priorities = ["low", "medium", "high", "critical"]
        statuses = ["open", "in_progress", "resolved", "escalated"]
        agents = ["Alice Johnson", "Bob Martinez", "Carol White", "David Lee", "Frank Davis"]
        subjects = [
            "Cannot connect to VPN", "Laptop won't boot", "Email not syncing",
            "Slow internet on floor 3", "Password reset needed", "Software license expired",
            "Printer offline", "Database connection timeout", "Security alert triggered",
            "Access denied to shared drive",
        ]

        seeded = []
        for i in range(count):
            days_ago = random.randint(0, 30)
            created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            priority = random.choice(priorities)
            status = random.choice(statuses)
            sla_hours = SLA_HOURS.get(priority, 24)
            category = random.choice(categories)

            resolution_hours = None
            resolved_at = None
            if status in ("resolved",):
                resolution_hours = round(random.uniform(1, sla_hours * 1.5), 1)
                resolved_at = (created + timedelta(hours=resolution_hours)).isoformat()

            t = {
                "id": generate_ticket_id(),
                "tenant_id": tenant_id,
                "subject": random.choice(subjects),
                "description": "User reported this issue and needs urgent assistance.",
                "category": category,
                "priority": priority,
                "status": status,
                "requester_email": f"user{i}@company.com",
                "requester_name": f"User {i}",
                "department": random.choice(["IT", "HR", "Finance", "Sales"]),
                "assigned_agent": random.choice(agents),
                "language": "en",
                "source": random.choice(["web", "email", "api"]),
                "tags": [],
                "ai_category": category,
                "ai_category_confidence": round(random.uniform(0.7, 0.99), 3),
                "ai_classification_method": random.choice(["ml", "rule_based"]),
                "ai_predicted_resolution_hours": round(random.uniform(2, sla_hours), 1),
                "ai_sla_risk": round(random.uniform(0.1, 0.8), 3),
                "routing_method": random.choice(["ml", "rule_based"]),
                "routing_confidence": round(random.uniform(0.6, 0.95), 3),
                "sla_target_hours": sla_hours,
                "sla_deadline": (created + timedelta(hours=sla_hours)).isoformat(),
                "sla_breached": resolution_hours and resolution_hours > sla_hours,
                "escalated": random.random() < 0.1,
                "escalation_count": 0,
                "ab_test_group": random.choice(["rule_based", "ml_routing"]),
                "created_at": created.isoformat(),
                "updated_at": created.isoformat(),
                "first_response_at": (created + timedelta(hours=random.uniform(0.5, 4))).isoformat(),
                "first_response_hours": round(random.uniform(0.5, 4), 2),
                "resolved_at": resolved_at,
                "resolution_hours": resolution_hours,
                "satisfaction_score": random.choice([None, None, 3, 4, 4, 5]) if status == "resolved" else None,
                "resolution_notes": "Issue resolved successfully." if status == "resolved" else None,
                "explanation": None,
            }
            _tickets[t["id"]] = t
            seeded.append(t["id"])

        logger.info(f"Seeded {len(seeded)} demo tickets for tenant {tenant_id}")
        return seeded


ticket_service = TicketService()
