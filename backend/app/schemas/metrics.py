"""
Schémas Pydantic – Métriques.

Couvre les réponses API pour :
- screen_1 : détail d'un site (KPIs, graphique évolution, top pages, sources)
- screen_4 : tableau de bord multi-sites
- screen_10 : rapports exportables
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sources d'acquisition
# ---------------------------------------------------------------------------

class AcquisitionSources(BaseModel):
    """
    Répartition des sources d'acquisition en pourcentage.
    Correspond au camembert 'Sources d'acquisition' (screen_1).

    Exemple mockup :
        organic=45, direct=25, social=18, referral=12
    """
    organic: float = Field(..., ge=0, le=100, description="% trafic organique.")
    direct: float = Field(..., ge=0, le=100, description="% trafic direct.")
    social: float = Field(..., ge=0, le=100, description="% trafic social.")
    referral: float = Field(..., ge=0, le=100, description="% trafic référent.")


# ---------------------------------------------------------------------------
# Top pages
# ---------------------------------------------------------------------------

class TopPage(BaseModel):
    """
    Une ligne du widget 'Pages les plus visitées' (screen_1).

    Exemple mockup :
        path="/accueil", views=15240, traffic_pct=36.0
    """
    rank: int = Field(..., ge=1, description="Position dans le classement.")
    path: str = Field(..., examples=["/accueil", "/cours-maths"])
    page_views: int = Field(..., ge=0)
    traffic_pct: float = Field(
        ..., ge=0, le=100, description="Part du trafic total en pourcentage."
    )


# ---------------------------------------------------------------------------
# Série temporelle (graphique)
# ---------------------------------------------------------------------------

class TrafficDataPoint(BaseModel):
    """
    Un point de données pour le graphique 'Évolution du trafic' (screen_1).
    """
    date: date
    sessions: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# KPIs détail d'un site – screen_1
# ---------------------------------------------------------------------------

class SiteKPIs(BaseModel):
    """
    KPIs affichés en haut de la page de détail d'un site (screen_1).

    Exemple mockup (Certiskool.fr) :
        total_visits = 42 150
        trend_pct    = +12.5%
        bounce_rate  = 34.2%
    """
    total_visits: int = Field(..., ge=0, description="Sessions totales sur la période.")
    trend_pct: float = Field(..., description="Variation % vs période précédente. Ex. +12.5.")
    bounce_rate_pct: float = Field(..., ge=0, le=100, description="Taux de rebond en %.")


class SiteDetailMetrics(BaseModel):
    """
    Réponse complète pour la page de détail d'un site (screen_1).

    Regroupe tous les widgets visibles dans le mockup :
    1. Bandeau KPIs (visites, tendance, taux de rebond)
    2. Graphique évolution du trafic (série temporelle)
    3. Top pages
    4. Sources d'acquisition
    """
    site_id: int
    site_name: str
    period_days: int = Field(..., description="Durée de la période analysée (7, 30 ou 90 jours).")

    # Bandeau KPIs – 3 cards en haut (screen_1)
    kpis: SiteKPIs

    # Graphique 'Évolution du trafic'
    traffic_series: list[TrafficDataPoint]

    # Widget 'Pages les plus visitées'
    top_pages: list[TopPage]

    # Widget 'Sources d'acquisition'
    acquisition_sources: AcquisitionSources


# ---------------------------------------------------------------------------
# Vue d'ensemble multi-sites – screen_4
# ---------------------------------------------------------------------------

class GlobalMetrics(BaseModel):
    """
    Métriques agrégées sur l'ensemble des sites pour le tableau de bord (screen_4).
    Permet de remplir chaque card de la grille.
    """
    period_days: int = Field(7, description="Période analysée : 7 ou 30 jours.")
    total_sites: int = Field(..., description="Nombre de sites gérés au total.")
    active_sites: int = Field(..., description="Nombre de sites avec statut 'healthy'.")
    total_visits: int = Field(..., description="Visites cumulées sur tous les sites.")
    avg_bounce_rate_pct: float = Field(..., description="Taux de rebond moyen global.")


# ---------------------------------------------------------------------------
# Métriques pour la liste de sites – screen_3
# ---------------------------------------------------------------------------

class SiteListMetrics(BaseModel):
    """
    Métriques agrégées pour une ligne du tableau 'Sites Gérés' (screen_3).

    Colonnes du mockup :
        Visites totales (30j) | Taux de rebond | Session moyenne
    """
    site_id: int
    total_visits: int
    bounce_rate_pct: float
    avg_session_duration_seconds: float

    @property
    def avg_session_duration_formatted(self) -> str:
        """Retourne la durée de session formatée (ex. '2m 14s')."""
        minutes = int(self.avg_session_duration_seconds // 60)
        seconds = int(self.avg_session_duration_seconds % 60)
        return f"{minutes}m {seconds:02d}s"


# ---------------------------------------------------------------------------
# Rapport – screen_10
# ---------------------------------------------------------------------------

class ReportSiteSummary(BaseModel):
    """
    Résumé d'un site dans un rapport (screen_10 – cards de résultats).

    Exemple mockup :
        site_name="Certiskool.fr", total_visits=42150, trend_pct=+12.5
    """
    site_id: int
    site_name: str
    total_visits: int
    trend_pct: float
    is_healthy: bool


class ReportResponse(BaseModel):
    """
    Réponse complète du générateur de rapports (screen_10).

    Contient :
    - La série temporelle de trafic cumulé (graphique de synthèse)
    - Le résumé par site (cards de résultats)
    """
    period_days: Literal[7, 30, 90]
    site_count: int
    global_traffic_series: list[TrafficDataPoint]
    sites_summary: list[ReportSiteSummary]
