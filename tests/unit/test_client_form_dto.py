import pytest
from pydantic import ValidationError

from app.presentation.schemas.client_form import ClientFormInput


def test_client_form_accepts_valid_payload() -> None:
    form = ClientFormInput(
        first_name=" Ana ",
        last_name="Perez",
        email="ANA@Example.com",
        phone="3001234567",
        company="ACME",
        lead_source="Web",
        comment="Interes en demo",
    )

    assert form.first_name == "Ana"
    assert form.email == "ana@example.com"
    assert form.to_domain().company == "ACME"


def test_client_form_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        ClientFormInput(
            first_name="Ana",
            last_name="Perez",
            email="invalid-email",
        )


def test_client_form_requires_last_name() -> None:
    with pytest.raises(ValidationError):
        ClientFormInput(
            first_name="Ana",
            last_name="",
            email="ana@example.com",
        )
