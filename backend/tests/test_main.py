"""
OpsDesk AI — Backend Tests
Run with: pytest backend/tests/ -v
"""
import sys
import os
import types

# ── Bootstrap stubs for web-framework deps (allows testing ML logic in isolation) ──

def _stub_web_deps():
    for mod_name in [
        'fastapi', 'fastapi.middleware.cors', 'fastapi.middleware.gzip',
        'fastapi.responses', 'pydantic_settings',
    ]:
        if mod_name not in sys.modules:
            m = types.ModuleType(mod_name)
            sys.modules[mod_name] = m

    import types as _t
    fa = sys.modules['fastapi']
    fa.APIRouter = lambda: _t.SimpleNamespace(
        get=lambda *a, **k: lambda f: f,
        post=lambda *a, **k: lambda f: f,
        patch=lambda *a, **k: lambda f: f,
        delete=lambda *a, **k: lambda f: f,
    )
    fa.Query = lambda *a, **k: None
    fa.Header = lambda *a, **k: None
    fa.HTTPException = Exception

    ps = sys.modules['pydantic_settings']
    class _BS:
        SLA_CRITICAL_HOURS = 2; SLA_HIGH_HOURS = 8
        SLA_MEDIUM_HOURS = 24; SLA_LOW_HOURS = 72
        OPENAI_API_KEY = ''; OPENAI_MODEL = 'gpt-4o-mini'
        MODELS_DIR = 'ml/models'; DATA_DIR = 'data/processed'
    ps.BaseSettings = _BS

    try:
        import pydantic
    except ImportError:
        pd = types.ModuleType('pydantic')
        class _BM:
            def __init__(self, **kw):
                for k, v in kw.items(): setattr(self, k, v)
        pd.BaseModel = _BM
        pd.Field = lambda *a, **k: None
        sys.modules['pydantic'] = pd


_stub_web_deps()

# Now we can safely import project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestMLService:
    """Unit tests for the ML inference layer."""

    @classmethod
    def setup_class(cls):
        from app.services.ml_service import ml_service
        ml_service.load_models()
        cls.svc = ml_service

    def test_classify_returns_valid_category(self):
        result = self.svc.classify_ticket(
            "Cannot connect to VPN", "Timeout after authentication"
        )
        assert "category" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["method"] in ("ml", "rule_based")
        assert len(result["top_predictions"]) >= 1

    def test_classify_email_category(self):
        result = self.svc.classify_ticket("Outlook not syncing emails", "No new emails showing")
        assert result["category"] in (
            "Email", "Software", "Network", "Access Management",
            "Hardware", "Security", "Database", "Cloud", "VPN", "Printing"
        )

    def test_classify_printing_category(self):
        result = self.svc.classify_ticket("Printer offline on floor 3", "Cannot find printer")
        assert "category" in result
        assert result["confidence"] > 0

    def test_classify_rule_based_fallback(self):
        """Empty model — should always fall back gracefully."""
        result = self.svc._classify_rule_based("network internet wifi slow")
        assert result["category"] == "Network"
        assert result["method"] == "rule_based"

    def test_route_returns_agent(self):
        result = self.svc.route_ticket("Network", "high")
        assert "assigned_agent" in result
        assert isinstance(result["assigned_agent"], str)
        assert len(result["assigned_agent"]) > 0
        assert "routing_method" in result

    def test_route_critical_escalates(self):
        result = self.svc.route_ticket("Software", "critical", use_ml=False)
        assert result["escalate"] is True

    def test_resolution_predictor(self):
        result = self.svc.predict_resolution_time("Software", "high", "application crash error")
        assert "predicted_hours" in result
        assert result["predicted_hours"] > 0
        assert "sla_target_hours" in result
        assert "sla_at_risk" in result
        assert isinstance(result["sla_at_risk"], bool)

    def test_sla_risk_critical_is_high(self):
        score = self.svc.score_sla_risk("Security", "critical", 500)
        assert 0.0 <= score <= 1.0
        # Critical should have higher risk than low
        low_score = self.svc.score_sla_risk("Printing", "low", 50)
        assert score >= low_score

    def test_kb_search_returns_results(self):
        results = self.svc.search_knowledge_base("password reset login", top_k=3)
        assert isinstance(results, list)
        # Each result has similarity score
        for r in results:
            assert "similarity" in r
            assert 0.0 <= r["similarity"] <= 1.0

    def test_explain_routing_has_factors(self):
        result = self.svc.explain_routing("Network", "high")
        assert "assigned_to" in result
        assert "explanation_factors" in result
        assert len(result["explanation_factors"]) >= 1
        factor = result["explanation_factors"][0]
        assert "feature" in factor
        assert "contribution" in factor
        assert "explanation" in factor

    def test_model_versions_dict(self):
        versions = self.svc.get_model_versions()
        assert isinstance(versions, dict)
        assert "classifier" in versions


class TestTicketService:
    """Unit tests for ticket business logic."""

    @classmethod
    def setup_class(cls):
        from app.services.ml_service import ml_service
        ml_service.load_models()
        from app.services.ticket_service import ticket_service
        cls.svc = ticket_service
        cls.tenant = "test_tenant"

    def test_create_ticket_minimal(self):
        t = self.svc.create_ticket(
            {"subject": "Test ticket", "priority": "medium"},
            self.tenant
        )
        assert t["id"].startswith("TKT-")
        assert t["tenant_id"] == self.tenant
        assert t["status"] == "open"
        assert t["ai_category"] is not None
        assert t["assigned_agent"] is not None
        assert t["ab_test_group"] in ("rule_based", "ml_routing")
        assert t["sla_target_hours"] == 24  # medium

    def test_create_ticket_critical_sla(self):
        t = self.svc.create_ticket(
            {"subject": "Critical outage", "priority": "critical"},
            self.tenant
        )
        assert t["sla_target_hours"] == 2

    def test_create_ticket_has_ai_fields(self):
        t = self.svc.create_ticket(
            {"subject": "VPN not working", "description": "Timeout", "priority": "high"},
            self.tenant
        )
        assert "ai_category" in t
        assert "ai_category_confidence" in t
        assert 0.0 <= t["ai_category_confidence"] <= 1.0
        assert "ai_predicted_resolution_hours" in t
        assert t["ai_predicted_resolution_hours"] > 0
        assert "ai_sla_risk" in t
        assert 0.0 <= t["ai_sla_risk"] <= 1.0

    def test_get_ticket_found(self):
        t = self.svc.create_ticket({"subject": "Get test"}, self.tenant)
        found = self.svc.get_ticket(t["id"], self.tenant)
        assert found is not None
        assert found["id"] == t["id"]

    def test_get_ticket_wrong_tenant(self):
        t = self.svc.create_ticket({"subject": "Tenant isolation test"}, self.tenant)
        not_found = self.svc.get_ticket(t["id"], "other_tenant")
        assert not_found is None

    def test_update_ticket_status(self):
        t = self.svc.create_ticket({"subject": "Update test"}, self.tenant)
        updated = self.svc.update_ticket(t["id"], {"status": "in_progress"}, self.tenant)
        assert updated["status"] == "in_progress"
        assert updated.get("first_response_at") is not None

    def test_resolve_ticket_sets_resolution_time(self):
        t = self.svc.create_ticket({"subject": "Resolve test"}, self.tenant)
        resolved = self.svc.update_ticket(t["id"], {"status": "resolved"}, self.tenant)
        assert resolved["resolved_at"] is not None
        assert resolved["resolution_hours"] is not None
        assert resolved["resolution_hours"] >= 0

    def test_escalate_ticket(self):
        t = self.svc.create_ticket({"subject": "Escalate test", "priority": "medium"}, self.tenant)
        escalated = self.svc.escalate_ticket(t["id"], self.tenant, "User reported P1 impact")
        assert escalated["escalated"] is True
        assert escalated["status"] == "escalated"
        assert escalated["escalation_count"] >= 1

    def test_add_and_get_comments(self):
        t = self.svc.create_ticket({"subject": "Comment test"}, self.tenant)
        comment = self.svc.add_comment(t["id"], "Test comment body", "Agent Bob")
        assert comment["body"] == "Test comment body"
        comments = self.svc.get_comments(t["id"])
        assert len(comments) >= 1
        assert any(c["body"] == "Test comment body" for c in comments)

    def test_list_tickets_pagination(self):
        # Seed some tickets
        for i in range(5):
            self.svc.create_ticket({"subject": f"List test {i}"}, self.tenant)
        result = self.svc.list_tickets(self.tenant, page=1, page_size=3)
        assert "tickets" in result
        assert "total" in result
        assert len(result["tickets"]) <= 3

    def test_analytics_structure(self):
        self.svc.seed_demo_data(self.tenant, 10)
        analytics = self.svc.get_analytics(self.tenant, days=30)
        assert "summary" in analytics
        assert "performance" in analytics
        assert "distributions" in analytics
        assert "agent_performance" in analytics
        assert "trend" in analytics
        assert "ab_test" in analytics
        assert "cost_analysis" in analytics
        assert analytics["summary"]["total_tickets"] > 0

    def test_seed_demo_data(self):
        ids = self.svc.seed_demo_data("seed_test_tenant", 15)
        assert len(ids) == 15


class TestForecasting:
    """Unit tests for time-series forecasting."""

    def test_forecast_returns_structure(self):
        from ml.forecasting import forecast_ticket_volume
        result = forecast_ticket_volume(periods_days=7)
        assert "historical" in result
        assert "forecast" in result
        assert "recommendation" in result
        assert "method" in result
        assert len(result["forecast"]) == 7

    def test_forecast_records_have_required_fields(self):
        from ml.forecasting import forecast_ticket_volume
        result = forecast_ticket_volume(periods_days=5)
        for rec in result["forecast"]:
            assert "ds" in rec
            assert "predicted" in rec
            assert "lower" in rec
            assert "upper" in rec
            assert rec["predicted"] >= 0
            assert rec["lower"] <= rec["predicted"] <= rec["upper"]

    def test_anomaly_detection(self):
        from ml.forecasting import detect_anomalies
        # Inject obvious spike
        series = [10.0] * 14 + [100.0] + [10.0] * 5
        flags = detect_anomalies(series, window=7)
        assert any(flags), "Should detect the spike as anomaly"

    def test_exponential_smoothing(self):
        from ml.forecasting import exponential_smoothing
        series = [1.0, 3.0, 5.0, 7.0, 9.0]
        smoothed = exponential_smoothing(series, alpha=0.5)
        assert len(smoothed) == len(series)
        assert smoothed[0] == 1.0
        # Should be between extremes
        assert 1.0 <= smoothed[-1] <= 9.0

    def test_predict_incidents(self):
        from ml.forecasting import predict_incidents
        incidents = predict_incidents(lookback_days=7)
        assert isinstance(incidents, list)
        for inc in incidents:
            assert "timestamp" in inc
            assert "severity" in inc
            assert inc["severity"] in ("low", "medium", "high")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
