import logging

from app.domain.entities import WooOrderInput, WooOrderResult
from app.domain.ports import WooCommercePort


class CreateWooOrderUseCase:
    def __init__(
        self, woo_client: WooCommercePort, logger: logging.Logger | None = None
    ) -> None:
        self._woo_client = woo_client
        self._logger = logger or logging.getLogger(__name__)

    def execute(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        result = self._woo_client.create_order(order, request_id=request_id)
        self._logger.info(
            "woo_order_created request_id=%s order_id=%s status=%s",
            request_id,
            result.order_id,
            result.status,
        )
        return result
