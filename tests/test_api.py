from fastapi.testclient import TestClient

from app.main import build_app


def client():
    return TestClient(build_app(":memory:"))


def test_dashboard_uses_synthetic_seed():
    with client() as test_client:
        payload = test_client.get("/api/dashboard").json()
        assert payload["total_orders"] == 6
        assert payload["revenue_cents"] > payload["gross_profit_cents"] > 0


def test_status_update_requires_operator_role():
    with client() as test_client:
        denied = test_client.patch("/api/orders/1/status", json={"status": "Ready"})
        assert denied.status_code == 403
        allowed = test_client.patch(
            "/api/orders/1/status",
            headers={"X-Demo-Role": "operator"},
            json={"status": "Ready"},
        )
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "Ready"


def test_audit_log_is_admin_only():
    with client() as test_client:
        assert test_client.get("/api/audit", headers={"X-Demo-Role": "operator"}).status_code == 403
        assert test_client.get("/api/audit", headers={"X-Demo-Role": "admin"}).status_code == 200
