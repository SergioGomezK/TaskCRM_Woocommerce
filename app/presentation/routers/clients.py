from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.application.use_cases.submit_client_form import SubmitClientFormUseCase
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    CRMValidationError,
)
from app.presentation.dependencies import get_submit_client_form_use_case
from app.presentation.schemas.client_form import ClientFormInput
from app.presentation.templates import templates

router = APIRouter(prefix="/clientes", tags=["clientes"])

EMPTY_FORM_DATA = {
    "first_name": "",
    "last_name": "",
    "email": "",
    "phone": "",
    "company": "",
    "lead_source": "",
    "comment": "",
}


def _build_form_context(
    request: Request,
    form_data: dict[str, str] | None = None,
    errors: dict[str, str] | None = None,
    success_message: str | None = None,
    crm_record_id: str | None = None,
) -> dict[str, object]:
    return {
        "request": request,
        "form_data": form_data or dict(EMPTY_FORM_DATA),
        "errors": errors or {},
        "success_message": success_message,
        "crm_record_id": crm_record_id,
    }


def _validation_errors_to_messages(exc: ValidationError) -> dict[str, str]:
    messages: dict[str, str] = {}
    for item in exc.errors():
        location = item.get("loc", [])
        field = str(location[-1]) if location else "form"
        error_type = item.get("type", "")

        if field == "email":
            messages[field] = "Debe ser un correo electronico valido."
            continue
        if error_type in {"string_too_short", "missing"}:
            messages[field] = "Este campo es obligatorio."
            continue

        messages[field] = "Valor invalido."
    return messages


@router.get("/form", response_class=HTMLResponse)
async def render_client_form(request: Request) -> HTMLResponse:
    context = _build_form_context(request=request)
    return templates.TemplateResponse(request, "clients_form.html", context=context)


@router.post("/form", response_class=HTMLResponse)
async def submit_client_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    company: str = Form(""),
    lead_source: str = Form(""),
    comment: str = Form(""),
    use_case: SubmitClientFormUseCase = Depends(get_submit_client_form_use_case),
) -> HTMLResponse:
    raw_form = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "company": company,
        "lead_source": lead_source,
        "comment": comment,
    }

    try:
        form_input = ClientFormInput.model_validate(raw_form)
    except ValidationError as exc:
        context = _build_form_context(
            request=request,
            form_data=raw_form,
            errors=_validation_errors_to_messages(exc),
        )
        return templates.TemplateResponse(
            request,
            "clients_form.html",
            context=context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    request_id = getattr(request.state, "request_id", None)

    try:
        result = use_case.execute(form_input.to_domain(), request_id=request_id)
    except CRMValidationError as exc:
        context = _build_form_context(
            request=request,
            form_data=raw_form,
            errors={"crm": f"Vtiger rechazo los datos: {exc}"},
        )
        return templates.TemplateResponse(
            request,
            "clients_form.html",
            context=context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except CRMAuthenticationError:
        context = _build_form_context(
            request=request,
            form_data=raw_form,
            errors={"crm": "No fue posible autenticar con Vtiger."},
        )
        return templates.TemplateResponse(
            request,
            "clients_form.html",
            context=context,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    except CRMNetworkError:
        context = _build_form_context(
            request=request,
            form_data=raw_form,
            errors={"crm": "No fue posible conectar con Vtiger."},
        )
        return templates.TemplateResponse(
            request,
            "clients_form.html",
            context=context,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except CRMUnexpectedError:
        context = _build_form_context(
            request=request,
            form_data=raw_form,
            errors={"crm": "Ocurrio un error inesperado enviando al CRM."},
        )
        return templates.TemplateResponse(
            request,
            "clients_form.html",
            context=context,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    context = _build_form_context(
        request=request,
        success_message="Cliente enviado correctamente a Vtiger.",
        crm_record_id=result.crm_record_id,
    )
    return templates.TemplateResponse(request, "clients_form.html", context=context)
