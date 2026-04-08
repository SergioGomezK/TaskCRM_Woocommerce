from fastapi.testclient import TestClient

from app.domain.entities import WooOrderResult
from app.domain.errors import WooValidationError
from app.main import create_app
from app.presentation.dependencies import get_create_woo_order_use_case


class SuccessfulWooUseCase:
    def execute(self, order, request_id=None) -> WooOrderResult:  # noqa: ANN001
        return WooOrderResult(
            order_id=501,
            status="processing",
            total="99.90",
            currency="USD",
        )


class ValidationErrorWooUseCase:
    def execute(self, order, request_id=None):  # noqa: ANN001
        raise WooValidationError("Product is required.")


def _payload() -> dict[str, object]:
    return {
        "payment_method": "bacs",
        "payment_method_title": "Transferencia",
        "set_paid": False,
        "billing": {
            "first_name": "Ana",
            "last_name": "Perez",
            "address_1": "Calle 1",
            "city": "Bogota",
            "country": "CO",
            "email": "ana@example.com",
            "phone": "3001234567",
        },
        "shipping": {
            "first_name": "Ana",
            "last_name": "Perez",
            "address_1": "Calle 1",
            "city": "Bogota",
            "country": "CO",
        },
        "line_items": [{"product_id": 55, "quantity": 1}],
    }


def test_create_woo_order_success() -> None:
    app = create_app()
    app.dependency_overrides[get_create_woo_order_use_case] = lambda: SuccessfulWooUseCase()
    with TestClient(app) as client:
        response = client.post("/woocommerce/orders", json=_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["order_id"] == 501
    assert payload["status"] == "processing"
    assert payload["currency"] == "USD"


def test_create_woo_order_validation_error() -> None:
    app = create_app()
    app.dependency_overrides[get_create_woo_order_use_case] = (
        lambda: ValidationErrorWooUseCase()
    )
    with TestClient(app) as client:
        response = client.post("/woocommerce/orders", json=_payload())

    assert response.status_code == 400
    assert "WooCommerce validation error" in response.json()["detail"]
