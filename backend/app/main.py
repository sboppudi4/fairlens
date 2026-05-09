"""FastAPI application factory."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import FairLensError
from app.core.storage import ensure_bucket

# --- Prometheus metrics --------------------------------------------------
REQUESTS_TOTAL = Counter(
    "fairlens_http_requests_total",
    "Total HTTP requests, labelled by method/path/status.",
    labelnames=("method", "path", "status"),
)
REQUEST_DURATION = Histogram(
    "fairlens_http_request_duration_seconds",
    "HTTP request duration (seconds), labelled by method/path.",
    labelnames=("method", "path"),
)

# --- Rate limiter --------------------------------------------------------
# 100 req/min per remote IP, applied globally. Specific endpoints can override.
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


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

    # Rate limiting (per-IP, 100/min default)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _observability(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        dur = time.perf_counter() - start
        # Use the route template (not the literal path) to keep cardinality bounded.
        route = request.scope.get("route")
        path_label = getattr(route, "path", request.url.path)
        REQUEST_DURATION.labels(request.method, path_label).observe(dur)
        REQUESTS_TOTAL.labels(request.method, path_label, str(response.status_code)).inc()
        log = structlog.get_logger("fairlens.access")
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(dur * 1000, 2),
            client_ip=request.client.host if request.client else None,
        )
        return response

    @app.exception_handler(FairLensError)
    async def _domain_error(_req: Request, exc: FairLensError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(api_router)
    return app


app = create_app()
