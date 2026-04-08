import logging
from typing import Any

import requests

from app.domain.entities import WooOrderInput, WooOrderResult
from app.domain.errors import (
    WooAuthenticationError,
    WooNetworkError,
    WooUnexpectedError,
    WooValidationError,
)
from app.domain.ports import WooCommercePort
from app.infrastructure.config import Settings
from app.infrastructure.woocommerce.mappers import map_order_input_to_woo_payload


class WooCommerceClient(WooCommercePort):
    def __init__(
        self,
        settings: Settings,
        session: requests.Session | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._session = session or requests.Session()
        self._logger = logger or logging.getLogger(__name__)

        if not settings.woo_base_url:
            raise WooUnexpectedError("Missing WOO_BASE_URL configuration.")
        if settings.woo_consumer_key is None:
            raise WooUnexpectedError("Missing WOO_CONSUMER_KEY configuration.")
        if settings.woo_consumer_secret is None:
            raise WooUnexpectedError("Missing WOO_CONSUMER_SECRET configuration.")

        self._consumer_key = settings.woo_consumer_key.get_secret_value()
        self._consumer_secret = settings.woo_consumer_secret.get_secret_value()
        self._endpoint = (
            f"{settings.woo_base_url}/wp-json/{settings.woo_api_version}/orders"
        )

    def create_order(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        payload = map_order_input_to_woo_payload(order)

        auth: tuple[str, str] | None = None
        params: dict[str, str] | None = None
        if self._settings.woo_query_string_auth:
            params = {
                "consumer_key": self._consumer_key,
                "consumer_secret": self._consumer_secret,
            }
        else:
            auth = (self._consumer_key, self._consumer_secret)

        try:
            response = self._session.post(
                self._endpoint,
                json=payload,
                params=params,
                auth=auth,
                timeout=self._settings.woo_timeout_seconds,
            )
        except requests.Timeout as exc:
            raise WooNetworkError("Timeout while connecting to WooCommerce.") from exc
        except requests.RequestException as exc:
            raise WooNetworkError("Network error while connecting to WooCommerce.") from exc

        body: Any = None
        if response.content:
            try:
                body = response.json()
            except ValueError:
                body = None

        if response.status_code in (401, 403):
            raise WooAuthenticationError(_error_message(body, "Authentication failed."))
        if response.status_code >= 500:
            raise WooNetworkError("WooCommerce service unavailable.")
        if response.status_code >= 400:
            raise WooValidationError(_error_message(body, "WooCommerce rejected request data."))

        if not isinstance(body, dict):
            raise WooUnexpectedError("WooCommerce response is not valid JSON.")

        order_id = body.get("id")
        if not isinstance(order_id, int):
            raise WooUnexpectedError("WooCommerce response missing order id.")

        status = str(body.get("status", ""))
        total = str(body.get("total", ""))
        currency = str(body.get("currency", ""))

        self._logger.info(
            "woo_order_created request_id=%s order_id=%s",
            request_id,
            order_id,
        )
        return WooOrderResult(
            order_id=order_id,
            status=status,
            total=total,
            currency=currency,
        )


def _error_message(payload: Any, default: str) -> str:
    if not isinstance(payload, dict):
        return default
    message = payload.get("message")
    if not message:
        return default
    return str(message)
