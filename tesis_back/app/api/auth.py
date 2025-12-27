from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from app.database.session import get_db_session
from app.schemas.user import loginSchema
from app.models.usuarios import usuarios
from app.utils.security import verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
logger = logging.getLogger(__name__)

@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login_user(
    user_in: loginSchema,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Login de usuario.

    - Verifica que el correo y contraseña sean correctos
    - Devuelve un token JWT (pendiente de implementar)
    """
    logger.debug("Solicitud de login para el correo %s", user_in.correo)

    # 1) Verificar si existe un usuario con ese correo
    result = await session.execute(
        select(usuarios).where(usuarios.correo == user_in.correo)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        logger.warning("Intento de login con correo no registrado: %s", user_in.correo)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    # 2) Verificar la contraseña
    if not verify_password(user_in.password, existing_user.password_hash):
        logger.warning("Intento de login con contraseña incorrecta para el correo: %s", user_in.correo)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    # 3) TODO: Generar y devolver un token JWT

    return {"message": "Login exitoso"}  # Placeholder hasta implementar JWT
    
