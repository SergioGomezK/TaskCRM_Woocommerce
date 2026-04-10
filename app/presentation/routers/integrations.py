from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.application.use_cases.generate_checkout_links_from_vtiger_leads import (
    GenerateCheckoutLinksFromVtigerLeadsUseCase,
)
from app.application.use_cases.sync_vtiger_leads_to_woo_orders import (
    SyncVtigerLeadsToWooOrdersUseCase,
)
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    CRMValidationError,
    WooAuthenticationError,
    WooNetworkError,
    WooUnexpectedError,
    WooValidationError,
)
from app.infrastructure.config import Settings, get_settings
from app.presentation.dependencies import (
    get_generate_checkout_links_from_vtiger_leads_use_case,
    get_sync_vtiger_leads_to_woo_orders_use_case,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class LeadSyncItemResponse(BaseModel):
    lead_id: str
    status: str
    woo_order_id: str | None = None
    error: str | None = None


class LeadSyncBatchResponse(BaseModel):
    processed: int
    created: int
    failed: int
    skipped: int
    items: list[LeadSyncItemResponse]


class LeadCheckoutLinkItemResponse(BaseModel):
    lead_id: str
    status: str
    checkout_url: str | None = None
    error: str | None = None


class LeadCheckoutLinkBatchResponse(BaseModel):
    processed: int
    generated: int
    failed: int
    skipped: int
    items: list[LeadCheckoutLinkItemResponse]


def _validate_integration_key(
    *,
    settings: Settings,
    integration_key: str | None,
) -> None:
    expected_key = (
        settings.integration_api_key.get_secret_value()
        if settings.integration_api_key is not None
        else None
    )
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Integration API key is not configured.",
        )
    if integration_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid integration key.",
        )


@router.post("/vtiger/leads-to-orders/sync", response_model=LeadSyncBatchResponse)
async def sync_vtiger_leads_to_orders(
    request: Request,
    limit: int | None = Query(default=None, ge=1, le=500),
    integration_key: str | None = Header(default=None, alias="X-Integration-Key"),
    settings: Settings = Depends(get_settings),
    use_case: SyncVtigerLeadsToWooOrdersUseCase = Depends(
        get_sync_vtiger_leads_to_woo_orders_use_case
    ),
) -> LeadSyncBatchResponse:
    _validate_integration_key(settings=settings, integration_key=integration_key)

    request_id = getattr(request.state, "request_id", None)

    try:
        result = use_case.execute(limit=limit, request_id=request_id)
    except (CRMValidationError, WooValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (CRMAuthenticationError, WooAuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except (CRMNetworkError, WooNetworkError) as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (CRMUnexpectedError, WooUnexpectedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return LeadSyncBatchResponse(
        processed=result.processed,
        created=result.created,
        failed=result.failed,
        skipped=result.skipped,
        items=[LeadSyncItemResponse.model_validate(asdict(item)) for item in result.items],
    )


@router.post(
    "/vtiger/leads-to-checkout-links/sync",
    response_model=LeadCheckoutLinkBatchResponse,
)
async def generate_checkout_links_from_vtiger_leads(
    request: Request,
    limit: int | None = Query(default=None, ge=1, le=500),
    integration_key: str | None = Header(default=None, alias="X-Integration-Key"),
    settings: Settings = Depends(get_settings),
    use_case: GenerateCheckoutLinksFromVtigerLeadsUseCase = Depends(
        get_generate_checkout_links_from_vtiger_leads_use_case
    ),
) -> LeadCheckoutLinkBatchResponse:
    _validate_integration_key(settings=settings, integration_key=integration_key)
    request_id = getattr(request.state, "request_id", None)

    try:
        result = use_case.execute(limit=limit, request_id=request_id)
    except (CRMValidationError, WooValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (CRMAuthenticationError, WooAuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except (CRMNetworkError, WooNetworkError) as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (CRMUnexpectedError, WooUnexpectedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return LeadCheckoutLinkBatchResponse(
        processed=result.processed,
        generated=result.generated,
        failed=result.failed,
        skipped=result.skipped,
        items=[
            LeadCheckoutLinkItemResponse.model_validate(asdict(item))
            for item in result.items
        ],
    )
