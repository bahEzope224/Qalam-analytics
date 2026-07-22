"""Déclaration de la Base de Données (Base Class) SQLAlchemy.

Ce fichier évite les imports circulaires en déclarant uniquement la classe Base,
sans importer les modèles qui héritent de cette même classe.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Convention de nommage des contraintes pour Alembic
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
