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
    address_1: str
    city: str
    country: str
    email: str
    phone: str
    address_2: str | None = None
    state: str | None = None
    postcode: str | None = None


@dataclass(frozen=True, slots=True)
class WooShipping:
    first_name: str
    last_name: str
    address_1: str
    city: str
    country: str
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
