from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.application.use_cases.resolve_checkout_link import ResolveCheckoutLinkUseCase
from app.domain.errors import (
    CRMAuthenticationError,
    CRMNetworkError,
    CRMUnexpectedError,
    InvalidCheckoutLinkError,
    WooUnexpectedError,
)
from app.presentation.dependencies import get_resolve_checkout_link_use_case

router = APIRouter(tags=["checkout-links"])


@router.get("/checkout-links/{link_id}")
async def resolve_checkout_link(
    link_id: str,
    request: Request,
    use_case: ResolveCheckoutLinkUseCase = Depends(get_resolve_checkout_link_use_case),
) -> RedirectResponse:
    request_id = getattr(request.state, "request_id", None)
    try:
        checkout_url = use_case.execute(link_id=link_id, request_id=request_id)
    except InvalidCheckoutLinkError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CRMAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except CRMNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except (CRMUnexpectedError, WooUnexpectedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return RedirectResponse(url=checkout_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
