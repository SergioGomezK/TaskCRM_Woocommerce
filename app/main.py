from fastapi import FastAPI

from app.infrastructure.logging import RequestIdMiddleware, configure_logging
from app.presentation.routers.checkout_links import router as checkout_links_router
from app.presentation.routers.health import router as health_router
from app.presentation.routers.integrations import router as integrations_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="Formulario CRM")
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health_router)
    app.include_router(integrations_router)
    app.include_router(checkout_links_router)

    return app


app = create_app()