from typing import Protocol

from app.domain.entities import (
    CRMCreateResult,
    CRMLeadForSync,
    CRMLeadSummary,
    ClientLead,
    WooBilling,
    WooOrderInput,
    WooOrderResult,
    WooShipping,
)


class CRMClientPort(Protocol):
    def create_contact(
        self, contact: ClientLead, request_id: str | None = None
    ) -> CRMCreateResult:
        """Create a contact in CRM and return its identifier."""

    def list_leads(
        self, limit: int = 20, request_id: str | None = None
    ) -> list[CRMLeadSummary]:
        """List leads from CRM."""

    def list_leads_for_sync(
        self,
        *,
        limit: int,
        sync_status_value: str,
        request_id: str | None = None,
    ) -> list[CRMLeadForSync]:
        """List leads that are candidates to sync with WooCommerce."""

    def update_lead_sync_result(
        self,
        *,
        lead_id: str,
        sync_status: str,
        woo_order_id: str | None = None,
        sync_error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Persist synchronization result in lead custom fields."""


class WooCommercePort(Protocol):
    def create_order(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        """Create an order in WooCommerce."""


class CheckoutLinkPort(Protocol):
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
        """Build a WooCommerce checkout URL with prefilled parameters."""
