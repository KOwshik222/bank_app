"""
AI-Powered Banking Incident Resolution & Root Cause Analysis Agent
==================================================================
FastAPI application entry point.

Start with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.events import get_event_bus

settings = get_settings()


from logging.handlers import RotatingFileHandler
from pathlib import Path

def _file_sink_processor(logger, method_name, event_dict):
    """Write structlog event to persistent banking_app.log file."""
    import json
    try:
        log_file = settings.logs_dir / "banking_app.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_dict, default=str) + "\n")
    except Exception:
        pass
    return event_dict


def configure_logging() -> None:
    """Configure structured JSON logging and rotating file handler."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.logs_dir / "banking_app.log"

    # Configure root standard logger for uvicorn, sqlalchemy, and app modules
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            log_file, maxBytes=15 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s"}'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            _file_sink_processor,
            structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown hooks."""
    configure_logging()
    log = structlog.get_logger()

    # Startup
    log.info("Starting AI Banking Incident Resolution Agent", version=settings.app_version)
    await init_db()
    log.info("Database initialized")

    event_bus = get_event_bus()
    await event_bus.start()
    log.info("Event bus started")

    yield

    # Shutdown
    log.info("Shutting down...")
    await event_bus.stop()
    await close_db()
    log.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered platform that investigates simulated banking application incidents, "
        "performs root cause analysis, recommends remediation with human approval, "
        "and verifies fixes."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ───────────────────────────────────────────────────
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.metrics import MetricsMiddleware, get_prometheus_metrics

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)

from starlette.requests import Request
from fastapi.responses import JSONResponse
from app.services.external_bank_client import ExternalBankingOutageError

@app.exception_handler(ExternalBankingOutageError)
async def external_outage_handler(request: Request, exc: ExternalBankingOutageError):
    err_log = logging.getLogger("payment-service")
    err_log.error(
        f"GatewayTimeoutException: External provider unreachable after 10000ms: {exc.error_code} on {request.url.path}: {exc.message}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Third-Party Payment Processor Outage", "error_code": exc.error_code, "message": exc.message},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    err_log = logging.getLogger("banking.unhandled_error")
    err_log.error(
        f"Unhandled error processing {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_type": type(exc).__name__, "message": str(exc)},
    )

# ── Register Routers ─────────────────────────────────────────────
from app.routers import accounts, ai, audit, auth, customers, incidents, payments, transactions

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(accounts.router)
app.include_router(payments.router)
app.include_router(transactions.router)
app.include_router(incidents.router)
app.include_router(audit.router)
app.include_router(ai.router)


# ── Health & Observability ───────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
    }


@app.get("/metrics", tags=["System"])
async def prometheus_metrics():
    """Prometheus exposition metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(get_prometheus_metrics(), media_type="text/plain; version=0.0.4")


# ── Static Files & Dashboard UI ──────────────────────────────────
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["Dashboard"])
@app.get("/dashboard", tags=["Dashboard"])
async def dashboard():
    """Banking Incident Command Center UI."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
