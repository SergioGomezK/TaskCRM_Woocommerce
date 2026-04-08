from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.application.use_cases.list_leads import ListLeadsUseCase
from app.domain.errors import CRMAuthenticationError, CRMNetworkError, CRMUnexpectedError
from app.presentation.dependencies import get_list_leads_use_case

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadResponse(BaseModel):
    crm_record_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    lead_source: str | None = None


class LeadsListResponse(BaseModel):
    count: int
    limit: int
    data: list[LeadResponse]


@router.get("", response_model=LeadsListResponse)
async def list_leads(
    request: Request,
    limit: int = Query(default=20, ge=1, le=200),
    use_case: ListLeadsUseCase = Depends(get_list_leads_use_case),
) -> LeadsListResponse:
    request_id = getattr(request.state, "request_id", None)
    try:
        leads = use_case.execute(limit=limit, request_id=request_id)
    except CRMAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Authentication error with Vtiger: {exc}",
        ) from exc
    except CRMNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Network error with Vtiger: {exc}",
        ) from exc
    except CRMUnexpectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected Vtiger error: {exc}",
        ) from exc

    return LeadsListResponse(
        count=len(leads),
        limit=limit,
        data=[LeadResponse.model_validate(asdict(lead)) for lead in leads],
    )
