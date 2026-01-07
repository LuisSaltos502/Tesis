from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from app.database.session import get_db_session
from app.core.config import settings
from app.utils.security import require_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["system"])

@router.get("/db-check")
async def db_check(
    session: AsyncSession = Depends(get_db_session), 
    current_user=Depends(require_role("admin", "usuario", "operador")),
    ):
    
    """
    Verifica que se pueda conectar a la base de datos.
    - Ejecuta una consulta simple para validar la conexión
    """
    logger.debug("Probando conexión a la base de datos")
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {"status": "ok", "db_response": value}

