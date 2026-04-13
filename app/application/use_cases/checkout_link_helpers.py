import unicodedata

from app.domain.entities import CRMLeadForSync


def validate_checkout_source_lead(lead: CRMLeadForSync) -> str | None:
    if lead.product_id is None:
        return "Lead does not have a valid product_id."

    required_fields = {
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "email": lead.email,
        "phone": lead.phone,
        "student_id_type": lead.student_id_type,
        "student_id_number": lead.student_id_number,
        "student_academic_program": lead.student_academic_program,
    }
    missing = [name for name, value in required_fields.items() if not value]
    if missing:
        return f"Missing required lead fields: {', '.join(missing)}"
    return None


def normalize_academic_program(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _normalize_text(value)
    if not normalized:
        return None

    mapping = {
        "tech_mba": "tech_mba",
        "master tech mba": "tech_mba",
        "ia_generativa": "ia_generativa",
        "master en inteligencia artificial": "ia_generativa",
        "data_science": "data_science",
        "master en data science": "data_science",
    }
    return mapping.get(normalized)


def _normalize_text(value: str) -> str:
    collapsed = " ".join(value.strip().split())
    without_accents = unicodedata.normalize("NFKD", collapsed)
    ascii_only = "".join(ch for ch in without_accents if not unicodedata.combining(ch))
    return ascii_only.lower()
