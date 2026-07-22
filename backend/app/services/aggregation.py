"""
Service d'agrégation des métriques GA4.

Orchestre les appels au GA4Client, calcule les KPIs métier
et formate les données pour les schémas Pydantic de l'API.

Ce service est la couche entre les routers et le GA4Client :
    Router → AggregationService → GA4Client → API Google
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site, SiteStatus
from app.models.metrics_snapshot import MetricsSnapshot
from app.models.page_metrics import PageMetrics
from app.schemas.metrics import (
    AcquisitionSources,
    GlobalMetrics,
    ReportResponse,
    ReportSiteSummary,
    SiteDetailMetrics,
    SiteKPIs,
    SiteListMetrics,
    TopPage,
    TrafficDataPoint,
)
from app.services.ga4_client import GA4Client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _period_dates(days: int) -> tuple[str, str]:
    """
    Retourne les dates de début/fin pour une période de N jours.

    Returns:
        Tuple (start_date, end_date) au format 'YYYY-MM-DD'.
    """
    end = date.today()
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def compute_trend(current: float, previous: float) -> float:
    """
    Calcule la variation en pourcentage entre deux valeurs.

    Args:
        current:  Valeur sur la période actuelle.
        previous: Valeur sur la période précédente.

    Returns:
        Variation en % arrondie à 1 décimale.
        Retourne 0.0 si previous est 0 (évite la division par zéro).

    Examples:
        >>> compute_trend(1200, 1000)
        20.0
        >>> compute_trend(800, 1000)
        -20.0
        >>> compute_trend(500, 0)
        0.0
    """
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def _compute_health_score(bounce_rate: float, trend_pct: float) -> int:
    """
    Calcule un score de santé (0–100) basé sur le taux de rebond et la tendance.

    Logique métier :
    - Base : 100
    - -20 pts si bounce_rate > 60%
    - -10 pts si bounce_rate entre 50% et 60%
    - -10 pts si trend_pct < -10%
    - -5  pts si trend_pct entre -10% et 0%

    Returns:
        Score entier entre 0 et 100.
    """
    score = 100
    if bounce_rate > 60:
        score -= 20
    elif bounce_rate > 50:
        score -= 10

    if trend_pct < -10:
        score -= 10
    elif trend_pct < 0:
        score -= 5

    return max(0, score)


def _status_from_score(score: int) -> SiteStatus:
    """Dérive le SiteStatus depuis le health_score."""
    if score >= 80:
        return SiteStatus.healthy
    elif score >= 60:
        return SiteStatus.warning
    else:
        return SiteStatus.error


# ---------------------------------------------------------------------------
# Service principal
# ---------------------------------------------------------------------------

class AggregationService:
    """
    Orchestre les appels GA4 et produit les schémas de réponse API.

    Args:
        db: Session SQLAlchemy async (injectée via Depends).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_client(self, ga4_property_id: str) -> GA4Client:
        """Instancie un GA4Client pour la propriété donnée."""
        return await GA4Client.create(property_id=ga4_property_id, db=self.db)

    # -----------------------------------------------------------------------
    # Détail d'un site – screen_1
    # -----------------------------------------------------------------------

    async def get_site_detail(
        self, site: Site, period_days: int = 30
    ) -> SiteDetailMetrics:
        """
        Retourne toutes les métriques pour la page de détail d'un site (screen_1).

        Agrège :
        - KPIs (visites, tendance, taux de rebond)
        - Série temporelle journalière
        - Top pages
        - Sources d'acquisition

        Args:
            site:        Objet Site SQLAlchemy.
            period_days: Durée de la période (7, 30 ou 90 jours).

        Returns:
            SiteDetailMetrics prêt à sérialiser.
        """
        client = await self._get_client(site.ga4_property_id)
        start, end = _period_dates(period_days)
        prev_start, prev_end = _period_dates(period_days * 2)

        # --- KPIs période actuelle ---
        kpis_current = client.get_period_kpis(start, end)

        # --- KPIs période précédente (pour calcul tendance) ---
        kpis_prev = client.get_period_kpis(prev_start, prev_end)

        trend = compute_trend(kpis_current["sessions"], kpis_prev["sessions"])
        bounce_pct = round(kpis_current["bounce_rate"] * 100, 1)

        # --- Série temporelle ---
        raw_series = client.get_traffic_series(start, end)
        traffic_series = [
            TrafficDataPoint(date=row["date"], sessions=row["sessions"])
            for row in raw_series
        ]

        # --- Top pages ---
        raw_pages = client.get_top_pages(start, end, limit=10)
        top_pages = [
            TopPage(
                rank=p["rank"],
                path=p["path"],
                page_views=p["page_views"],
                traffic_pct=p["traffic_pct"],
            )
            for p in raw_pages
        ]

        # --- Sources d'acquisition ---
        sources = client.get_acquisition_sources(start, end)
        acquisition = AcquisitionSources(**sources)

        return SiteDetailMetrics(
            site_id=site.id,
            site_name=site.name,
            period_days=period_days,
            kpis=SiteKPIs(
                total_visits=kpis_current["sessions"],
                trend_pct=trend,
                bounce_rate_pct=bounce_pct,
            ),
            traffic_series=traffic_series,
            top_pages=top_pages,
            acquisition_sources=acquisition,
        )

    # -----------------------------------------------------------------------
    # Métriques liste sites – screen_3
    # -----------------------------------------------------------------------

    async def get_sites_list_metrics(
        self, sites: list[Site], period_days: int = 30
    ) -> list[SiteListMetrics]:
        """
        Retourne les métriques synthétiques pour chaque site (tableau screen_3).

        Colonnes : visites 30j, taux de rebond, durée session moyenne.

        Args:
            sites: Liste de sites à traiter.

        Returns:
            Liste de SiteListMetrics dans le même ordre que `sites`.
        """
        results: list[SiteListMetrics] = []
        start, end = _period_dates(period_days)

        for site in sites:
            if not site.is_active or site.status == SiteStatus.offline:
                results.append(SiteListMetrics(
                    site_id=site.id,
                    total_visits=0,
                    bounce_rate_pct=0.0,
                    avg_session_duration_seconds=0.0,
                ))
                continue

            try:
                client = await self._get_client(site.ga4_property_id)
                kpis = client.get_period_kpis(start, end)
                results.append(SiteListMetrics(
                    site_id=site.id,
                    total_visits=kpis["sessions"],
                    bounce_rate_pct=round(kpis["bounce_rate"] * 100, 1),
                    avg_session_duration_seconds=kpis["avg_session_duration"],
                ))
            except Exception as exc:
                logger.error("Erreur GA4 pour site %s: %s", site.name, exc)
                results.append(SiteListMetrics(
                    site_id=site.id,
                    total_visits=0,
                    bounce_rate_pct=0.0,
                    avg_session_duration_seconds=0.0,
                ))

        return results

    # -----------------------------------------------------------------------
    # Dashboard global – screen_4
    # -----------------------------------------------------------------------

    async def get_global_metrics(
        self, sites: list[Site], period_days: int = 30
    ) -> GlobalMetrics:
        """
        Retourne les KPIs agrégés pour le tableau de bord global (screen_4).

        Args:
            sites:       Liste de tous les sites.
            period_days: Période à analyser (7 ou 30 jours).

        Returns:
            GlobalMetrics avec totaux consolidés.
        """
        start, end = _period_dates(period_days)
        total_sessions = 0
        bounce_rates: list[float] = []
        active_count = 0

        for site in sites:
            if not site.is_active or site.status == SiteStatus.offline:
                continue
            try:
                client = await self._get_client(site.ga4_property_id)
                kpis = client.get_period_kpis(start, end)
                total_sessions += kpis["sessions"]
                if kpis["sessions"] > 0:
                    bounce_rates.append(kpis["bounce_rate"] * 100)
                active_count += 1
            except Exception as exc:
                logger.warning("Impossible de récupérer GA4 pour %s: %s", site.name, exc)

        avg_bounce = round(sum(bounce_rates) / len(bounce_rates), 1) if bounce_rates else 0.0

        return GlobalMetrics(
            period_days=period_days,
            total_sites=len(sites),
            active_sites=active_count,
            total_visits=total_sessions,
            avg_bounce_rate_pct=avg_bounce,
        )

    # -----------------------------------------------------------------------
    # Rapport – screen_10
    # -----------------------------------------------------------------------

    async def generate_report(
        self,
        sites: list[Site],
        period_days: int = 7,
    ) -> ReportResponse:
        """
        Génère un rapport multi-sites (screen_10).

        Retourne :
        - La série temporelle de trafic cumulé sur tous les sites sélectionnés.
        - Un résumé par site (visites + tendance).

        Args:
            sites:       Sous-ensemble de sites à inclure dans le rapport.
            period_days: Période : 7, 30 ou 90 jours.

        Returns:
            ReportResponse prêt à sérialiser ou à exporter en PDF.
        """
        start, end = _period_dates(period_days)
        prev_start, prev_end = _period_dates(period_days * 2)

        # Cumul du trafic journalier sur tous les sites
        cumul: dict[str, int] = {}
        sites_summary: list[ReportSiteSummary] = []

        for site in sites:
            if not site.is_active:
                continue
            try:
                client = await self._get_client(site.ga4_property_id)

                # Série temporelle
                series = client.get_traffic_series(start, end)
                for point in series:
                    cumul[point["date"]] = cumul.get(point["date"], 0) + point["sessions"]

                # KPIs pour le résumé
                kpis_cur = client.get_period_kpis(start, end)
                kpis_pre = client.get_period_kpis(prev_start, prev_end)
                trend = compute_trend(kpis_cur["sessions"], kpis_pre["sessions"])

                sites_summary.append(ReportSiteSummary(
                    site_id=site.id,
                    site_name=site.name,
                    total_visits=kpis_cur["sessions"],
                    trend_pct=trend,
                    is_healthy=(site.status == SiteStatus.healthy),
                ))
            except Exception as exc:
                logger.error("Rapport – erreur GA4 pour %s: %s", site.name, exc)

        global_series = [
            TrafficDataPoint(date=d, sessions=s)
            for d, s in sorted(cumul.items())
        ]

        return ReportResponse(
            period_days=period_days,
            site_count=len(sites_summary),
            global_traffic_series=global_series,
            sites_summary=sites_summary,
        )

    # -----------------------------------------------------------------------
    # Snapshot journalier (appelé par les tâches Celery)
    # -----------------------------------------------------------------------

    async def snapshot_site(self, site: Site) -> None:
        """
        Enregistre un snapshot journalier des métriques GA4 en base.

        Appelé par la tâche Celery ``fetch_all_sites_metrics`` chaque nuit.
        Crée ou met à jour le MetricsSnapshot du jour.

        Args:
            site: Site à snapshoter.
        """
        today = date.today()
        start = today.isoformat()

        client = await self._get_client(site.ga4_property_id)
        kpis = client.get_period_kpis(start, start)
        sources = client.get_acquisition_sources(start, start)

        # Upsert MetricsSnapshot
        result = await self.db.execute(
            select(MetricsSnapshot).where(
                MetricsSnapshot.site_id == site.id,
                MetricsSnapshot.snapshot_date == today,
            )
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            snapshot = MetricsSnapshot(site_id=site.id, snapshot_date=today)
            self.db.add(snapshot)

        snapshot.sessions = kpis["sessions"]
        snapshot.users = kpis["users"]
        snapshot.new_users = kpis["new_users"]
        snapshot.page_views = kpis["page_views"]
        snapshot.bounce_rate = kpis["bounce_rate"]
        snapshot.avg_session_duration = kpis["avg_session_duration"]
        snapshot.traffic_organic = sources["organic"] / 100
        snapshot.traffic_direct = sources["direct"] / 100
        snapshot.traffic_social = sources["social"] / 100
        snapshot.traffic_referral = sources["referral"] / 100

        # Upsert top 10 pages du jour
        raw_pages = client.get_top_pages(start, start, limit=10)
        for p in raw_pages:
            res = await self.db.execute(
                select(PageMetrics).where(
                    PageMetrics.site_id == site.id,
                    PageMetrics.page_date == today,
                    PageMetrics.path == p["path"],
                )
            )
            pm = res.scalar_one_or_none()
            if pm is None:
                pm = PageMetrics(
                    site_id=site.id, page_date=today, path=p["path"]
                )
                self.db.add(pm)
            pm.page_views = p["page_views"]
            pm.traffic_pct = p["traffic_pct"] / 100
            pm.rank = p["rank"]

        # Mise à jour du score de santé du site
        prev_start, _ = _period_dates(60)
        kpis_prev = client.get_period_kpis(prev_start, (today - timedelta(days=30)).isoformat())
        trend = compute_trend(kpis["sessions"], kpis_prev["sessions"])
        score = _compute_health_score(kpis["bounce_rate"] * 100, trend)
        site.health_score = score
        site.status = _status_from_score(score)

        logger.info(
            "Snapshot site '%s' – sessions=%d, score=%d, statut=%s",
            site.name, kpis["sessions"], score, site.status,
        )
