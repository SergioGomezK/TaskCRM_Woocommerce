from app.application.use_cases.generate_checkout_links_from_vtiger_leads import (
    GenerateCheckoutLinksFromVtigerLeadsUseCase,
)
from app.domain.entities import CRMLeadForSync, WooBilling, WooShipping


class FakeCRMClient:
    def __init__(self, leads: list[CRMLeadForSync]) -> None:
        self._leads = leads

    def list_leads_for_sync(
        self, *, limit: int, sync_status_value: str, request_id: str | None = None
    ) -> list[CRMLeadForSync]:
        return self._leads[:limit]


class FakeCheckoutBuilder:
    def __init__(self) -> None:
        self.last_country: str | None = None
        self.last_program: str | None = None

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
        self.last_country = billing.country
        self.last_program = student_academic_program
        return (
            "https://shop.example.com/checkout/?"
            f"add-to-cart={product_id}&student_id_type={student_id_type}"
            f"&student_academic_program={student_academic_program}"
        )


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
    link_builder = FakeCheckoutBuilder()
    use_case = GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        checkout_link_builder=link_builder,
        pending_status="pending",
        default_country="CO",
        batch_limit_default=50,
    )

    result = use_case.execute()

    assert result.processed == 3
    assert result.generated == 1
    assert result.failed == 1
    assert result.skipped == 1
    assert result.items[0].status == "generated"
    assert result.items[0].checkout_url is not None
    assert "student_academic_program=ia_generativa" in result.items[0].checkout_url
    assert link_builder.last_country == "CO"
    assert link_builder.last_program == "ia_generativa"


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
    link_builder = FakeCheckoutBuilder()
    use_case = GenerateCheckoutLinksFromVtigerLeadsUseCase(
        crm_client=crm_client,
        checkout_link_builder=link_builder,
        pending_status="pending",
        default_country="CO",
        batch_limit_default=50,
    )

    result = use_case.execute()

    assert result.processed == 1
    assert result.generated == 0
    assert result.failed == 1
    assert result.items[0].status == "failed"
    assert "Invalid student_academic_program" in (result.items[0].error or "")
