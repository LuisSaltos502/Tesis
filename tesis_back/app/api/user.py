from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db_session
from app.schemas.user import UserCreate, UserRead
from app.models.usuarios import usuarios
import logging
from app.utils.security import hash_password

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
)

logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Crea un nuevo usuario.

    - Verifica que el correo no esté repetido
    - Hashea la contraseña
    - Guarda en la tabla usuarios
    """
    logger.debug("Solicitud para crear usuario con correo %s", user_in.correo)

    # 1) Verificar si ya existe un usuario con ese correo
    result = await session.execute(
        select(usuarios).where(usuarios.correo == user_in.correo, usuarios.celular == user_in.celular)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        if existing_user.correo == user_in.correo:
            logger.warning("Intento de registro con correo ya registrado: %s", user_in.correo)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado.",
            )
        if existing_user.celular == user_in.celular:
            logger.warning("Intento de registro con celular ya registrado: %s", user_in.celular)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El celular ya está registrado.",
            )

    # 2) Crear instancia del modelo
    db_user = usuarios(
        nombre=user_in.nombre,
        segundo_nombre=user_in.segundo_nombre,
        apellido=user_in.apellido,
        segundo_apellido=user_in.segundo_apellido,
        correo=user_in.correo,
        celular=user_in.celular,
        rol=user_in.rol,
        password_hash=hash_password(user_in.password),
        estado_cuenta=True,
    )

    # 3) Guardar en base
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    logger.info("Usuario creado con id %s y correo %s", db_user.id_usuario, db_user.correo)
    return db_user

@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(usuarios).where(usuarios.id_usuario == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    return user


@router.get("/", response_model=list[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    solo_activos: bool = True,
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(usuarios)

    if solo_activos:
        stmt = stmt.where(usuarios.estado_cuenta == True)  # noqa

    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    users = result.scalars().all()
    return users

from app.schemas.user import UserUpdate

@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(usuarios).where(usuarios.id_usuario == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    # Pasar el modelo Pydantic a dict ignorando campos None
    update_data = user_in.model_dump(exclude_unset=True)

    # Si se permite cambiar correo, podrías aquí verificar duplicados
    # si "correo" in update_data: hacer select para ver si ya existe otro usuario con ese correo, etc.

    for field, value in update_data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(usuarios).where(usuarios.id_usuario == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if not user.estado_cuenta:
        # Ya está inactivo, podrías devolver 400 o simplemente 204 sin hacer nada
        return

    user.estado_cuenta = False
    await session.commit()
    return


