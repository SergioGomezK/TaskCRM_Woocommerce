from app.application.use_cases.create_woo_order import CreateWooOrderUseCase
from app.domain.entities import (
    WooBilling,
    WooOrderInput,
    WooOrderLineItem,
    WooOrderResult,
    WooShipping,
)


class FakeWooClient:
    def create_order(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        return WooOrderResult(order_id=101, status="processing", total="25.00", currency="USD")


def test_create_woo_order_use_case_returns_result() -> None:
    use_case = CreateWooOrderUseCase(woo_client=FakeWooClient())

    result = use_case.execute(
        WooOrderInput(
            payment_method="bacs",
            payment_method_title="Transferencia",
            set_paid=False,
            billing=WooBilling(
                first_name="Ana",
                last_name="Perez",
                address_1="Calle 1",
                city="Bogota",
                country="CO",
                email="ana@example.com",
                phone="3001234567",
            ),
            shipping=WooShipping(
                first_name="Ana",
                last_name="Perez",
                address_1="Calle 1",
                city="Bogota",
                country="CO",
            ),
            line_items=[WooOrderLineItem(product_id=55, quantity=1)],
        )
    )

    assert result.order_id == 101
    assert result.status == "processing"
