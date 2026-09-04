"""HTTP endpoints for application health."""

from fastapi import APIRouter, status

from app.health.dependencies import SettingsDependency
from app.health.schemas import LivenessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check whether the API process is alive",
)
def get_liveness(settings: SettingsDependency) -> LivenessResponse:
    """Return process-level health without checking external dependencies."""
    return LivenessResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
    )
