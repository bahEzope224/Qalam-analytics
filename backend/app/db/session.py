"""
Session SQLAlchemy asynchrone.

Fournit :
- `engine`            : moteur async PostgreSQL (asyncpg)
- `AsyncSessionLocal` : factory de sessions
- `get_db()`          : générateur utilisé via FastAPI Depends()
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ---------------------------------------------------------------------------
# Moteur async
# ---------------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENV == "development"),   # log SQL uniquement en dev
    pool_pre_ping=True,                     # vérifie la connexion avant usage
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Factory de sessions
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # évite les lazy-load après commit
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Dépendance FastAPI
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:
    """
    Générateur de session SQLAlchemy async.

    Garantit la fermeture et le rollback automatique en cas d'erreur.
    À injecter dans les endpoints via ``Depends(get_db)``.

    Yields:
        AsyncSession: session active pour la durée de la requête.

    Example::

        @router.get("/example")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Site))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
