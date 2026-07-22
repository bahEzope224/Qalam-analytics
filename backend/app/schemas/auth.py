"""
Schémas Pydantic – Authentification.

Couvre les tokens JWT et les données utilisateur.
"""

from pydantic import BaseModel, EmailStr, Field


class TokenSchema(BaseModel):
    """
    Réponse retournée après un login réussi.
    Contient l'access token et le refresh token.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload décodé d'un JWT (usage interne)."""
    sub: str = Field(..., description="Email ou identifiant de l'utilisateur.")
    type: str = Field(..., description="Type du token : 'access' ou 'refresh'.")


class LoginRequest(BaseModel):
    """Payload de connexion."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserSchema(BaseModel):
    """Données utilisateur retournées dans les réponses API."""
    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}
