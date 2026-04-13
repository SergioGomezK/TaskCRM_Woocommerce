from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WooBilling:
    first_name: str
    last_name: str
    email: str
    phone: str
    address_1: str | None = None
    city: str | None = None
    country: str | None = None
    state: str | None = None
    postcode: str | None = None


@dataclass(frozen=True, slots=True)
class WooShipping:
    first_name: str
    last_name: str
    address_1: str | None = None
    city: str | None = None
    country: str | None = None
    state: str | None = None
    postcode: str | None = None


@dataclass(frozen=True, slots=True)
class CRMLeadForSync:
    lead_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address_1: str | None = None
    city: str | None = None
    country: str | None = None
    state: str | None = None
    postcode: str | None = None
    product_id: int | None = None
    woo_order_id: str | None = None
    sync_status: str | None = None
    student_id_type: str | None = None
    student_id_number: str | None = None
    student_academic_program: str | None = None


@dataclass(frozen=True, slots=True)
class LeadCheckoutLinkItemResult:
    lead_id: str
    status: str
    link_id: str | None = None
    static_link: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class LeadCheckoutLinkBatchResult:
    processed: int
    generated: int
    failed: int
    skipped: int
    items: list[LeadCheckoutLinkItemResult]