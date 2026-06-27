from fastapi import APIRouter, Depends
from sqlalchemy import text
from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.database import engine
from app.utils.redis_client import redis_client

router = APIRouter(tags=["健康"])


@router.get("/health")
async def health_check():
    """服务健康检查"""
    health = {
        "status": "ok",
        "version": "0.1.0",
        "checks": {}
    }

    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Redis check
    try:
        redis_client.ping()
        health["checks"]["redis"] = "ok"
    except Exception as e:
        health["checks"]["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


@router.get("/ready")
async def readiness_check():
    """就绪检查"""
    return {"ready": True}


@router.get("/metrics")
async def metrics():
    """Prometheus 指标暴露"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
