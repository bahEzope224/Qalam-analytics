"""
Tâches Celery d'ingestion GA4.

Ce module contient tous les jobs planifiés qui récupèrent les données
Google Analytics 4 et les persisent en base de données PostgreSQL.

Architecture d'exécution :
    Celery Beat (scheduler)
        └─→ fetch_all_sites_metrics()      [02h00 – quotidien]
                └─→ fetch_site_metrics()   [par site, en parallèle]
        └─→ update_all_health_scores()     [toutes les 6h]
        └─→ retry_failed_sites()           [08h00 – rattrapage]

Les tâches Celery sont synchrones. L'accès SQLAlchemy async est encapsulé
via ``asyncio.run()`` pour s'exécuter dans le thread du worker Celery.

Commandes utiles :
    # Déclencher manuellement depuis Python / shell :
    from app.tasks.ingestion import fetch_all_sites_metrics
    fetch_all_sites_metrics.delay()

    # Déclencher pour un site spécifique :
    fetch_site_metrics.delay(site_id=1)
"""

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any

from celery import Task, group
from sqlalchemy import select

from app.models.site import Site, SiteStatus
from app.models.metrics_snapshot import MetricsSnapshot
from app.worker import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper : exécuteur async → sync pour Celery
# ---------------------------------------------------------------------------

def _run_async(coro) -> Any:
    """
    Exécute une coroutine dans une nouvelle boucle asyncio.

    Celery travaille dans un environnement synchrone ; cette fonction
    permet d'y appeler des fonctions async (SQLAlchemy, services).

    Args:
        coro: Coroutine à exécuter.

    Returns:
        Le résultat de la coroutine.
    """
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Tâche de base avec retry automatique
# ---------------------------------------------------------------------------

class BaseIngestionTask(Task):
    """
    Classe de base pour toutes les tâches d'ingestion.

    Ajoute :
    - Logging structuré au démarrage et à la fin
    - Retry automatique sur exception (max 3 tentatives, délai exponentiel)
    """
    abstract = True
    max_retries = 3
    default_retry_delay = 60       # secondes

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "❌ Tâche %s [%s] échouée : %s",
            self.name, task_id, exc,
            exc_info=einfo,
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(
            "🔄 Tâche %s [%s] – retry n°%d : %s",
            self.name, task_id, self.request.retries, exc,
        )

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("✅ Tâche %s [%s] terminée.", self.name, task_id)


# ---------------------------------------------------------------------------
# fetch_all_sites_metrics – Tâche maître nocturne
# ---------------------------------------------------------------------------

@celery_app.task(
    base=BaseIngestionTask,
    name="app.tasks.ingestion.fetch_all_sites_metrics",
    queue="ingestion",
    bind=True,
)
def fetch_all_sites_metrics(self: BaseIngestionTask) -> dict[str, Any]:
    """
    Tâche maître d'ingestion nocturne (02h00 chaque nuit).

    Récupère la liste de tous les sites actifs depuis la DB,
    puis dispatche une tâche ``fetch_site_metrics`` par site
    en parallèle via un groupe Celery.

    Returns:
        Dictionnaire de bilan : total de sites traités, succès, erreurs.

    Schedule (Celery Beat) :
        "fetch-all-sites-nightly" → crontab(hour=2, minute=0)
    """
    logger.info("🌙 Démarrage de l'ingestion nocturne – %s", date.today().isoformat())

    async def _load_sites() -> list[dict]:
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Site).where(Site.is_active == True)  # noqa: E712
            )
            sites = result.scalars().all()
            # Sérialisation avant fermeture de la session
            return [
                {"id": s.id, "name": s.name, "ga4_property_id": s.ga4_property_id}
                for s in sites
            ]

    sites_data = _run_async(_load_sites())

    if not sites_data:
        logger.warning("Aucun site actif trouvé. Ingestion ignorée.")
        return {"total": 0, "dispatched": 0}

    logger.info("📋 %d site(s) à traiter.", len(sites_data))

    # Dispatch des tâches par site en parallèle
    job_group = group(
        fetch_site_metrics.s(site["id"]) for site in sites_data
    )
    result = job_group.apply_async()

    return {
        "total": len(sites_data),
        "dispatched": len(sites_data),
        "group_id": result.id if result else None,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# fetch_site_metrics – Tâche par site
# ---------------------------------------------------------------------------

@celery_app.task(
    base=BaseIngestionTask,
    name="app.tasks.ingestion.fetch_site_metrics",
    queue="ingestion",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def fetch_site_metrics(self: BaseIngestionTask, site_id: int) -> dict[str, Any]:
    """
    Récupère et stocke les métriques GA4 pour un site donné.

    Processus :
    1. Charge le site depuis la DB
    2. Appelle GA4Client pour récupérer les KPIs du jour
    3. Upsert du MetricsSnapshot
    4. Upsert du top 10 PageMetrics
    5. Recalcule health_score et status du site
    6. Met à jour last_synced_at

    Args:
        site_id: Identifiant du site à synchroniser.

    Returns:
        Dictionnaire de résultat : site_name, sessions, health_score, status.

    Raises:
        Retry automatique (max 3) si une exception survient.
    """
    logger.info("📥 Ingestion site ID=%d", site_id)

    async def _do_snapshot(site_id: int) -> dict[str, Any]:
        from app.db.session import AsyncSessionLocal
        from app.services.aggregation import AggregationService

        async with AsyncSessionLocal() as db:
            # Charger le site
            result = await db.execute(select(Site).where(Site.id == site_id))
            site: Site | None = result.scalar_one_or_none()

            if site is None:
                logger.error("Site ID=%d introuvable. Tâche abandonnée.", site_id)
                return {"site_id": site_id, "error": "site_not_found"}

            if not site.is_active:
                logger.info("Site '%s' inactif – skip.", site.name)
                return {"site_id": site_id, "skipped": True}

            # Snapshot via le service d'agrégation
            service = AggregationService(db)
            await service.snapshot_site(site)

            # Mise à jour last_synced_at
            site.last_synced_at = datetime.now(timezone.utc)
            await db.commit()

            return {
                "site_id": site.id,
                "site_name": site.name,
                "health_score": site.health_score,
                "status": site.status.value,
                "synced_at": site.last_synced_at.isoformat(),
            }

    try:
        return _run_async(_do_snapshot(site_id))
    except Exception as exc:
        logger.error("Erreur ingestion site ID=%d : %s", site_id, exc)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)


# ---------------------------------------------------------------------------
# update_all_health_scores – Recalcul des scores (sans appel GA4)
# ---------------------------------------------------------------------------

@celery_app.task(
    base=BaseIngestionTask,
    name="app.tasks.ingestion.update_all_health_scores",
    queue="default",
)
def update_all_health_scores() -> dict[str, Any]:
    """
    Recalcule le health_score et le status de chaque site depuis les snapshots DB.

    Contrairement à ``fetch_site_metrics``, cette tâche n'appelle pas l'API GA4.
    Elle lit les MetricsSnapshot existants et recalcule les scores.

    Planifiée toutes les 6h pour refléter les tendances récentes.

    Returns:
        Bilan : nombre de sites mis à jour.
    """
    logger.info("🔄 Recalcul des scores de santé – %s", datetime.now(timezone.utc))

    from app.services.aggregation import _compute_health_score, _status_from_score, compute_trend

    async def _recalculate() -> dict[str, Any]:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import func as sqlfunc

        updated = 0
        errors = 0

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Site).where(Site.is_active == True)  # noqa: E712
            )
            sites = result.scalars().all()

            for site in sites:
                try:
                    today = date.today()

                    # Sessions des 30 derniers jours
                    res_cur = await db.execute(
                        select(sqlfunc.sum(MetricsSnapshot.sessions)).where(
                            MetricsSnapshot.site_id == site.id,
                            MetricsSnapshot.snapshot_date >= date.fromordinal(
                                today.toordinal() - 30
                            ),
                        )
                    )
                    sessions_cur = res_cur.scalar() or 0

                    # Sessions des 30 jours précédents (j-60 → j-30)
                    res_pre = await db.execute(
                        select(sqlfunc.sum(MetricsSnapshot.sessions)).where(
                            MetricsSnapshot.site_id == site.id,
                            MetricsSnapshot.snapshot_date >= date.fromordinal(
                                today.toordinal() - 60
                            ),
                            MetricsSnapshot.snapshot_date < date.fromordinal(
                                today.toordinal() - 30
                            ),
                        )
                    )
                    sessions_pre = res_pre.scalar() or 0

                    # Taux de rebond moyen (30 derniers jours)
                    res_bounce = await db.execute(
                        select(sqlfunc.avg(MetricsSnapshot.bounce_rate)).where(
                            MetricsSnapshot.site_id == site.id,
                            MetricsSnapshot.snapshot_date >= date.fromordinal(
                                today.toordinal() - 30
                            ),
                        )
                    )
                    avg_bounce = (res_bounce.scalar() or 0.0) * 100  # → pourcentage

                    trend = compute_trend(sessions_cur, sessions_pre)
                    score = _compute_health_score(avg_bounce, trend)
                    new_status = _status_from_score(score)

                    site.health_score = score
                    site.status = new_status
                    updated += 1

                    logger.debug(
                        "Site '%s' → score=%d, status=%s",
                        site.name, score, new_status,
                    )

                except Exception as exc:
                    logger.error("Erreur recalcul site '%s': %s", site.name, exc)
                    errors += 1

            await db.commit()

        return {"updated": updated, "errors": errors}

    return _run_async(_recalculate())


# ---------------------------------------------------------------------------
# retry_failed_sites – Rattrapage du matin (08h00)
# ---------------------------------------------------------------------------

@celery_app.task(
    base=BaseIngestionTask,
    name="app.tasks.ingestion.retry_failed_sites",
    queue="ingestion",
)
def retry_failed_sites() -> dict[str, Any]:
    """
    Rattrapage matinal (08h00) pour les sites en erreur.

    Identifie les sites dont le statut est ``error`` ou dont
    la dernière synchronisation date de plus de 20h,
    et lance une tâche ``fetch_site_metrics`` pour chacun.

    Returns:
        Nombre de sites dont la resynchronisation a été déclenchée.
    """
    logger.info("☀️  Rattrapage matinal des sites en erreur")

    async def _find_failed_sites() -> list[int]:
        from app.db.session import AsyncSessionLocal
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) - timedelta(hours=20)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Site.id).where(
                    Site.is_active == True,  # noqa: E712
                    (Site.status == SiteStatus.error)
                    | (Site.last_synced_at == None)   # noqa: E711
                    | (Site.last_synced_at < threshold),
                )
            )
            return [row[0] for row in result.fetchall()]

    failed_ids = _run_async(_find_failed_sites())

    if not failed_ids:
        logger.info("Aucun site en erreur à rattraper. ✅")
        return {"retried": 0}

    logger.info("🔁 Rattrapage de %d site(s) en erreur.", len(failed_ids))

    job_group = group(fetch_site_metrics.s(site_id) for site_id in failed_ids)
    job_group.apply_async()

    return {
        "retried": len(failed_ids),
        "site_ids": failed_ids,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# cleanup_old_snapshots – Nettoyage (hebdomadaire)
# ---------------------------------------------------------------------------

@celery_app.task(
    name="app.tasks.ingestion.cleanup_old_snapshots",
    queue="default",
)
def cleanup_old_snapshots(retention_days: int = 365) -> dict[str, Any]:
    """
    Supprime les snapshots plus anciens que `retention_days` jours.

    À déclencher manuellement ou à ajouter au beat_schedule.
    Réduit la taille de la table ``metrics_snapshots`` au fil du temps.

    Args:
        retention_days: Nombre de jours de rétention (défaut : 365).

    Returns:
        Nombre de lignes supprimées.
    """
    logger.info("🧹 Nettoyage des snapshots > %d jours", retention_days)

    from datetime import timedelta

    async def _cleanup() -> dict[str, Any]:
        from app.db.session import AsyncSessionLocal
        from sqlalchemy import delete as sa_delete

        cutoff = date.today() - timedelta(days=retention_days)
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                sa_delete(MetricsSnapshot).where(
                    MetricsSnapshot.snapshot_date < cutoff
                )
            )
            await db.commit()
            deleted = res.rowcount
            logger.info("🧹 %d snapshot(s) supprimé(s) (avant le %s).", deleted, cutoff)
            return {"deleted": deleted, "cutoff_date": cutoff.isoformat()}

    return _run_async(_cleanup())
