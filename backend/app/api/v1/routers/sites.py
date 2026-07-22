"""
Router – Sites.

GET    /api/v1/sites/            → liste des sites (screen_3)
GET    /api/v1/sites/{site_id}   → détail d'un site (screen_1)
POST   /api/v1/sites/            → ajouter un site (screen_2)
PATCH  /api/v1/sites/{site_id}   → modifier un site (screen_2)
DELETE /api/v1/sites/{site_id}   → supprimer un site
GET    /api/v1/sites/{site_id}/realtime → utilisateurs temps réel
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_admin,
    get_current_user,
    get_db,
)
from app.models.site import Site, SiteStatus
from app.models.user import User
from app.schemas.metrics import SiteDetailMetrics
from app.schemas.site import SiteCreate, SiteSchema, SiteUpdate, SiteDashboardCard
from app.services.aggregation import AggregationService
from app.services.ga4_client import GA4Client

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_site_or_404(site_id: int, db: AsyncSession) -> Site:
    """Charge un site par son ID ou lève une 404."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site avec l'ID {site_id} introuvable.",
        )
    return site


# ---------------------------------------------------------------------------
# GET /api/v1/sites/ – liste des sites (screen_3)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[SiteSchema],
    summary="Liste des sites gérés",
    description=(
        "Retourne la liste paginée de tous les sites avec leurs métriques synthétiques "
        "(statut, visites 30j, taux de rebond, durée session). Correspond au screen_3."
    ),
)
async def list_sites(
    period: int = Query(default=30, description="Période en jours."),
    status_filter: SiteStatus | None = Query(
        default=None,
        alias="status",
        description="Filtrer par statut (healthy, warning, offline, error).",
    ),
    search: str | None = Query(
        default=None,
        description="Recherche sur le nom ou l'URL du site.",
    ),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SiteSchema]:
    """
    Tableau 'Sites Gérés' (screen_3).

    Colonnes retournées : site web, statut, visites totales (30j),
    taux de rebond, session moyenne.
    """
    query = select(Site)

    if status_filter:
        query = query.where(Site.status == status_filter)
    if search:
        query = query.where(
            Site.name.ilike(f"%{search}%") | Site.url.ilike(f"%{search}%")
        )

    query = query.offset(pagination.offset).limit(pagination.limit)
    result = await db.execute(query)
    sites = result.scalars().all()

    # Enrichissement avec les métriques GA4
    service = AggregationService(db)
    metrics_list = await service.get_sites_list_metrics(list(sites), period_days=period)
    metrics_map = {m.site_id: m for m in metrics_list}

    response: list[SiteSchema] = []
    for site in sites:
        m = metrics_map.get(site.id)
        response.append(
            SiteSchema(
                id=site.id,
                name=site.name,
                url=site.url,
                ga4_property_id=site.ga4_property_id,
                status=site.status,
                health_score=site.health_score,
                is_active=site.is_active,
                last_synced_at=site.last_synced_at,
                created_at=site.created_at,
                total_visits=m.total_visits if m else None,
                bounce_rate_pct=m.bounce_rate_pct if m else None,
                avg_session_duration_seconds=m.avg_session_duration_seconds if m else None,
            )
        )
    return response


# ---------------------------------------------------------------------------
# GET /api/v1/sites/overview – Vue d'ensemble des sites (compatibilité)
# ---------------------------------------------------------------------------

@router.get(
    "/overview",
    response_model=list[SiteDashboardCard],
    summary="Cards de tableau de bord par site",
    description="Retourne une card par site pour le dashboard global. Utilisé par le frontend.",
)
async def get_sites_overview_compat(
    period: int = Query(default=30),
    sort_by: Literal["trafic", "tendance", "sante"] = Query(default="trafic"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if period not in (7, 30, 90):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="La période doit être de 7, 30 ou 90 jours.")
    from app.api.v1.routers.overview import get_dashboard_cards
    return await get_dashboard_cards(period=period, sort_by=sort_by, db=db, current_user=current_user)


# ---------------------------------------------------------------------------
# GET /api/v1/sites/{site_id} – détail d'un site (screen_1)
# ---------------------------------------------------------------------------

@router.get(
    "/{site_id}",
    response_model=SiteDetailMetrics,
    summary="Métriques détaillées d'un site",
    description=(
        "Retourne les KPIs, la série temporelle du trafic, le top des pages "
        "et les sources d'acquisition pour un site. Correspond au screen_1."
    ),
)
async def get_site_detail(
    site_id: int,
    period: int = Query(
        default=30,
        description="Période d'analyse : 7, 30 ou 90 jours.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SiteDetailMetrics:
    """
    Page de détail d'un site (screen_1).

    Retourne :
    - 3 cards KPI (visites, tendance, taux de rebond)
    - Graphique 'Évolution du trafic'
    - Widget 'Pages les plus visitées'
    - Camembert 'Sources d'acquisition'
    """
    site = await _get_site_or_404(site_id, db)

    if site.status == SiteStatus.offline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Le site '{site.name}' est hors ligne. Aucune donnée disponible.",
        )

    service = AggregationService(db)
    return await service.get_site_detail(site=site, period_days=period)


# ---------------------------------------------------------------------------
# GET /api/v1/sites/{site_id}/realtime
# ---------------------------------------------------------------------------

@router.get(
    "/{site_id}/realtime",
    summary="Utilisateurs actifs en temps réel",
    description="Retourne le nombre d'utilisateurs actifs sur le site à l'instant T.",
)
async def get_site_realtime(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Données temps réel d'un site (onglet 'Real-time' dans la navigation).

    Returns:
        {"site_id": 1, "active_users": 42}
    """
    site = await _get_site_or_404(site_id, db)
    client = await GA4Client.create(property_id=site.ga4_property_id, db=db)
    active_users = client.get_realtime_users()
    return {"site_id": site_id, "site_name": site.name, "active_users": active_users}


# ---------------------------------------------------------------------------
# POST /api/v1/sites/ – ajouter un site (admin – screen_2)
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=SiteSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un nouveau site",
    description="Crée un site et l'associe à une propriété GA4. Réservé aux admins.",
)
async def create_site(
    payload: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SiteSchema:
    """
    Bouton '+ Ajouter un site' (screen_2 et screen_3).

    Vérifie que la propriété GA4 n'est pas déjà enregistrée
    avant de créer l'entrée en base.
    """
    # Vérification unicité
    existing = await db.execute(
        select(Site).where(
            (Site.ga4_property_id == payload.ga4_property_id)
            | (Site.url == payload.url)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un site avec cette URL ou cet ID GA4 existe déjà.",
        )

    site = Site(
        name=payload.name,
        url=payload.url,
        ga4_property_id=payload.ga4_property_id,
        status=SiteStatus.healthy,
        health_score=100,
    )
    db.add(site)
    await db.flush()   # récupère l'id sans commit définitif

    return SiteSchema(
        id=site.id,
        name=site.name,
        url=site.url,
        ga4_property_id=site.ga4_property_id,
        status=site.status,
        health_score=site.health_score,
        is_active=site.is_active,
        last_synced_at=site.last_synced_at,
        created_at=site.created_at,
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/sites/{site_id} – modifier un site (admin – screen_2)
# ---------------------------------------------------------------------------

@router.patch(
    "/{site_id}",
    response_model=SiteSchema,
    summary="Modifier un site",
    description="Met à jour partiellement les informations d'un site. Réservé aux admins.",
)
async def update_site(
    site_id: int,
    payload: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SiteSchema:
    """
    Bouton 'Modifier' dans le tableau des sites suivis (screen_2).
    """
    site = await _get_site_or_404(site_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)

    return SiteSchema(
        id=site.id,
        name=site.name,
        url=site.url,
        ga4_property_id=site.ga4_property_id,
        status=site.status,
        health_score=site.health_score,
        is_active=site.is_active,
        last_synced_at=site.last_synced_at,
        created_at=site.created_at,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/sites/{site_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un site",
    description="Supprime un site et toutes ses données associées. Réservé aux admins.",
)
async def delete_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> None:
    site = await _get_site_or_404(site_id, db)
    await db.delete(site)
