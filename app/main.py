from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.infrastructure.logging import RequestIdMiddleware, configure_logging
from app.presentation.routers.clients import router as clients_router
from app.presentation.routers.health import router as health_router
from app.presentation.routers.integrations import router as integrations_router
from app.presentation.routers.leads import router as leads_router
from app.presentation.routers.woocommerce import router as woocommerce_router


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="Formulario CRM")
    app.add_middleware(RequestIdMiddleware)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(health_router)
    app.include_router(clients_router)
    app.include_router(leads_router)
    app.include_router(woocommerce_router)
    app.include_router(integrations_router)

    return app


app = create_app()
