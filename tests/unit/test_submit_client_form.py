import pytest

from app.application.use_cases.submit_client_form import SubmitClientFormUseCase
from app.domain.entities import CRMCreateResult, ClientLead
from app.domain.errors import CRMAuthenticationError


class FakeCRMClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.received_contact: ClientLead | None = None

    def create_contact(
        self, contact: ClientLead, request_id: str | None = None
    ) -> CRMCreateResult:
        self.received_contact = contact
        if self.should_fail:
            raise CRMAuthenticationError("Auth failed")
        return CRMCreateResult(crm_record_id="19x42")


def test_submit_client_form_returns_crm_id() -> None:
    crm_client = FakeCRMClient()
    use_case = SubmitClientFormUseCase(crm_client=crm_client)

    result = use_case.execute(
        ClientLead(
            first_name="Ana",
            last_name="Perez",
            email="ana@example.com",
        )
    )

    assert result.crm_record_id == "19x42"
    assert crm_client.received_contact is not None
    assert crm_client.received_contact.last_name == "Perez"


def test_submit_client_form_propagates_crm_error() -> None:
    crm_client = FakeCRMClient(should_fail=True)
    use_case = SubmitClientFormUseCase(crm_client=crm_client)

    with pytest.raises(CRMAuthenticationError):
        use_case.execute(
            ClientLead(
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
            )
        )
