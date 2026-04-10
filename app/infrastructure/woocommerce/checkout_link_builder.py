from urllib.parse import urlencode

from app.domain.entities import WooBilling, WooShipping
from app.domain.errors import WooUnexpectedError
from app.domain.ports import CheckoutLinkPort
from app.infrastructure.config import Settings


class WooCheckoutLinkBuilder(CheckoutLinkPort):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.woo_base_url:
            raise WooUnexpectedError("Missing WOO_BASE_URL configuration.")

    def build_checkout_url(
        self,
        *,
        product_id: int,
        quantity: int,
        billing: WooBilling,
        shipping: WooShipping,
    ) -> str:
        if product_id <= 0:
            raise WooUnexpectedError("product_id must be > 0")
        if quantity <= 0:
            raise WooUnexpectedError("quantity must be > 0")

        params: dict[str, str | int] = {
            "add-to-cart": product_id,
            "quantity": quantity,
        }

        self._add_if_value(params, "student_first_name", billing.first_name)
        self._add_if_value(params, "student_last_name", billing.last_name)
        self._add_if_value(params, "billing_email", billing.email)
        self._add_if_value(params, "billing_phone", billing.phone)
        self._add_if_value(params, "billing_address_1", billing.address_1)
        self._add_if_value(params, "billing_city", billing.city)
        self._add_if_value(params, "billing_state", billing.state)
        self._add_if_value(params, "billing_postcode", billing.postcode)
        self._add_if_value(params, "billing_country", billing.country)

        self._add_if_value(params, "shipping_first_name", shipping.first_name)
        self._add_if_value(params, "shipping_last_name", shipping.last_name)
        self._add_if_value(params, "shipping_address_1", shipping.address_1)
        self._add_if_value(params, "shipping_city", shipping.city)
        self._add_if_value(params, "shipping_state", shipping.state)
        self._add_if_value(params, "shipping_postcode", shipping.postcode)
        self._add_if_value(params, "shipping_country", shipping.country)

        base_url = f"{self._settings.woo_base_url}{self._settings.woo_checkout_path}"
        return f"{base_url}?{urlencode(params)}"

    @staticmethod
    def _add_if_value(
        params: dict[str, str | int], key: str, value: str | None
    ) -> None:
        if value is None:
            return
        normalized = value.strip()
        if normalized:
            params[key] = normalized
