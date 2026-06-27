import logging
import sys
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.config import get_settings
from app.config import get_settings
from app.routers import auth, categories, documents, search, tags, stats, health
from app.utils.logging import configure_logging

settings = get_settings()
configure_logging()

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("app_starting", app_name=settings.app_name)
    logger.info("app_started", app_name=settings.app_name)
    yield
    # Shutdown
    logger.info("app_stopping", app_name=settings.app_name)


app = FastAPI(
    title="KB Search",
    description="Knowledge Base Search System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    path = request.url.path
    method = request.method
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

    # Structured logging
    logger.info(
        "request_processed",
        method=method,
        path=path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    return response


# Register routers
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(tags.router)
app.include_router(stats.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {"message": "KB Search API", "version": "0.1.0", "docs": "/docs"}
