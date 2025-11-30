from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import async_sessionmaker

DATABASE_URL = (
    
    f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_async_engine(
    
    DATABASE_URL,
    echo=False, # En caso de querer ver los queris en la consola cambiar a true
    pool_pre_ping=True, # Comprueba si la conexcion sigue viva
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
