import logging
from urllib.parse import quote

from app.application.use_cases.checkout_link_helpers import (
    normalize_academic_program,
    validate_checkout_source_lead,
)
from app.domain.entities import LeadCheckoutLinkBatchResult, LeadCheckoutLinkItemResult
from app.domain.ports import CRMClientPort, CheckoutLinkIdentityPort


class GenerateCheckoutLinksFromVtigerLeadsUseCase:
    def __init__(
        self,
        crm_client: CRMClientPort,
        link_identity: CheckoutLinkIdentityPort,
        *,
        pending_status: str,
        batch_limit_default: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self._crm_client = crm_client
        self._link_identity = link_identity
        self._pending_status = pending_status
        self._batch_limit_default = batch_limit_default
        self._logger = logger or logging.getLogger(__name__)

    def execute(
        self,
        *,
        public_base_url: str,
        limit: int | None = None,
        request_id: str | None = None,
    ) -> LeadCheckoutLinkBatchResult:
        effective_limit = self._resolve_limit(limit)
        leads = self._crm_client.list_leads_for_sync(
            limit=effective_limit,
            sync_status_value=self._pending_status,
            request_id=request_id,
        )

        base_url = public_base_url.rstrip("/")
        items: list[LeadCheckoutLinkItemResult] = []
        generated = 0
        failed = 0
        skipped = 0

        for lead in leads:
            if lead.woo_order_id is not None and lead.woo_order_id != "0":
                skipped += 1
                items.append(
                    LeadCheckoutLinkItemResult(
                        lead_id=lead.lead_id,
                        status="skipped",
                        error="Lead already has woo_order_id.",
                    )
                )
                continue

            validation_error = validate_checkout_source_lead(lead)
            if validation_error:
                failed += 1
                items.append(
                    LeadCheckoutLinkItemResult(
                        lead_id=lead.lead_id,
                        status="failed",
                        error=validation_error,
                    )
                )
                continue

            program_slug = normalize_academic_program(lead.student_academic_program)
            if program_slug is None:
                failed += 1
                items.append(
                    LeadCheckoutLinkItemResult(
                        lead_id=lead.lead_id,
                        status="failed",
                        error=(
                            "Invalid student_academic_program. Allowed values: "
                            "tech_mba, ia_generativa, data_science "
                            "(or their WordPress labels)."
                        ),
                    )
                )
                continue

            link_id = self._link_identity.create_link_id(lead.lead_id)
            generated += 1
            items.append(
                LeadCheckoutLinkItemResult(
                    lead_id=lead.lead_id,
                    status="generated",
                    link_id=link_id,
                    static_link=f"{base_url}/checkout-links/{quote(link_id, safe='')}",
                )
            )

        processed = len(leads)
        self._logger.info(
            "vtiger_static_links_generated request_id=%s processed=%s generated=%s failed=%s skipped=%s",
            request_id,
            processed,
            generated,
            failed,
            skipped,
        )
        return LeadCheckoutLinkBatchResult(
            processed=processed,
            generated=generated,
            failed=failed,
            skipped=skipped,
            items=items,
        )

    def _resolve_limit(self, limit: int | None) -> int:
        if limit is None:
            return self._batch_limit_default
        return max(1, min(limit, 500))
