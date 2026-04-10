import logging

from app.domain.entities import (
    CRMLeadForSync,
    LeadSyncBatchResult,
    LeadSyncItemResult,
    WooBilling,
    WooOrderInput,
    WooOrderLineItem,
    WooShipping,
)
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    CRMValidationError,
    WooAuthenticationError,
    WooNetworkError,
    WooUnexpectedError,
    WooValidationError,
)
from app.domain.ports import CRMClientPort, WooCommercePort


class SyncVtigerLeadsToWooOrdersUseCase:
    def __init__(
        self,
        crm_client: CRMClientPort,
        woo_client: WooCommercePort,
        *,
        pending_status: str,
        processed_status: str,
        failed_status: str,
        default_country: str,
        default_payment_method: str,
        default_payment_method_title: str,
        default_set_paid: bool,
        batch_limit_default: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self._crm_client = crm_client
        self._woo_client = woo_client
        self._pending_status = pending_status
        self._processed_status = processed_status
        self._failed_status = failed_status
        self._default_country = default_country
        self._default_payment_method = default_payment_method
        self._default_payment_method_title = default_payment_method_title
        self._default_set_paid = default_set_paid
        self._batch_limit_default = batch_limit_default
        self._logger = logger or logging.getLogger(__name__)

    def execute(
        self, limit: int | None = None, request_id: str | None = None
    ) -> LeadSyncBatchResult:
        effective_limit = self._resolve_limit(limit)
        leads = self._crm_client.list_leads_for_sync(
            limit=effective_limit,
            sync_status_value=self._pending_status,
            request_id=request_id,
        )

        items: list[LeadSyncItemResult] = []
        created = 0
        failed = 0
        skipped = 0

        for lead in leads:
            if self._is_already_processed(lead):
                skipped += 1
                items.append(
                    LeadSyncItemResult(
                        lead_id=lead.lead_id,
                        status="skipped",
                        woo_order_id=lead.woo_order_id,
                        error="Lead already processed.",
                    )
                )
                continue

            order_or_error = self._build_order_from_lead(lead)
            if isinstance(order_or_error, str):
                failed += 1
                error_message = order_or_error
                self._persist_sync_result(
                    lead_id=lead.lead_id,
                    sync_status=self._failed_status,
                    sync_error=error_message,
                    request_id=request_id,
                )
                items.append(
                    LeadSyncItemResult(
                        lead_id=lead.lead_id,
                        status="failed",
                        error=error_message,
                    )
                )
                continue

            try:
                order_result = self._woo_client.create_order(
                    order_or_error, request_id=request_id
                )
            except (
                WooValidationError,
                WooAuthenticationError,
                WooNetworkError,
                WooUnexpectedError,
            ) as exc:
                failed += 1
                error_message = _truncate_error(str(exc))
                self._persist_sync_result(
                    lead_id=lead.lead_id,
                    sync_status=self._failed_status,
                    sync_error=error_message,
                    request_id=request_id,
                )
                items.append(
                    LeadSyncItemResult(
                        lead_id=lead.lead_id,
                        status="failed",
                        error=error_message,
                    )
                )
                continue

            created += 1
            woo_order_id = str(order_result.order_id)
            self._persist_sync_result(
                lead_id=lead.lead_id,
                sync_status=self._processed_status,
                woo_order_id=woo_order_id,
                sync_error=None,
                request_id=request_id,
            )
            items.append(
                LeadSyncItemResult(
                    lead_id=lead.lead_id,
                    status="created",
                    woo_order_id=woo_order_id,
                )
            )

        processed = len(leads)
        self._logger.info(
            "vtiger_to_woo_sync_finished request_id=%s processed=%s created=%s failed=%s skipped=%s",
            request_id,
            processed,
            created,
            failed,
            skipped,
        )
        return LeadSyncBatchResult(
            processed=processed,
            created=created,
            failed=failed,
            skipped=skipped,
            items=items,
        )

    def _resolve_limit(self, limit: int | None) -> int:
        if limit is None:
            return self._batch_limit_default
        return max(1, min(limit, 500))

    def _is_already_processed(self, lead: CRMLeadForSync) -> bool:
        if lead.woo_order_id:
            return True
        if lead.sync_status is None:
            return False
        return lead.sync_status.lower() == self._processed_status.lower()

    def _build_order_from_lead(self, lead: CRMLeadForSync) -> WooOrderInput | str:
        if lead.product_id is None:
            return "Lead does not have a valid product_id."

        required_fields = {
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "email": lead.email,
            "phone": lead.phone
            
        }
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            return f"Missing required lead fields: {', '.join(missing)}"

        country = lead.country or self._default_country

        return WooOrderInput(
            payment_method=self._default_payment_method,
            payment_method_title=self._default_payment_method_title,
            set_paid=self._default_set_paid,
            billing=WooBilling(
                first_name=lead.first_name or "",
                last_name=lead.last_name or "",
                address_1=lead.address_1 or "",
                city=lead.city or "",
                country=country,
                email=lead.email or "",
                phone=lead.phone or "",
                state=lead.state,
                postcode=lead.postcode,
            ),
            shipping=WooShipping(
                first_name=lead.first_name or "",
                last_name=lead.last_name or "",
                address_1=lead.address_1 or "",
                city=lead.city or "",
                country=country,
                state=lead.state,
                postcode=lead.postcode,
            ),
            line_items=[WooOrderLineItem(product_id=lead.product_id, quantity=1)],
            customer_note=f"Created from Vtiger lead {lead.lead_id}",
        )

    def _persist_sync_result(
        self,
        *,
        lead_id: str,
        sync_status: str,
        woo_order_id: str | None = None,
        sync_error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        try:
            self._crm_client.update_lead_sync_result(
                lead_id=lead_id,
                sync_status=sync_status,
                woo_order_id=woo_order_id,
                sync_error=sync_error,
                request_id=request_id,
            )
        except (
            CRMValidationError,
            CRMAuthenticationError,
            CRMNetworkError,
            CRMUnexpectedError,
        ) as exc:
            self._logger.error(
                "sync_result_persist_failed lead_id=%s request_id=%s error=%s",
                lead_id,
                request_id,
                exc,
            )


def _truncate_error(value: str, max_length: int = 240) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3] + "..."
