"""
Dépendances communes FastAPI – v1.

Fournit :
- ``get_db``           : session SQLAlchemy async (ré-exportée depuis db.session)
- ``get_current_user`` : utilisateur authentifié via JWT Bearer
- ``get_current_admin``: idem, mais vérifie is_admin=True
- ``PaginationParams`` : paramètres de pagination communs
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import extract_token_subject
from app.db.session import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Ré-export de get_db pour import unifié depuis dependencies
# ---------------------------------------------------------------------------

# Les routers importent get_db depuis ici plutôt que depuis db.session
# pour centraliser les dépendances au même endroit.
__all__ = ["get_db", "get_current_user", "get_current_admin", "PaginationParams"]

# Schéma Bearer pour l'extraction automatique du token depuis Authorization header
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Dépendance principale d'authentification.

    Extrait et valide le Bearer JWT depuis le header ``Authorization``,
    puis charge l'utilisateur correspondant depuis la base de données.
    Si AUTH_ENABLED est à False, renvoie un utilisateur fictif pour le dev.
    """
    from app.core.config import settings

    if not settings.AUTH_ENABLED:
        # Tente de trouver un utilisateur existant dans la base
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user is None:
            # Crée un utilisateur de test par défaut
            user = User(
                email="admin@qalam-analytics.local",
                full_name="Administrateur de Test",
                hashed_password="fakehashedpassword",
                is_active=True,
                is_admin=True,
            )
            db.add(user)
            await db.flush()
        return user

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Décoder le token et extraire le sujet (email)
    email = extract_token_subject(credentials.credentials)

    # 2. Charger l'utilisateur depuis la DB
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou token révoqué.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Vérifier que le compte est actif
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé. Contactez un administrateur.",
        )

    return user


# ---------------------------------------------------------------------------
# get_current_admin
# ---------------------------------------------------------------------------

async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dépendance d'authentification avec vérification des droits admin.

    Identique à ``get_current_user`` mais lève une 403 si l'utilisateur
    n'est pas administrateur.

    Utilisé pour protéger les routes de gestion des sites et des paramètres
    (screen_2 : Settings, ajout/suppression de sites GA4).

    Args:
        current_user: Utilisateur authentifié (injecté par get_current_user).

    Returns:
        User: L'utilisateur authentifié avec is_admin=True.

    Raises:
        HTTPException(403): L'utilisateur n'a pas les droits administrateur.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Paramètres de pagination
# ---------------------------------------------------------------------------

class PaginationParams:
    """
    Paramètres de pagination communs, injectables via Depends.

    Attributes:
        page  : Numéro de page (commence à 1).
        limit : Nombre d'éléments par page (max 100).
        offset: Décalage SQL calculé automatiquement.

    Example::

        @router.get("/sites")
        async def list_sites(pagination: PaginationParams = Depends()):
            # pagination.offset, pagination.limit
    """

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Numéro de page (commence à 1)."),
        limit: int = Query(default=20, ge=1, le=100, description="Éléments par page (max 100)."),
    ):
        self.page = page
        self.limit = limit
        self.offset = (page - 1) * limit
