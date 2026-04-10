import logging

from app.domain.entities import (
    CRMLeadForSync,
    LeadCheckoutLinkBatchResult,
    LeadCheckoutLinkItemResult,
    WooBilling,
    WooShipping,
)
from app.domain.ports import CRMClientPort, CheckoutLinkPort


class GenerateCheckoutLinksFromVtigerLeadsUseCase:
    def __init__(
        self,
        crm_client: CRMClientPort,
        checkout_link_builder: CheckoutLinkPort,
        *,
        pending_status: str,
        default_country: str,
        batch_limit_default: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self._crm_client = crm_client
        self._checkout_link_builder = checkout_link_builder
        self._pending_status = pending_status
        self._default_country = default_country
        self._batch_limit_default = batch_limit_default
        self._logger = logger or logging.getLogger(__name__)

    def execute(
        self, limit: int | None = None, request_id: str | None = None
    ) -> LeadCheckoutLinkBatchResult:
        effective_limit = self._resolve_limit(limit)
        leads = self._crm_client.list_leads_for_sync(
            limit=effective_limit,
            sync_status_value=self._pending_status,
            request_id=request_id,
        )

        items: list[LeadCheckoutLinkItemResult] = []
        generated = 0
        failed = 0
        skipped = 0

        for lead in leads:
            if lead.woo_order_id is not None and lead.woo_order_id != '0':
                skipped += 1
                items.append(
                    LeadCheckoutLinkItemResult(
                        lead_id=lead.lead_id,
                        status="skipped",
                        error="Lead already has woo_order_id.",
                    )
                )
                continue

            validation_error = self._validate_lead(lead)
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

            country = lead.country or self._default_country
            billing = WooBilling(
                first_name=lead.first_name or "",
                last_name=lead.last_name or "",
                email=lead.email or "",
                phone=lead.phone or "",
                address_1=lead.address_1,
                city=lead.city,
                country=country,
                state=lead.state,
                postcode=lead.postcode,
            )
            shipping = WooShipping(
                first_name=lead.first_name or "",
                last_name=lead.last_name or "",
                address_1=lead.address_1,
                city=lead.city,
                country=country,
                state=lead.state,
                postcode=lead.postcode,
            )

            checkout_url = self._checkout_link_builder.build_checkout_url(
                product_id=lead.product_id or 0,
                quantity=1,
                billing=billing,
                shipping=shipping,
            )
            generated += 1
            items.append(
                LeadCheckoutLinkItemResult(
                    lead_id=lead.lead_id,
                    status="generated",
                    checkout_url=checkout_url,
                )
            )

        processed = len(leads)
        self._logger.info(
            "vtiger_checkout_links_generated request_id=%s processed=%s generated=%s failed=%s skipped=%s",
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

    @staticmethod
    def _validate_lead(lead: CRMLeadForSync) -> str | None:
        if lead.product_id is None:
            return "Lead does not have a valid product_id."

        required_fields = {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "phone": lead.phone,
        }
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            return f"Missing required lead fields: {', '.join(missing)}"
        return None
