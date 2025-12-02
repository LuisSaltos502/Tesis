from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from app.database.session import get_db_session
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])

# Endpoint básico de verificación
@router.get("/health")
async def health_check():
    logger.debug("Solicitud recibida: /system/health")
    return {
        "status": "ok",
        "db_host": settings.DB_HOST,
        "db_name": settings.DB_NAME,
    }

@router.get("/db-check")
async def db_check(session: AsyncSession = Depends(get_db_session)):
    logger.debug("Probando conexión a la base de datos")
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {"status": "ok", "db_response": value}
