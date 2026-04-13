from app.application.use_cases.checkout_link_helpers import (
    normalize_academic_program,
    validate_checkout_source_lead,
)
from app.domain.entities import WooBilling, WooShipping
from app.domain.errors import InvalidCheckoutLinkError
from app.domain.ports import CRMClientPort, CheckoutLinkIdentityPort, CheckoutLinkPort


class ResolveCheckoutLinkUseCase:
    def __init__(
        self,
        crm_client: CRMClientPort,
        checkout_link_builder: CheckoutLinkPort,
        link_identity: CheckoutLinkIdentityPort,
        *,
        default_country: str,
    ) -> None:
        self._crm_client = crm_client
        self._checkout_link_builder = checkout_link_builder
        self._link_identity = link_identity
        self._default_country = default_country

    def execute(self, *, link_id: str, request_id: str | None = None) -> str:
        lead_id = self._link_identity.get_lead_id(link_id)
        if not lead_id:
            raise InvalidCheckoutLinkError("Invalid checkout link.")

        lead = self._crm_client.get_lead_for_checkout(
            lead_id=lead_id,
            request_id=request_id,
        )
        if lead is None:
            raise InvalidCheckoutLinkError("Lead not found for checkout link.")

        validation_error = validate_checkout_source_lead(lead)
        if validation_error:
            raise InvalidCheckoutLinkError(validation_error)

        program_slug = normalize_academic_program(lead.student_academic_program)
        if program_slug is None:
            raise InvalidCheckoutLinkError("Invalid student_academic_program.")

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
        return self._checkout_link_builder.build_checkout_url(
            product_id=lead.product_id or 0,
            billing=billing,
            shipping=shipping,
            student_id_type=lead.student_id_type,
            student_id_number=lead.student_id_number,
            student_academic_program=program_slug,
        )
