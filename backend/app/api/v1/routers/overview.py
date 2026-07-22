"""
Router – Vue d'ensemble (dashboard global).

GET /api/v1/overview/
GET /api/v1/overview/cards

Correspond au screen_4 : 'Vue d'ensemble des sites'.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models.site import Site, SiteStatus
from app.models.user import User
from app.schemas.metrics import GlobalMetrics, SiteDetailMetrics
from app.schemas.site import SiteDashboardCard
from app.services.aggregation import AggregationService, compute_trend
from app.services.ga4_client import GA4Client
from app.core.config import settings

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /api/v1/overview/ – KPIs globaux
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=GlobalMetrics,
    summary="KPIs globaux de tous les sites",
    description=(
        "Retourne les métriques agrégées sur l'ensemble du portefeuille de sites "
        "(visites cumulées, taux de rebond moyen, nombre de sites actifs). "
        "Période : 7 ou 30 jours."
    ),
)
async def get_overview(
    period: int = Query(
        default=30,
        description="Période d'analyse en jours (7, 30 ou 90).",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GlobalMetrics:
    if period not in (7, 30, 90):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="La période doit être de 7, 30 ou 90 jours.")
    """
    Vue d'ensemble agrégée – tableau de bord global (screen_4).

    Interroge GA4 pour chaque site actif et consolide :
    - Sessions totales
    - Taux de rebond moyen
    - Nombre de sites actifs vs total
    """
    result = await db.execute(select(Site).where(Site.is_active == True))  # noqa: E712
    sites = result.scalars().all()

    service = AggregationService(db)
    return await service.get_global_metrics(sites=list(sites), period_days=period)


# ---------------------------------------------------------------------------
# GET /api/v1/overview/cards – Cards par site (grille screen_4)
# ---------------------------------------------------------------------------

@router.get(
    "/cards",
    response_model=list[SiteDashboardCard],
    summary="Cards de tableau de bord par site",
    description=(
        "Retourne une card par site avec : score de santé, visites totales "
        "et tendance vs période précédente. Filtrable par période (7j / 30j)."
    ),
)
async def get_dashboard_cards(
    period: int = Query(default=30),
    sort_by: Literal["trafic", "tendance", "sante"] = Query(
        default="trafic",
        description="Critère de tri : 'trafic', 'tendance' ou 'sante'.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SiteDashboardCard]:
    if period not in (7, 30, 90):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="La période doit être de 7, 30 ou 90 jours.")
    """
    Grille de cards 'Vue d'ensemble des sites' (screen_4).

    Chaque card affiche :
    - Nom du site + statut (couleur)
    - Score de santé en %
    - Visites totales sur la période
    - Tendance % vs période précédente
    """
    result = await db.execute(select(Site).where(Site.is_active == True))  # noqa: E712
    sites = result.scalars().all()

    from app.services.aggregation import _period_dates
    start, end = _period_dates(period)
    prev_start, prev_end = _period_dates(period * 2)

    cards: list[SiteDashboardCard] = []
    for site in sites:
        if site.status == SiteStatus.offline:
            cards.append(SiteDashboardCard(
                id=site.id,
                name=site.name,
                status=site.status,
                health_score=site.health_score,
                total_visits=0,
                trend_pct=0.0,
            ))
            continue

        try:
            client = await GA4Client.create(property_id=site.ga4_property_id, db=db)
            kpis_cur = client.get_period_kpis(start, end)
            kpis_pre = client.get_period_kpis(prev_start, prev_end)
            trend = compute_trend(kpis_cur["sessions"], kpis_pre["sessions"])

            cards.append(SiteDashboardCard(
                id=site.id,
                name=site.name,
                status=site.status,
                health_score=site.health_score,
                total_visits=kpis_cur["sessions"],
                trend_pct=trend,
            ))
        except Exception:
            cards.append(SiteDashboardCard(
                id=site.id,
                name=site.name,
                status=SiteStatus.error,
                health_score=0,
                total_visits=0,
                trend_pct=0.0,
            ))

    # Tri
    sort_keys = {
        "trafic":   lambda c: c.total_visits,
        "tendance": lambda c: c.trend_pct,
        "sante":    lambda c: c.health_score,
    }
    cards.sort(key=sort_keys[sort_by], reverse=True)
    return cards
