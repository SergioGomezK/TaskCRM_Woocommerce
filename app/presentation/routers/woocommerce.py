from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.application.use_cases.create_woo_order import CreateWooOrderUseCase
from app.domain.errors import (
    WooAuthenticationError,
    WooNetworkError,
    WooUnexpectedError,
    WooValidationError,
)
from app.presentation.dependencies import get_create_woo_order_use_case
from app.presentation.schemas.woocommerce_order import (
    WooCreateOrderRequest,
    WooCreateOrderResponse,
)

router = APIRouter(prefix="/woocommerce", tags=["woocommerce"])


@router.post("/orders", response_model=WooCreateOrderResponse, deprecated=True)
async def create_order(
    payload: WooCreateOrderRequest,
    request: Request,
    use_case: CreateWooOrderUseCase = Depends(get_create_woo_order_use_case),
) -> WooCreateOrderResponse:
    request_id = getattr(request.state, "request_id", None)
    try:
        result = use_case.execute(payload.to_domain(), request_id=request_id)
    except WooValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"WooCommerce validation error: {exc}",
        ) from exc
    except WooAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce authentication error: {exc}",
        ) from exc
    except WooNetworkError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"WooCommerce network error: {exc}",
        ) from exc
    except WooUnexpectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce unexpected error: {exc}",
        ) from exc

    return WooCreateOrderResponse(
        order_id=result.order_id,
        status=result.status,
        total=result.total,
        currency=result.currency,
    )
