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
        billing: WooBilling,
        shipping: WooShipping,
        student_id_type: str | None = None,
        student_id_number: str | None = None,
        student_academic_program: str | None = None,
    ) -> str:
        if product_id <= 0:
            raise WooUnexpectedError("product_id must be > 0")

        params: dict[str, str | int] = {
            "add-to-cart": product_id,
        }

        self._add_if_value(params, "student_first_name", billing.first_name)
        self._add_if_value(params, "student_last_name", billing.last_name)
        self._add_if_value(params, "student_id_type", student_id_type)
        self._add_if_value(params, "student_id_number", student_id_number)
        self._add_if_value(params, "student_country", billing.country)
        self._add_if_value(params, "student_state", billing.state)
        self._add_if_value(params, "student_address", billing.address_1)
        self._add_if_value(params, "student_postcode", billing.postcode)
        self._add_if_value(params, "student_phone", billing.phone)
        self._add_if_value(params, "student_email", billing.email)
        self._add_if_value(params, "student_academic_program", student_academic_program)

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
