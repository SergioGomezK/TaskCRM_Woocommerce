from app.application.use_cases.list_leads import ListLeadsUseCase
from app.domain.entities import CRMLeadSummary


class FakeCRMClient:
    def list_leads(self, limit: int = 20, request_id: str | None = None) -> list[CRMLeadSummary]:
        return [
            CRMLeadSummary(
                crm_record_id="11x1",
                first_name="Ana",
                last_name="Perez",
                email="ana@example.com",
            ),
            CRMLeadSummary(
                crm_record_id="11x2",
                first_name="Luis",
                last_name="Diaz",
                email="luis@example.com",
            ),
        ][:limit]


def test_list_leads_use_case_returns_data() -> None:
    use_case = ListLeadsUseCase(crm_client=FakeCRMClient())

    result = use_case.execute(limit=1)

    assert len(result) == 1
    assert result[0].crm_record_id == "11x1"
