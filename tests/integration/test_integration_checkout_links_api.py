from fastapi.testclient import TestClient

from app.domain.entities import LeadCheckoutLinkBatchResult, LeadCheckoutLinkItemResult
from app.infrastructure.config import Settings, get_settings
from app.main import create_app
from app.presentation.dependencies import (
    get_generate_checkout_links_from_vtiger_leads_use_case,
)


class SuccessfulCheckoutLinksUseCase:
    def execute(self, limit=None, request_id=None) -> LeadCheckoutLinkBatchResult:  # noqa: ANN001
        return LeadCheckoutLinkBatchResult(
            processed=2,
            generated=1,
            failed=1,
            skipped=0,
            items=[
                LeadCheckoutLinkItemResult(
                    lead_id="11x1",
                    status="generated",
                    checkout_url="https://shop.example.com/checkout/?add-to-cart=55&quantity=1",
                ),
                LeadCheckoutLinkItemResult(
                    lead_id="11x2",
                    status="failed",
                    error="Missing required lead fields: email",
                ),
            ],
        )


def _settings_with_key() -> Settings:
    return Settings(
        vtiger_base_url="https://example-vtiger.com",
        vtiger_username="api_user",
        vtiger_access_key="access-key",
        integration_api_key="test-key",
    )


def test_checkout_links_endpoint_requires_integration_key() -> None:
    app = create_app()
    app.dependency_overrides[get_generate_checkout_links_from_vtiger_leads_use_case] = (
        lambda: SuccessfulCheckoutLinksUseCase()
    )
    app.dependency_overrides[get_settings] = _settings_with_key

    with TestClient(app) as client:
        response = client.post("/integrations/vtiger/leads-to-checkout-links/sync")

    assert response.status_code == 401


def test_checkout_links_endpoint_returns_batch_json() -> None:
    app = create_app()
    app.dependency_overrides[get_generate_checkout_links_from_vtiger_leads_use_case] = (
        lambda: SuccessfulCheckoutLinksUseCase()
    )
    app.dependency_overrides[get_settings] = _settings_with_key

    with TestClient(app) as client:
        response = client.post(
            "/integrations/vtiger/leads-to-checkout-links/sync?limit=20",
            headers={"X-Integration-Key": "test-key"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["processed"] == 2
    assert payload["generated"] == 1
    assert payload["failed"] == 1
    assert payload["items"][0]["status"] == "generated"
    assert "add-to-cart=55" in payload["items"][0]["checkout_url"]
