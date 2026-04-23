"""FastAPI application factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import FairLensError
from app.core.storage import ensure_bucket


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _configure_logging(settings.LOG_LEVEL)
    log = structlog.get_logger("fairlens.startup")
    try:
        ensure_bucket()
        log.info("storage.bucket_ready", bucket=settings.AWS_BUCKET_NAME)
    except Exception as e:  # noqa: BLE001
        # MinIO may not be ready immediately on first compose up; the worker / first request will retry.
        log.warning("storage.bucket_init_failed", error=str(e))
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="FairLens API",
        version="0.1.0",
        description="AI Fairness Audit Platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(FairLensError)
    async def _domain_error(_req: Request, exc: FairLensError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(api_router)
    return app


app = create_app()
