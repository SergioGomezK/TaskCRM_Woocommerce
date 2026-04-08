from app.domain.entities import ClientLead


def map_client_to_vtiger_contact(
    contact: ClientLead, assigned_user_id: str
) -> dict[str, str]:
    payload: dict[str, str] = {
        "firstname": contact.first_name,
        "lastname": contact.last_name,
        "email": contact.email,
        "assigned_user_id": assigned_user_id,
    }

    if contact.phone:
        payload["phone"] = contact.phone
    if contact.lead_source:
        payload["leadsource"] = contact.lead_source

    description_lines: list[str] = []
    if contact.company:
        description_lines.append(f"Empresa: {contact.company}")
    if contact.comment:
        description_lines.append(f"Comentario: {contact.comment}")
    if description_lines:
        payload["description"] = "\n".join(description_lines)

    return payload
