"""
SQLAlchemy ORM models for OpsDesk AI.
Multi-tenant, production-grade schema.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, JSON, Enum as SAEnum, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, enum.Enum):
    NETWORK = "Network"
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    SECURITY = "Security"
    DATABASE = "Database"
    CLOUD = "Cloud"
    EMAIL = "Email"
    VPN = "VPN"
    PRINTING = "Printing"
    ACCESS_MANAGEMENT = "Access Management"
    OTHER = "Other"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    USER = "user"
    VIEWER = "viewer"


# ── Tables ─────────────────────────────────────────────────────────────────────

class Tenant(Base):
    """Multi-tenant organization record."""
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    plan = Column(String(32), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    tickets = relationship("Ticket", back_populates="tenant")
    users = relationship("User", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.USER)
    department = Column(String(128))
    hashed_password = Column(String(512))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    preferences = Column(JSON, default=dict)

    tenant = relationship("Tenant", back_populates="users")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent",
                                    foreign_keys="Ticket.assigned_agent_id")

    __table_args__ = (Index("ix_users_tenant_email", "tenant_id", "email"),)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(32), primary_key=True)  # TKT-XXXXX
    tenant_id = Column(String(64), ForeignKey("tenants.id"), nullable=False)

    # Core fields
    subject = Column(String(512), nullable=False)
    description = Column(Text)
    category = Column(SAEnum(TicketCategory), default=TicketCategory.OTHER)
    priority = Column(SAEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.OPEN)

    # People
    requester_id = Column(String(64), ForeignKey("users.id"))
    requester_email = Column(String(256))
    requester_name = Column(String(256))
    assigned_agent_id = Column(String(64), ForeignKey("users.id"))
    department = Column(String(128))

    # ML predictions
    ai_category = Column(String(64))
    ai_category_confidence = Column(Float)
    ai_predicted_resolution_hours = Column(Float)
    ai_sla_risk = Column(Float)  # 0–1 probability
    routing_method = Column(String(32))  # "ml" | "rule" | "manual"

    # Lifecycle timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Computed fields
    resolution_hours = Column(Float)
    first_response_hours = Column(Float)
    sla_target_hours = Column(Float)
    sla_breached = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    escalation_count = Column(Integer, default=0)

    # Quality
    satisfaction_score = Column(Integer)  # 1–5
    resolution_notes = Column(Text)
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)

    # Multi-language
    language = Column(String(8), default="en")

    # Source tracking
    source = Column(String(32), default="web")  # web, email, api, auto

    # A/B testing
    ab_test_group = Column(String(16))  # "rule_based" | "ml_routing"

    # Explainability
    shap_values = Column(JSON)

    tenant = relationship("Tenant", back_populates="tickets")
    assigned_agent = relationship("User", back_populates="assigned_tickets",
                                  foreign_keys=[assigned_agent_id])
    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")
    events = relationship("TicketEvent", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tickets_tenant_status", "tenant_id", "status"),
        Index("ix_tickets_tenant_created", "tenant_id", "created_at"),
        Index("ix_tickets_assigned", "assigned_agent_id", "status"),
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(32), ForeignKey("tickets.id"), nullable=False)
    author_id = Column(String(64), ForeignKey("users.id"))
    author_name = Column(String(256))
    body = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")


class TicketEvent(Base):
    """Immutable audit log for ticket lifecycle events."""
    __tablename__ = "ticket_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(32), ForeignKey("tickets.id"), nullable=False)
    event_type = Column(String(64), nullable=False)  # created, assigned, escalated, resolved
    actor_id = Column(String(64))
    actor_name = Column(String(256))
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="events")


class KBArticle(Base):
    """Knowledge base articles generated from resolved tickets."""
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), ForeignKey("tenants.id"))
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String(64))
    tags = Column(JSON, default=list)
    source_ticket_ids = Column(JSON, default=list)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ABTestResult(Base):
    """A/B test tracking for routing strategies."""
    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(32))
    group = Column(String(32))  # rule_based | ml_routing
    routing_time_ms = Column(Float)
    resolution_hours = Column(Float)
    sla_met = Column(Boolean)
    satisfaction_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
