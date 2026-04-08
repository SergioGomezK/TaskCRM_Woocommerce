import logging
from dataclasses import dataclass

from app.domain.entities import ClientLead
from app.domain.ports import CRMClientPort


@dataclass(frozen=True, slots=True)
class SubmitClientFormResult:
    crm_record_id: str


class SubmitClientFormUseCase:
    def __init__(
        self, crm_client: CRMClientPort, logger: logging.Logger | None = None
    ) -> None:
        self._crm_client = crm_client
        self._logger = logger or logging.getLogger(__name__)

    def execute(
        self, contact: ClientLead, request_id: str | None = None
    ) -> SubmitClientFormResult:
        result = self._crm_client.create_contact(contact, request_id=request_id)
        self._logger.info(
            "crm_contact_created request_id=%s crm_record_id=%s email=%s",
            request_id,
            result.crm_record_id,
            contact.email,
        )
        return SubmitClientFormResult(crm_record_id=result.crm_record_id)
