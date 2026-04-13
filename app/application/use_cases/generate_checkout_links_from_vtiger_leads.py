import logging
import unicodedata

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
            program_slug = _normalize_academic_program(lead.student_academic_program)
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
                billing=billing,
                shipping=shipping,
                student_id_type=lead.student_id_type,
                student_id_number=lead.student_id_number,
                student_academic_program=program_slug,
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
            "student_id_type": lead.student_id_type,
            "student_id_number": lead.student_id_number,
            "student_academic_program": lead.student_academic_program,
        }
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            return f"Missing required lead fields: {', '.join(missing)}"
        return None


def _normalize_text(value: str) -> str:
    collapsed = " ".join(value.strip().split())
    without_accents = unicodedata.normalize("NFKD", collapsed)
    ascii_only = "".join(ch for ch in without_accents if not unicodedata.combining(ch))
    return ascii_only.lower()


def _normalize_academic_program(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    if not normalized:
        return None

    mapping = {
        "tech_mba": "tech_mba",
        "master tech mba": "tech_mba",
        "ia_generativa": "ia_generativa",
        "master en inteligencia artificial": "ia_generativa",
        "data_science": "data_science",
        "master en data science": "data_science",
    }
    return mapping.get(normalized)
