"""FastAPI application composition root."""

from fastapi import FastAPI
from scalar_fastapi import add_scalar_reference

from app.core.config import get_settings
from app.health.router import router as health_router


def create_app() -> FastAPI:
    """Build and configure a FastAPI application instance."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url=None,
        redoc_url=None,
    )
    application.include_router(health_router)
    add_scalar_reference(application, route="/docs")
    return application


app = create_app()
