from fastapi.testclient import TestClient

from app.domain.entities import LeadSyncBatchResult, LeadSyncItemResult
from app.infrastructure.config import Settings, get_settings
from app.main import create_app
from app.presentation.dependencies import get_sync_vtiger_leads_to_woo_orders_use_case


class SuccessfulSyncUseCase:
    def execute(self, limit=None, request_id=None) -> LeadSyncBatchResult:  # noqa: ANN001
        return LeadSyncBatchResult(
            processed=2,
            created=1,
            failed=1,
            skipped=0,
            items=[
                LeadSyncItemResult(lead_id="11x1", status="created", woo_order_id="501"),
                LeadSyncItemResult(lead_id="11x2", status="failed", error="Missing product"),
            ],
        )


def _settings_with_key() -> Settings:
    return Settings(
        vtiger_base_url="https://example-vtiger.com",
        vtiger_username="api_user",
        vtiger_access_key="access-key",
        integration_api_key="test-key",
    )


def test_sync_endpoint_requires_integration_key() -> None:
    app = create_app()
    app.dependency_overrides[get_sync_vtiger_leads_to_woo_orders_use_case] = (
        lambda: SuccessfulSyncUseCase()
    )
    app.dependency_overrides[get_settings] = _settings_with_key

    with TestClient(app) as client:
        response = client.post("/integrations/vtiger/leads-to-orders/sync")

    assert response.status_code == 401


def test_sync_endpoint_returns_batch_json() -> None:
    app = create_app()
    app.dependency_overrides[get_sync_vtiger_leads_to_woo_orders_use_case] = (
        lambda: SuccessfulSyncUseCase()
    )
    app.dependency_overrides[get_settings] = _settings_with_key

    with TestClient(app) as client:
        response = client.post(
            "/integrations/vtiger/leads-to-orders/sync?limit=20",
            headers={"X-Integration-Key": "test-key"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["processed"] == 2
    assert payload["created"] == 1
    assert payload["failed"] == 1
    assert payload["items"][0]["woo_order_id"] == "501"
