from app.application.use_cases.sync_vtiger_leads_to_woo_orders import (
    SyncVtigerLeadsToWooOrdersUseCase,
)
from app.domain.entities import CRMLeadForSync, WooOrderInput, WooOrderResult


class FakeCRMClient:
    def __init__(self, leads: list[CRMLeadForSync]) -> None:
        self._leads = leads
        self.updated: list[dict[str, str | None]] = []

    def list_leads_for_sync(
        self, *, limit: int, sync_status_value: str, request_id: str | None = None
    ) -> list[CRMLeadForSync]:
        return self._leads[:limit]

    def update_lead_sync_result(
        self,
        *,
        lead_id: str,
        sync_status: str,
        woo_order_id: str | None = None,
        sync_error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.updated.append(
            {
                "lead_id": lead_id,
                "sync_status": sync_status,
                "woo_order_id": woo_order_id,
                "sync_error": sync_error,
            }
        )


class FakeWooClient:
    def create_order(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        return WooOrderResult(order_id=999, status="processing", total="10.00", currency="USD")


def _use_case(crm_client: FakeCRMClient) -> SyncVtigerLeadsToWooOrdersUseCase:
    return SyncVtigerLeadsToWooOrdersUseCase(
        crm_client=crm_client,
        woo_client=FakeWooClient(),
        pending_status="pending",
        processed_status="processed",
        failed_status="failed",
        default_country="CO",
        default_payment_method="bacs",
        default_payment_method_title="Transferencia bancaria",
        default_set_paid=False,
        batch_limit_default=50,
    )


def test_sync_creates_order_and_marks_processed() -> None:
    crm_client = FakeCRMClient(
        leads=[
            CRMLeadForSync(
                lead_id="11x1",
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
                phone="3001234567",
                address_1="Calle 1",
                city="Bogota",
                country="CO",
                state=None,
                postcode=None,
                product_id=55,
                woo_order_id=None,
                sync_status="pending",
            )
        ]
    )
    use_case = _use_case(crm_client)

    result = use_case.execute()

    assert result.processed == 1
    assert result.created == 1
    assert result.failed == 0
    assert result.skipped == 0
    assert crm_client.updated[0]["sync_status"] == "processed"
    assert crm_client.updated[0]["woo_order_id"] == "999"


def test_sync_fails_when_product_id_is_missing() -> None:
    crm_client = FakeCRMClient(
        leads=[
            CRMLeadForSync(
                lead_id="11x2",
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
                phone="3001234567",
                address_1="Calle 1",
                city="Bogota",
                country="CO",
                state=None,
                postcode=None,
                product_id=None,
                woo_order_id=None,
                sync_status="pending",
            )
        ]
    )
    use_case = _use_case(crm_client)

    result = use_case.execute()

    assert result.processed == 1
    assert result.created == 0
    assert result.failed == 1
    assert crm_client.updated[0]["sync_status"] == "failed"
