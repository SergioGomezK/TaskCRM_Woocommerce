from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator

from app.domain.entities import ClientLead

ShortText = Annotated[str, StringConstraints(min_length=1, max_length=80)]
PhoneText = Annotated[str, StringConstraints(min_length=1, max_length=30)]
CompanyText = Annotated[str, StringConstraints(min_length=1, max_length=120)]
LeadSourceText = Annotated[str, StringConstraints(min_length=1, max_length=100)]
CommentText = Annotated[str, StringConstraints(min_length=1, max_length=1000)]


class ClientFormInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: ShortText
    last_name: ShortText
    email: EmailStr
    phone: PhoneText | None = None
    company: CompanyText | None = None
    lead_source: LeadSourceText | None = None
    comment: CommentText | None = None

    @field_validator("phone", "company", "lead_source", "comment", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    def to_domain(self) -> ClientLead:
        return ClientLead(
            first_name=self.first_name,
            last_name=self.last_name,
            email=str(self.email),
            phone=self.phone,
            company=self.company,
            lead_source=self.lead_source,
            comment=self.comment,
        )
