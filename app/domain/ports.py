from typing import Protocol

from app.domain.entities import CRMLeadForSync, WooBilling, WooShipping


class CRMClientPort(Protocol):
    def list_leads_for_sync(
        self,
        *,
        limit: int,
        sync_status_value: str,
        request_id: str | None = None,
    ) -> list[CRMLeadForSync]:
        """List leads that are candidates to generate checkout links."""

    def get_lead_for_checkout(
        self, *, lead_id: str, request_id: str | None = None
    ) -> CRMLeadForSync | None:
        """Get a single lead by id for checkout-link resolution."""


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


class CheckoutLinkIdentityPort(Protocol):
    def create_link_id(self, lead_id: str) -> str:
        """Create deterministic link id for a lead id."""

    def get_lead_id(self, link_id: str) -> str | None:
        """Validate link id and return embedded lead id."""