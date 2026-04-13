from fastapi.testclient import TestClient

from app.domain.errors import InvalidCheckoutLinkError
from app.main import create_app
from app.presentation.dependencies import get_resolve_checkout_link_use_case


class SuccessfulResolveUseCase:
    def execute(self, *, link_id: str, request_id: str | None = None) -> str:
        return "https://pagoseguro.laruniversity.com/finalizar-compra/?add-to-cart=79"


class FailingResolveUseCase:
    def execute(self, *, link_id: str, request_id: str | None = None) -> str:
        raise InvalidCheckoutLinkError("Invalid checkout link.")


def test_resolve_checkout_link_redirects() -> None:
    app = create_app()
    app.dependency_overrides[get_resolve_checkout_link_use_case] = (
        lambda: SuccessfulResolveUseCase()
    )

    with TestClient(app) as client:
        response = client.get("/checkout-links/11x1.sig", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith(
        "https://pagoseguro.laruniversity.com/finalizar-compra/"
    )


def test_resolve_checkout_link_not_found() -> None:
    app = create_app()
    app.dependency_overrides[get_resolve_checkout_link_use_case] = (
        lambda: FailingResolveUseCase()
    )

    with TestClient(app) as client:
        response = client.get("/checkout-links/bad-token", follow_redirects=False)

    assert response.status_code == 404
