from app.domain.entities import ClientLead
from app.infrastructure.vtiger.mappers import map_client_to_vtiger_contact


def test_map_client_to_vtiger_contact_required_fields() -> None:
    payload = map_client_to_vtiger_contact(
        ClientLead(
            first_name="Ana",
            last_name="Perez",
            email="ana@example.com",
        ),
        assigned_user_id="19x1",
    )

    assert payload["firstname"] == "Ana"
    assert payload["lastname"] == "Perez"
    assert payload["email"] == "ana@example.com"
    assert payload["assigned_user_id"] == "19x1"


def test_map_client_to_vtiger_contact_description_merge() -> None:
    payload = map_client_to_vtiger_contact(
        ClientLead(
            first_name="Ana",
            last_name="Perez",
            email="ana@example.com",
            company="ACME",
            comment="Necesita cotizacion",
            lead_source="Web",
        ),
        assigned_user_id="19x1",
    )

    assert payload["leadsource"] == "Web"
    assert "Empresa: ACME" in payload["description"]
    assert "Comentario: Necesita cotizacion" in payload["description"]
