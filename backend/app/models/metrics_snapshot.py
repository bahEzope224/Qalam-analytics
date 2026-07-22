"""
Modèle SQLAlchemy – MetricsSnapshot.

Snapshot journalier des métriques GA4 pour un site.
Chaque ligne représente les données agrégées d'un site pour une journée donnée.
Alimente les graphiques d'évolution du trafic et les KPIs des mockups.
"""

from datetime import date, datetime

from sqlalchemy import (
    Integer, Float, Date, DateTime, ForeignKey,
    func, UniqueConstraint, String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class MetricsSnapshot(Base):
    """
    Table `metrics_snapshots` – Métriques journalières GA4 par site.

    Chaque enregistrement = (site, date) unique.
    Utilisé pour :
    - Les graphiques d'évolution du trafic (screen_1 : "Évolution du trafic")
    - Les KPIs du tableau de bord (screen_4 : visites, tendance)
    - La liste des sites (screen_3 : visites 30j, taux de rebond, durée session)
    - Les rapports exportables (screen_10)

    Columns:
        id                   : Clé primaire.
        site_id              : FK vers Site.
        snapshot_date        : Date du snapshot (un seul snapshot par site/jour).
        sessions             : Nombre de sessions GA4.
        users                : Nombre d'utilisateurs actifs GA4.
        new_users            : Nouveaux utilisateurs.
        page_views           : Pages vues totales.
        bounce_rate          : Taux de rebond (0.0 – 1.0).
        avg_session_duration : Durée moyenne de session en secondes.
        traffic_organic      : % du trafic organique (0.0 – 1.0).
        traffic_direct       : % du trafic direct.
        traffic_social       : % du trafic social.
        traffic_referral     : % du trafic référent.
        created_at           : Horodatage d'insertion.
    """

    __tablename__ = "metrics_snapshots"
    __table_args__ = (
        # Un seul snapshot par site et par jour
        UniqueConstraint("site_id", "snapshot_date", name="uq_metrics_site_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    site_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # --- Métriques de trafic ---
    sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Métriques d'engagement ---
    # bounce_rate : 0.0 → 0%, 1.0 → 100% (GA4 retourne un float entre 0 et 1)
    bounce_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # avg_session_duration en secondes (ex. 134.0 = 2m 14s)
    avg_session_duration: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # --- Sources d'acquisition (proportions, somme ≈ 1.0) ---
    # Correspondent aux données du camembert "Sources d'acquisition" (screen_1)
    traffic_organic: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traffic_direct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traffic_social: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traffic_referral: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Relation inverse ---
    site: Mapped["Site"] = relationship("Site", back_populates="metrics_snapshots")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<MetricsSnapshot site_id={self.site_id} "
            f"date={self.snapshot_date} sessions={self.sessions}>"
        )
