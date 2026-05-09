from fastapi import APIRouter, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.core.redis import get_async_redis
from app.dependencies import DBSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Returns 200 if the process is up."""
    return {"status": "ok"}


@router.get("/ready")
async def readiness(db: DBSession, response: Response) -> dict[str, str]:
    """Readiness probe. Verifies DB + Redis connectivity."""
    checks: dict[str, str] = {}
    overall_ok = True
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["db"] = f"fail: {e}"
        overall_ok = False
    try:
        r = get_async_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["redis"] = f"fail: {e}"
        overall_ok = False
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if overall_ok else "degraded", **checks}


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics endpoint. Exposes default process + collector metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
