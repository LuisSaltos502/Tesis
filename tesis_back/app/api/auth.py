from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from app.database.session import get_db_session
from app.schemas.user import loginSchema
from app.models.usuarios import usuarios
from app.utils.security import verify_password
from app.core.config import settings
from app.utils.security import create_access_token
from app.utils.security import get_current_user
from fastapi.security import OAuth2PasswordRequestForm


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
    # 3) Determinar el tiempo de expiración del token según el rol del usuario
    if existing_user.rol == "usuario":
        logger.info("Login exitoso de usuario: %s", user_in.correo)
        expires_minutes = settings.Access_Token_Expire_Minutes_Usuarios # Token válido para los usuarios
        
    elif existing_user.rol == "operador" or existing_user.rol == "admin":
        logger.info("Login exitoso de operador o administrador: %s", user_in.correo)
        expires_minutes = settings.Access_Token_Expire_Minutes_Operadores # Token válido para los operadores y administradores
        
    else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rol no permitido."
            )
    # 4) Crear el token JWT
    access_token = create_access_token(
        user_id=existing_user.id_usuario,
        role=existing_user.rol,
        expires_minutes=expires_minutes
    )
    return {"message": "Login exitoso", "access_token": access_token,"token_type": "bearer"}  # Placeholder hasta implementar JWT
    

@router.get("/me")
async def read_me(current_user = Depends(get_current_user)):
    return {"id_usuario": current_user.id_usuario, "rol": current_user.rol, "correo": current_user.correo}

@router.post("/token")
async def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
):
    # Swagger manda username/password (form)
    correo = form_data.username
    password = form_data.password

    # 1) Buscar usuario por correo
    result = await session.execute(
        select(usuarios).where(usuarios.correo == correo)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    # 2) Verificar password
    if not verify_password(password, existing_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    # 3) Expiración según tu settings ACTUAL
    if existing_user.rol == "usuario":
        expires_minutes = settings.Access_Token_Expire_Minutes_Usuarios
    elif existing_user.rol in ("operador", "admin"):
        expires_minutes = settings.Access_Token_Expire_Minutes_Operadores
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol no permitido.",
        )

    # 4) Crear token
    access_token = create_access_token(
        user_id=existing_user.id_usuario,
        role=existing_user.rol,
        expires_minutes=expires_minutes
    )

    # Respuesta estándar OAuth2 (Swagger la entiende)
    return {"access_token": access_token, "token_type": "bearer"}
