from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClientLead:
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    company: str | None = None
    lead_source: str | None = None
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class CRMCreateResult:
    crm_record_id: str


@dataclass(frozen=True, slots=True)
class CRMLeadSummary:
    crm_record_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    lead_source: str | None = None


@dataclass(frozen=True, slots=True)
class WooOrderLineItem:
    product_id: int
    quantity: int
    variation_id: int | None = None


@dataclass(frozen=True, slots=True)
class WooBilling:
    first_name: str
    last_name: str
    email: str 
    phone: str
    address_1: str | None = None
    city: str  | None = None
    country: str | None = None
    address_2: str | None = None
    state: str | None = None
    postcode: str | None = None


@dataclass(frozen=True, slots=True)
class WooShipping:
    first_name: str
    last_name: str
    address_1: str | None = None
    city: str | None = None
    country: str | None = None
    address_2: str | None = None
    state: str | None = None
    postcode: str | None = None


@dataclass(frozen=True, slots=True)
class WooOrderInput:
    payment_method: str
    payment_method_title: str
    set_paid: bool
    billing: WooBilling
    shipping: WooShipping
    line_items: list[WooOrderLineItem]
    customer_note: str | None = None


@dataclass(frozen=True, slots=True)
class WooOrderResult:
    order_id: int
    status: str
    total: str
    currency: str


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
class LeadSyncItemResult:
    lead_id: str
    status: str
    woo_order_id: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class LeadSyncBatchResult:
    processed: int
    created: int
    failed: int
    skipped: int
    items: list[LeadSyncItemResult]


@dataclass(frozen=True, slots=True)
class LeadCheckoutLinkItemResult:
    lead_id: str
    status: str
    checkout_url: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class LeadCheckoutLinkBatchResult:
    processed: int
    generated: int
    failed: int
    skipped: int
    items: list[LeadCheckoutLinkItemResult]
