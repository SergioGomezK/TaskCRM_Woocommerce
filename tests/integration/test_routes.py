from fastapi.testclient import TestClient

from app.application.use_cases.submit_client_form import SubmitClientFormResult
from app.domain.errors import CRMNetworkError
from app.main import create_app
from app.presentation.dependencies import get_submit_client_form_use_case


class SuccessfulUseCase:
    def execute(self, contact, request_id=None) -> SubmitClientFormResult:  # noqa: ANN001
        return SubmitClientFormResult(crm_record_id="19x100")


class NetworkFailingUseCase:
    def execute(self, contact, request_id=None):  # noqa: ANN001
        raise CRMNetworkError("No fue posible conectar con Vtiger.")


def _build_client(overridden_use_case) -> TestClient:  # noqa: ANN001
    app = create_app()
    app.dependency_overrides[get_submit_client_form_use_case] = lambda: overridden_use_case
    return TestClient(app)


def test_get_client_form_renders() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/clientes/form")

    assert response.status_code == 200
    assert "Formulario de Clientes" in response.text


def test_post_client_form_success() -> None:
    with _build_client(SuccessfulUseCase()) as client:
        response = client.post(
            "/clientes/form",
            data={
                "first_name": "Ana",
                "last_name": "Perez",
                "email": "ana@example.com",
                "phone": "3001234567",
                "company": "ACME",
                "lead_source": "Web",
                "comment": "Interes en demo",
            },
        )

    assert response.status_code == 200
    assert "Cliente enviado correctamente a Vtiger." in response.text
    assert "19x100" in response.text


def test_post_client_form_validation_error() -> None:
    with _build_client(SuccessfulUseCase()) as client:
        response = client.post(
            "/clientes/form",
            data={
                "first_name": "Ana",
                "last_name": "Perez",
                "email": "no-email",
            },
        )

    assert response.status_code == 422
    assert "Debe ser un correo electronico valido." in response.text


def test_post_client_form_crm_network_error() -> None:
    with _build_client(NetworkFailingUseCase()) as client:
        response = client.post(
            "/clientes/form",
            data={
                "first_name": "Ana",
                "last_name": "Perez",
                "email": "ana@example.com",
            },
        )

    assert response.status_code == 504
    assert "No fue posible conectar con Vtiger." in response.text
