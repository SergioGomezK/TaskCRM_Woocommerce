from fastapi.testclient import TestClient

from app.domain.errors import CRMNetworkError
from app.domain.entities import CRMLeadSummary
from app.main import create_app
from app.presentation.dependencies import get_list_leads_use_case


class SuccessfulLeadsUseCase:
    def execute(self, limit: int = 20, request_id: str | None = None) -> list[CRMLeadSummary]:
        return [
            CRMLeadSummary(
                crm_record_id="11x10",
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
                lead_source="Web",
            ),
            CRMLeadSummary(
                crm_record_id="11x11",
                first_name="Luis",
                last_name="Diaz",
                email="luis@example.com",
                lead_source="Referral",
            ),
        ][:limit]


class FailingLeadsUseCase:
    def execute(self, limit: int = 20, request_id: str | None = None):  # noqa: ANN001
        raise CRMNetworkError("No fue posible conectar con Vtiger.")


def _build_client(overridden_use_case) -> TestClient:  # noqa: ANN001
    app = create_app()
    app.dependency_overrides[get_list_leads_use_case] = lambda: overridden_use_case
    return TestClient(app)


def test_get_leads_returns_json() -> None:
    with _build_client(SuccessfulLeadsUseCase()) as client:
        response = client.get("/leads?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert payload["limit"] == 2
    assert payload["data"][0]["crm_record_id"] == "11x10"
    assert payload["data"][0]["lead_source"] == "Web"


def test_get_leads_network_error() -> None:
    with _build_client(FailingLeadsUseCase()) as client:
        response = client.get("/leads")

    assert response.status_code == 504
    payload = response.json()
    assert "Network error with Vtiger" in payload["detail"]
