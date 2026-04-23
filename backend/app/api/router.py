from fastapi import APIRouter

from app.api.v1 import audits, auth, datasets, health, reports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(datasets.router, prefix="/api/v1")
api_router.include_router(audits.router, prefix="/api/v1")
api_router.include_router(reports.router, prefix="/api/v1")
