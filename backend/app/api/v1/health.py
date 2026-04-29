from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.redis import get_async_redis
from app.dependencies import DBSession

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(db: DBSession, response: Response) -> dict[str, str]:
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
