from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.db.session import get_db

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Liveness + cheap DB ping for compose / uptime monitors."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("health_db_ping_failed", error=str(exc))

    status = "healthy" if db_ok else "degraded"
    logger.info("health_check_v1_called", status=status, db_ok=db_ok)
    return {
        "status": status,
        "service": "nexorux-erp-api",
        "version": "0.1.0",
        "checks": {"database": db_ok},
    }
