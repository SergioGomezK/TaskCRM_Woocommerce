import logging

from app.domain.entities import CRMLeadSummary
from app.domain.ports import CRMClientPort


class ListLeadsUseCase:
    def __init__(self, crm_client: CRMClientPort, logger: logging.Logger | None = None) -> None:
        self._crm_client = crm_client
        self._logger = logger or logging.getLogger(__name__)

    def execute(self, limit: int = 20, request_id: str | None = None) -> list[CRMLeadSummary]:
        leads = self._crm_client.list_leads(limit=limit, request_id=request_id)
        self._logger.info(
            "crm_leads_listed request_id=%s count=%s limit=%s",
            request_id,
            len(leads),
            limit,
        )
        return leads
