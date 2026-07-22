"""
Modèle SQLAlchemy – Site.

Représente un site web client géré par l'ESN et suivi via GA4.
Chaque site possède une propriété GA4 associée et un statut de santé.
"""

import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class SiteStatus(str, enum.Enum):
    """
    Statuts possibles d'un site, conformes aux mockups :
    - healthy  : site actif, données GA4 synchronisées (• Sain)
    - warning  : données partielles ou anomalie détectée (• À réviser / Attention)
    - offline  : site inaccessible ou désactivé (• Hors ligne)
    - error    : erreur de synchronisation GA4 (• Erreur)
    """
    healthy = "healthy"
    warning = "warning"
    offline = "offline"
    error   = "error"


class Site(Base):
    """
    Table `sites` – Informations d'un site client.

    Columns:
        id                 : Clé primaire auto-incrémentée.
        name               : Nom d'affichage du site (ex. "Certiskool.fr").
        url                : URL publique du site (ex. "https://certiskool.fr").
        ga4_property_id    : Identifiant de propriété GA4 (ex. "258493021").
        status             : Statut de santé courant (SiteStatus enum).
        health_score       : Score de santé en pourcentage (0–100).
        is_active          : Indique si le site est activement suivi.
        last_synced_at     : Horodatage de la dernière synchronisation GA4.
        created_at         : Horodatage de création de l'enregistrement.
        updated_at         : Horodatage de la dernière modification.

    Relationships:
        metrics_snapshots  : Historique journalier des métriques (1→N).
        page_metrics       : Top pages associées (1→N).
    """

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)

    # Identifiant numérique GA4 (ex. "258493021") – stocké en string
    # car GA4 le retourne parfois avec le préfixe "properties/"
    ga4_property_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    status: Mapped[SiteStatus] = mapped_column(
        Enum(SiteStatus, name="site_status"),
        nullable=False,
        default=SiteStatus.healthy,
        server_default=SiteStatus.healthy.value,
    )

    # Score de santé calculé par le service d'agrégation (0–100)
    health_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- Relations ---
    metrics_snapshots: Mapped[list["MetricsSnapshot"]] = relationship(  # noqa: F821
        "MetricsSnapshot", back_populates="site", cascade="all, delete-orphan"
    )
    page_metrics: Mapped[list["PageMetrics"]] = relationship(  # noqa: F821
        "PageMetrics", back_populates="site", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Site id={self.id} name={self.name!r} status={self.status}>"
