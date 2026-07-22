"""
Client Google Analytics 4 (GA4 Data API).

Encapsule les appels à `google-analytics-data` SDK.
Chaque instance est liée à une propriété GA4 (un site).

Documentation GA4 Data API :
https://developers.google.com/analytics/devguides/reporting/data/v1
"""

import logging
from typing import Any

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunReportResponse,
    RunRealtimeReportRequest,
)
from google.oauth2 import service_account

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes – noms de métriques / dimensions GA4
# ---------------------------------------------------------------------------

# Métriques utilisées dans l'application
GA4_METRICS = {
    "sessions": "sessions",
    "users": "activeUsers",
    "new_users": "newUsers",
    "page_views": "screenPageViews",
    "bounce_rate": "bounceRate",
    "avg_session_duration": "averageSessionDuration",
}

# Dimensions utilisées
GA4_DIMENSIONS = {
    "date": "date",
    "page_path": "pagePath",
    "session_source": "sessionDefaultChannelGroup",
}

# Groupes de canaux GA4 → clés internes
CHANNEL_MAP = {
    "Organic Search": "organic",
    "Direct": "direct",
    "Organic Social": "social",
    "Referral": "referral",
    "Paid Search": "organic",   # regroupé avec organic pour simplifier
    "Email": "referral",
    "Unassigned": "direct",
}


# ---------------------------------------------------------------------------
# Client GA4
# ---------------------------------------------------------------------------

class GA4Client:
    """
    Client d'appel à l'API Data GA4.

    Utilise un compte de service Google pour l'authentification.
    Une instance par propriété GA4 (un site).

    Args:
        property_id: Identifiant numérique de la propriété GA4
                     (ex. "258493021" ou "properties/258493021").
        credentials_path: Chemin vers le fichier JSON du compte de service.
                          Défaut : valeur de ``settings.GA4_CREDENTIALS_PATH``.

    Example::

        client = GA4Client(property_id="258493021")
        traffic = await client.get_traffic_series("2024-01-01", "2024-01-31")
    """

    def __init__(
        self,
        property_id: str,
        credentials_info: dict | None = None,
        credentials_path: str | None = None,
    ) -> None:
        # Normalise l'ID : accepte "258493021" ou "properties/258493021"
        if not property_id.startswith("properties/"):
            self.property_id = f"properties/{property_id}"
        else:
            self.property_id = property_id

        if credentials_info:
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        else:
            creds_path = credentials_path or settings.GA4_CREDENTIALS_PATH
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        self._client = BetaAnalyticsDataClient(credentials=credentials)

    @classmethod
    async def create(cls, property_id: str, db: Any) -> "GA4Client":
        """
        Instancie le client en tentant d'abord de charger la clé depuis la base de données.
        S'il n'y a pas de clé en base, retombe sur le fichier de configuration par défaut.
        """
        from sqlalchemy import select
        from app.models.system_setting import SystemSetting
        from app.core.crypto import decrypt_value
        import json

        result = await db.execute(select(SystemSetting).where(SystemSetting.key == "google_credentials"))
        setting = result.scalar_one_or_none()
        
        credentials_info = None
        if setting and setting.value:
            try:
                decrypted = decrypt_value(setting.value)
                credentials_info = json.loads(decrypted)
            except Exception as e:
                logger.error(f"Impossible de décoder les credentials GA4 depuis la BDD : {e}")

        return cls(property_id=property_id, credentials_info=credentials_info)

    # -----------------------------------------------------------------------
    # Méthode générique – run_report
    # -----------------------------------------------------------------------

    def run_report(
        self,
        dimensions: list[str],
        metrics: list[str],
        start_date: str,
        end_date: str,
    ) -> RunReportResponse:
        """
        Lance une requête brute vers l'API GA4 Data.

        Args:
            dimensions: Liste de noms de dimensions GA4 (ex. ["date", "pagePath"]).
            metrics:    Liste de noms de métriques GA4 (ex. ["sessions", "bounceRate"]).
            start_date: Date de début au format "YYYY-MM-DD" ou "NdaysAgo" (ex. "30daysAgo").
            end_date:   Date de fin (ex. "today" ou "2024-01-31").

        Returns:
            RunReportResponse: Réponse brute de l'API GA4.

        Raises:
            google.api_core.exceptions.GoogleAPIError: En cas d'erreur API.
        """
        request = RunReportRequest(
            property=self.property_id,
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        logger.debug(
            "GA4 run_report | property=%s | %s → %s | dims=%s | metrics=%s",
            self.property_id, start_date, end_date, dimensions, metrics,
        )
        return self._client.run_report(request)

    # -----------------------------------------------------------------------
    # Série temporelle du trafic
    # -----------------------------------------------------------------------

    def get_traffic_series(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """
        Retourne les sessions journalières entre deux dates.

        Utilisé pour alimenter le graphique 'Évolution du trafic' (screen_1).

        Args:
            start_date: Ex. "30daysAgo" ou "2024-01-01".
            end_date:   Ex. "today" ou "2024-01-31".

        Returns:
            Liste de dicts : [{"date": "2024-01-01", "sessions": 1250}, ...]
        """
        response = self.run_report(
            dimensions=["date"],
            metrics=["sessions"],
            start_date=start_date,
            end_date=end_date,
        )
        result = []
        for row in response.rows:
            result.append({
                "date": _parse_ga4_date(row.dimension_values[0].value),
                "sessions": int(row.metric_values[0].value),
            })
        return sorted(result, key=lambda x: x["date"])

    # -----------------------------------------------------------------------
    # KPIs agrégés sur une période
    # -----------------------------------------------------------------------

    def get_period_kpis(
        self, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        Retourne les KPIs agrégés sur une période (sans dimension de date).

        Utilisé pour les 3 cards KPI du haut (screen_1) :
        sessions totales, taux de rebond, durée session.

        Returns:
            Dict avec les clés : sessions, users, new_users, page_views,
            bounce_rate (float 0–1), avg_session_duration (secondes).
        """
        response = self.run_report(
            dimensions=[],
            metrics=[
                "sessions", "activeUsers", "newUsers",
                "screenPageViews", "bounceRate", "averageSessionDuration",
            ],
            start_date=start_date,
            end_date=end_date,
        )
        if not response.rows:
            return _empty_kpis()

        row = response.rows[0]
        return {
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "new_users": int(row.metric_values[2].value),
            "page_views": int(row.metric_values[3].value),
            "bounce_rate": float(row.metric_values[4].value),
            "avg_session_duration": float(row.metric_values[5].value),
        }

    # -----------------------------------------------------------------------
    # Top pages
    # -----------------------------------------------------------------------

    def get_top_pages(
        self, start_date: str, end_date: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Retourne les pages les plus visitées sur la période.

        Utilisé pour le widget 'Pages les plus visitées' (screen_1).

        Args:
            limit: Nombre maximum de pages à retourner (défaut 10).

        Returns:
            Liste triée par vues décroissantes :
            [{"path": "/accueil", "page_views": 15240, "traffic_pct": 36.0}, ...]
        """
        response = self.run_report(
            dimensions=["pagePath"],
            metrics=["screenPageViews"],
            start_date=start_date,
            end_date=end_date,
        )
        rows = sorted(
            response.rows,
            key=lambda r: int(r.metric_values[0].value),
            reverse=True,
        )[:limit]

        total_views = sum(int(r.metric_values[0].value) for r in response.rows) or 1
        result = []
        for rank, row in enumerate(rows, start=1):
            views = int(row.metric_values[0].value)
            result.append({
                "rank": rank,
                "path": row.dimension_values[0].value,
                "page_views": views,
                "traffic_pct": round((views / total_views) * 100, 1),
            })
        return result

    # -----------------------------------------------------------------------
    # Sources d'acquisition
    # -----------------------------------------------------------------------

    def get_acquisition_sources(
        self, start_date: str, end_date: str
    ) -> dict[str, float]:
        """
        Retourne la répartition des sources d'acquisition en pourcentage.

        Utilisé pour le camembert 'Sources d'acquisition' (screen_1).

        Returns:
            Dict : {"organic": 45.0, "direct": 25.0, "social": 18.0, "referral": 12.0}
        """
        response = self.run_report(
            dimensions=["sessionDefaultChannelGroup"],
            metrics=["sessions"],
            start_date=start_date,
            end_date=end_date,
        )
        totals: dict[str, int] = {"organic": 0, "direct": 0, "social": 0, "referral": 0}
        grand_total = 0

        for row in response.rows:
            channel = row.dimension_values[0].value
            sessions = int(row.metric_values[0].value)
            key = CHANNEL_MAP.get(channel, "referral")
            totals[key] += sessions
            grand_total += sessions

        if grand_total == 0:
            return {"organic": 0.0, "direct": 0.0, "social": 0.0, "referral": 0.0}

        return {k: round((v / grand_total) * 100, 1) for k, v in totals.items()}

    # -----------------------------------------------------------------------
    # Temps réel
    # -----------------------------------------------------------------------

    def get_realtime_users(self) -> int:
        """
        Retourne le nombre d'utilisateurs actifs en ce moment (temps réel).

        Utilisé pour l'onglet 'Real-time' dans la navigation.

        Returns:
            Nombre d'utilisateurs actifs dans les 30 dernières minutes.
        """
        request = RunRealtimeReportRequest(
            property=self.property_id,
            metrics=[Metric(name="activeUsers")],
        )
        response = self._client.run_realtime_report(request)
        if not response.rows:
            return 0
        return int(response.rows[0].metric_values[0].value)

    # -----------------------------------------------------------------------
    # Test de connexion
    # -----------------------------------------------------------------------

    def test_connection(self) -> bool:
        """
        Vérifie que la connexion à l'API GA4 est opérationnelle.

        Utilisé par le bouton 'Tester la connexion' (screen_2 – Paramètres).

        Returns:
            True si la connexion réussit, False sinon.
        """
        try:
            self.run_report(
                dimensions=[],
                metrics=["sessions"],
                start_date="yesterday",
                end_date="today",
            )
            return True
        except Exception as exc:
            logger.warning("GA4 connection test failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _parse_ga4_date(raw: str) -> str:
    """Convertit le format GA4 '20240101' → '2024-01-01'."""
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"


def _empty_kpis() -> dict[str, Any]:
    """Retourne un dict de KPIs vides (site sans données)."""
    return {
        "sessions": 0,
        "users": 0,
        "new_users": 0,
        "page_views": 0,
        "bounce_rate": 0.0,
        "avg_session_duration": 0.0,
    }
