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
    """
    Verifica el estado del sistema.

    - Verifica que el sistema esté operativo
        - Retorna información básica del sistema (host y nombre de la base de datos del .env)
    """
    logger.debug("Solicitud recibida: /system/health")
    return {
        "status": "ok",
        "db_host": settings.DB_HOST,
        "db_name": settings.DB_NAME,
    }

@router.get("/db-check")
async def db_check(session: AsyncSession = Depends(get_db_session)):
    
    """
    Verifica que se pueda conectar a la base de datos.
    - Ejecuta una consulta simple para validar la conexión
    """
    logger.debug("Probando conexión a la base de datos")
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {"status": "ok", "db_response": value}

@router.get("/status")
async def auth_status():
    """
    Verifica el estado del servicio de autenticación.
    """
    logger.debug("Solicitud recibida: /auth/status")
    return {"status": "authentication service is running"}