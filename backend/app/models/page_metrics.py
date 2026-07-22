"""
Modèle SQLAlchemy – PageMetrics.

Métriques des pages les plus visitées pour un site à une date donnée.
Alimente le widget "Pages les plus visitées" du mockup screen_1.
"""

from datetime import date, datetime

from sqlalchemy import (
    Integer, Float, Date, DateTime, ForeignKey,
    String, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PageMetrics(Base):
    """
    Table `page_metrics` – Top pages par site et par jour.

    Chaque ligne représente les métriques d'une URL spécifique
    pour un site donné à une date donnée.

    Columns:
        id           : Clé primaire.
        site_id      : FK vers Site.
        page_date    : Date du relevé.
        path         : Chemin de la page (ex. "/accueil", "/cours-maths").
        page_views   : Nombre de vues pour cette page ce jour-là.
        traffic_pct  : Pourcentage du trafic total du site (0.0 – 1.0).
        rank         : Rang de la page (1 = plus visitée) pour ce site/date.
        created_at   : Horodatage d'insertion.

    Conformité mockup (screen_1 – "Pages les plus visitées") :
        PAGE            VUES        % DU TRAFIC
        /accueil        15,240      36%
        /cours-maths     8,420      20%
        /blog/revisions  5,110      12%
    """

    __tablename__ = "page_metrics"
    __table_args__ = (
        # Un seul enregistrement par (site, date, path)
        UniqueConstraint("site_id", "page_date", "path", name="uq_page_site_date_path"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    site_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    page_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Chemin de la page sans le domaine (ex. "/accueil", "/cours-maths")
    path: Mapped[str] = mapped_column(String(1024), nullable=False)

    page_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Proportion du trafic total : 0.36 → 36%
    traffic_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Rang dans le classement pour ce site/date (1 = plus visitée)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Relation inverse ---
    site: Mapped["Site"] = relationship("Site", back_populates="page_metrics")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<PageMetrics site_id={self.site_id} "
            f"date={self.page_date} path={self.path!r} rank={self.rank}>"
        )
