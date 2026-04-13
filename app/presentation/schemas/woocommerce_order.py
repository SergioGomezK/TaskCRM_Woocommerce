from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.domain.entities import (
    WooBilling,
    WooOrderInput,
    WooOrderLineItem,
    WooShipping,
)

ShortText = Annotated[str, StringConstraints(min_length=1, max_length=120)]
AddressText = Annotated[str, StringConstraints(min_length=1, max_length=255)]
OptionalText = Annotated[str, StringConstraints(min_length=1, max_length=255)]


class WooLineItemInput(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    variation_id: int | None = Field(default=None, gt=0)

    model_config = ConfigDict(str_strip_whitespace=True)

    def to_domain(self) -> WooOrderLineItem:
        return WooOrderLineItem(
            product_id=self.product_id,
            quantity=self.quantity,
            variation_id=self.variation_id,
        )


class WooBillingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: ShortText
    last_name: ShortText
    address_1: AddressText | None = None
    address_2: OptionalText | None = None
    city: ShortText | None = None
    state: OptionalText | None = None
    postcode: OptionalText | None = None
    country: Annotated[str, StringConstraints(min_length=2, max_length=2)]
    email: EmailStr
    phone: ShortText

    @field_validator("address_1", "address_2", "city", "state", "postcode", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.upper()

    def to_domain(self) -> WooBilling:
        return WooBilling(
            first_name=self.first_name,
            last_name=self.last_name,
            address_1=self.address_1,
            address_2=self.address_2,
            city=self.city,
            state=self.state,
            postcode=self.postcode,
            country=self.country,
            email=str(self.email),
            phone=self.phone,
        )


class WooShippingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: ShortText
    last_name: ShortText
    address_1: AddressText | None = None
    address_2: OptionalText | None = None
    city: ShortText | None = None
    state: OptionalText | None = None
    postcode: OptionalText | None = None
    country: Annotated[str, StringConstraints(min_length=2, max_length=2)]

    @field_validator("address_1", "address_2", "city", "state", "postcode", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.upper()

    def to_domain(self) -> WooShipping:
        return WooShipping(
            first_name=self.first_name,
            last_name=self.last_name,
            address_1=self.address_1,
            address_2=self.address_2,
            city=self.city,
            state=self.state,
            postcode=self.postcode,
            country=self.country,
        )


class WooCreateOrderRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    payment_method: ShortText
    payment_method_title: ShortText
    set_paid: bool = False
    billing: WooBillingInput
    shipping: WooShippingInput
    line_items: list[WooLineItemInput] = Field(..., min_length=1)
    customer_note: Annotated[str, StringConstraints(min_length=1, max_length=1000)] | None = None

    @field_validator("customer_note", mode="before")
    @classmethod
    def empty_note_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def to_domain(self) -> WooOrderInput:
        return WooOrderInput(
            payment_method=self.payment_method,
            payment_method_title=self.payment_method_title,
            set_paid=self.set_paid,
            billing=self.billing.to_domain(),
            shipping=self.shipping.to_domain(),
            line_items=[item.to_domain() for item in self.line_items],
            customer_note=self.customer_note,
        )


class WooCreateOrderResponse(BaseModel):
    order_id: int
    status: str
    total: str
    currency: str
