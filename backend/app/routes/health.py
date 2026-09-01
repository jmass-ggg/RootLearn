"""Health check endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger, get_request_id

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": get_request_id(),
    }


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Health check with database connectivity test."""
    try:
        # Execute a simple query to verify database connectivity
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": get_request_id(),
        }
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": "Database connection failed",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": get_request_id(),
        }
