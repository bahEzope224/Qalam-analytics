"""
Modèle SQLAlchemy – User.
Utilisateurs internes de la plateforme Qalam Analytics.
"""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class User(Base):
    """
    Table `users` – Comptes internes de la plateforme.

    Columns:
        id         : Clé primaire.
        email      : Email unique (utilisé comme `sub` dans le JWT).
        full_name  : Nom complet affiché dans l'interface.
        hashed_password : Mot de passe haché bcrypt.
        is_active  : Compte actif (False = désactivé sans suppression).
        is_admin   : Accès aux paramètres et à la gestion des sites.
        created_at : Date de création.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} admin={self.is_admin}>"
