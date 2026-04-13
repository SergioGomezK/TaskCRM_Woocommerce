from app.application.use_cases.generate_checkout_links_from_vtiger_leads import (
    GenerateCheckoutLinksFromVtigerLeadsUseCase,
)
from app.domain.entities import CRMLeadForSync


class FakeCRMClient:
    def __init__(self, leads: list[CRMLeadForSync]) -> None:
        self._leads = leads

    def list_leads_for_sync(
        self, *, limit: int, sync_status_value: str, request_id: str | None = None
    ) -> list[CRMLeadForSync]:
        return self._leads[:limit]


class FakeLinkIdentity:
    def create_link_id(self, lead_id: str) -> str:
        return f"{lead_id}.sig"

    def get_lead_id(self, link_id: str) -> str | None:
        raise NotImplementedError


def test_generate_checkout_links_batch_result_counts() -> None:
    crm_client = FakeCRMClient(
        [
            CRMLeadForSync(
                lead_id="11x1",
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
                phone="3001234567",
                address_1="Calle 1",
                city="Bogota",
                country=None,
                state=None,
                postcode=None,
                product_id=55,
                woo_order_id=None,
                sync_status="pending",
                student_id_type="dni",
                student_id_number="12345678X",
                student_academic_program="Máster en Inteligencia Artificial",
            ),
            CRMLeadForSync(
                lead_id="11x2",
                first_name="Luis",
                last_name="Diaz",
                email="luis@example.com",
                phone="3009876543",
                address_1="Calle 2",
                city="Bogota",
                country="CO",
                state=None,
                postcode=None,
                product_id=None,
                woo_order_id=None,
                sync_status="pending",
                student_id_type="dni",
                student_id_number="87654321X",
                student_academic_program="ia_generativa",
            ),
            CRMLeadForSync(
                lead_id="11x3",
                first_name="Marta",
                last_name="Rios",
                email="marta@example.com",
                phone="3001111111",
                address_1="Calle 3",
                city="Bogota",
                country="CO",
                state=None,
                postcode=None,
                product_id=88,
                woo_order_id="501",
                sync_status="pending",
                student_id_type="dni",
                student_id_number="11111111X",
                student_academic_program="ia_generativa",
            ),
        ]
    )
    use_case = GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        link_identity=FakeLinkIdentity(),
        pending_status="pending",
        batch_limit_default=50,
    )

    result = use_case.execute(public_base_url="https://api.example.com")

    assert result.processed == 3
    assert result.generated == 1
    assert result.failed == 1
    assert result.skipped == 1
    assert result.items[0].status == "generated"
    assert result.items[0].link_id == "11x1.sig"
    assert (
        result.items[0].static_link
        == "https://api.example.com/checkout-links/11x1.sig"
    )


def test_generate_checkout_links_fails_with_unknown_program() -> None:
    crm_client = FakeCRMClient(
        [
            CRMLeadForSync(
                lead_id="11x9",
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
                student_id_type="dni",
                student_id_number="12345678X",
                student_academic_program="Programa inventado",
            )
        ]
    )
    use_case = GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        link_identity=FakeLinkIdentity(),
        pending_status="pending",
        batch_limit_default=50,
    )

    result = use_case.execute(public_base_url="https://api.example.com")

    assert result.processed == 1
    assert result.generated == 0
    assert result.failed == 1
    assert result.items[0].status == "failed"
    assert "Invalid student_academic_program" in (result.items[0].error or "")
