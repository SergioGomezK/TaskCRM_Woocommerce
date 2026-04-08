from typing import Protocol

from app.domain.entities import (
    CRMCreateResult,
    CRMLeadSummary,
    ClientLead,
    WooOrderInput,
    WooOrderResult,
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


class WooCommercePort(Protocol):
    def create_order(
        self, order: WooOrderInput, request_id: str | None = None
    ) -> WooOrderResult:
        """Create an order in WooCommerce."""
