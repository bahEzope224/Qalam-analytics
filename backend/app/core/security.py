"""
Module de sécurité – Authentification JWT & gestion des mots de passe.

Responsabilités :
- Création et vérification des tokens JWT (Access + Refresh)
- Hachage et vérification des mots de passe (bcrypt via passlib)
- Extraction du payload depuis un token Bearer
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# ---------------------------------------------------------------------------
# Contexte de hachage des mots de passe
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Hachage & vérification des mots de passe
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """
    Hache un mot de passe en clair avec bcrypt.

    Args:
        plain_password: Le mot de passe en clair à hacher.

    Returns:
        Le hash bcrypt du mot de passe.

    Example:
        >>> hashed = hash_password("MonMotDePasse123!")
        >>> hashed.startswith("$2b$")
        True
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à son hash bcrypt.

    Args:
        plain_password:   Le mot de passe fourni par l'utilisateur.
        hashed_password:  Le hash stocké en base de données.

    Returns:
        True si le mot de passe correspond, False sinon.

    Example:
        >>> hashed = hash_password("secret")
        >>> verify_password("secret", hashed)
        True
        >>> verify_password("mauvais", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# Création de tokens JWT
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Génère un Access Token JWT signé.

    Le token contient le payload `data` enrichi de :
    - `exp` : timestamp d'expiration (UTC)
    - `iat` : timestamp de création (UTC)
    - `type` : "access"

    Args:
        data:          Données à encoder dans le token (ex. {"sub": "user@esn.fr"}).
        expires_delta: Durée de validité personnalisée. Si None, utilise
                       `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.

    Returns:
        Le token JWT encodé sous forme de chaîne.

    Example:
        >>> token = create_access_token(data={"sub": "user@esn.fr"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Génère un Refresh Token JWT signé avec une durée de vie plus longue.

    Même mécanique que `create_access_token` mais :
    - Durée par défaut : 7 jours
    - Champ `type` : "refresh"

    Le Refresh Token permet d'obtenir un nouvel Access Token sans
    redemander les credentials à l'utilisateur.

    Args:
        data:          Données à encoder (généralement {"sub": email}).
        expires_delta: Durée de validité personnalisée.

    Returns:
        Le Refresh Token JWT encodé.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta is not None else timedelta(days=7))
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Vérification & décodage des tokens JWT
# ---------------------------------------------------------------------------

def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Décode et valide un token JWT.

    Vérifie :
    - La signature (avec SECRET_KEY et ALGORITHM)
    - La date d'expiration (`exp`)
    - Le type du token (`access` ou `refresh`)
    - La présence du sujet (`sub`)

    Args:
        token:         Le token JWT brut (sans le préfixe "Bearer ").
        expected_type: Type attendu du token : "access" (défaut) ou "refresh".

    Returns:
        Le payload décodé sous forme de dictionnaire.

    Raises:
        HTTPException(401): Si le token est invalide, expiré, de mauvais type
                            ou si le sujet est absent.

    Example:
        >>> token = create_access_token({"sub": "user@esn.fr"})
        >>> payload = verify_token(token)
        >>> payload["sub"]
        'user@esn.fr'
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise credentials_exception

    # Vérification du type de token
    token_type: str | None = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Type de token incorrect. Attendu : '{expected_type}', reçu : '{token_type}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Vérification de la présence du sujet
    subject: str | None = payload.get("sub")
    if subject is None:
        raise credentials_exception

    return payload


def extract_token_subject(token: str) -> str:
    """
    Raccourci : décode un Access Token et retourne uniquement le `sub` (email/ID).

    Utile dans les dépendances FastAPI pour obtenir rapidement l'identifiant
    de l'utilisateur courant sans manipuler le payload entier.

    Args:
        token: Le token JWT brut.

    Returns:
        La valeur du champ `sub` (email ou identifiant utilisateur).

    Raises:
        HTTPException(401): Si le token est invalide ou le `sub` absent.

    Example:
        >>> token = create_access_token({"sub": "admin@esn.fr"})
        >>> extract_token_subject(token)
        'admin@esn.fr'
    """
    payload = verify_token(token, expected_type="access")
    return payload["sub"]
