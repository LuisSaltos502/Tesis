from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid
from app.database.session import get_db_session
from app.models.dispositivos import dispositivos
from app.schemas.dispositivos import DispositivoBase, DispositivoCreate, DispositivoUpdate,DispositivoRead
from app.utils.security import get_current_user, require_role

router = APIRouter(
    prefix="/dispositivos",
    tags=["dispositivos"],
)

logger = logging.getLogger(__name__)

@router.post("/", response_model=DispositivoRead, status_code=status.HTTP_201_CREATED)
async def crear_dispositivo(
    data: DispositivoCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """
    Crea un nuevo dispositivo asociado a un usuario.
    Reglas:
    - usuario: solo puede crear para sí mismo (data.id_usuario == current_user.id_usuario)
    - operador/admin: pueden crear para cualquier usuario
    """

    # 1) Comprobar si ya existe un dispositivo con esa MAC
    stmt = select(dispositivos).where(dispositivos.mac == data.mac)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        logger.warning("Intento de crear dispositivo con MAC duplicada: %s", data.mac)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un dispositivo registrado con esa dirección MAC.",
        )

    # 2) Generar device_key (secreto interno por dispositivo)
    device_key = uuid.uuid4().hex

    # Determinar id_usuario_final
    if current_user.rol == "usuario":
        id_usuario_final = current_user.id_usuario
    elif current_user.rol in ("admin", "operador"):
        if data.id_usuario is None or data.id_usuario <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El campo id_usuario es obligatorio para roles admin y operador.",
            )
        logger.info("DEBUG current_user: id=%s rol=%s correo=%s",
            current_user.id_usuario, current_user.rol, current_user.correo)
        id_usuario_final = data.id_usuario
    else:
        logger.error("Rol no permitido para crear dispositivo: %s", current_user.rol)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear dispositivos.",
        )

    # 3) Crear instancia del modelo
    nuevo_dispositivo = dispositivos(
        nombre=data.nombre,
        mac=data.mac,
        rol_dispositivo=data.rol_dispositivo.value,
        origen=data.origen.value,
        id_usuario=id_usuario_final,
        ubicacion_texto=data.ubicacion_texto,
        latitud=data.latitud,
        longitud=data.longitud,
        estado_dispositivo=1,
        device_key=device_key,
    )

    session.add(nuevo_dispositivo)
    await session.commit()
    await session.refresh(nuevo_dispositivo)
    
    

    logger.info(
        "Dispositivo creado: id=%s, mac=%s, usuario=%s",
        nuevo_dispositivo.id_dispositivo,
        nuevo_dispositivo.mac,
        nuevo_dispositivo.id_usuario,
    )

    return nuevo_dispositivo


@router.get("/{mac}", response_model=DispositivoRead)
async def obtener_dispositivo_por_mac(
    mac: str,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_role("admin", "usuario", "operador")),
):
    """
    Obtiene un dispositivo por su dirección MAC.
    """

    stmt = select(dispositivos).where(dispositivos.mac == mac)
    result = await session.execute(stmt)
    dispositivo = result.scalar_one_or_none()

    if dispositivo is None:
        logger.warning("Dispositivo no encontrado con MAC: %s", mac)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado.",
        )

    logger.info("Dispositivo obtenido: id=%s, mac=%s", dispositivo.id_dispositivo, dispositivo.mac)
    return dispositivo

@router.get("/", response_model=list[DispositivoRead])
async def listar_dispositivos(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user),
):
    """
    Lista dispositivos con paginación:
    - admin/operador: ve todos
    - usuario: ve solo sus dispositivos
    """

    if current_user.rol in ("admin", "operador"):
        stmt = select(dispositivos)
    else:
        stmt = select(dispositivos).where(dispositivos.id_usuario == current_user.id_usuario)

    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    dispositivos_list = result.scalars().all()

    logger.info(
        "Listando dispositivos: rol=%s, user_id=%s, skip=%d, limit=%d, total=%d",
        current_user.rol, current_user.id_usuario, skip, limit, len(dispositivos_list)
    )
    return dispositivos_list


@router.patch("/{mac}", response_model=DispositivoRead)
async def actualizar_dispositivo(
    mac: str,
    data: DispositivoUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_role("admin", "usuario", "operador")),
):
    """
    Actualiza la información de un dispositivo existente.
    """

    stmt = select(dispositivos).where(dispositivos.mac == mac)
    result = await session.execute(stmt)
    dispositivo = result.scalar_one_or_none()

    if dispositivo is None:
        logger.warning("Intento de actualizar dispositivo no encontrado con MAC: %s", mac)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado.",
        )

    # Actualizar campos
    for var, value in vars(data).items():
        if value is not None:
            setattr(dispositivo, var, value)

    session.add(dispositivo)
    await session.commit()
    await session.refresh(dispositivo)

    logger.info("Dispositivo actualizado: id=%s, mac=%s", dispositivo.id_dispositivo, dispositivo.mac)
    return dispositivo

@router.delete("/{mac}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_dispositivo(
    mac: str,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_role("admin","operador")),
):
    """
    Elimina un dispositivo por su dirección MAC.
    """

    stmt = select(dispositivos).where(dispositivos.mac == mac)
    result = await session.execute(stmt)
    dispositivo = result.scalar_one_or_none()

    if dispositivo is None:
        logger.warning("Intento de eliminar dispositivo no encontrado con MAC: %s", mac)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado.",
        )

    await session.delete(dispositivo)
    await session.commit()

    logger.info("Dispositivo eliminado: mac=%s", mac)