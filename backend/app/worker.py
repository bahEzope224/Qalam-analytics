"""
Configuration et instanciation de l'application Celery.

Ce module est le point d'entrée du worker Celery.
Il configure le broker (Redis), le backend de résultats,
les schedules périodiques (beat) et les queues de tâches.

Démarrage du worker :
    celery -A app.worker worker --loglevel=info

Démarrage du scheduler (beat) :
    celery -A app.worker beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

Ou combiné (développement uniquement) :
    celery -A app.worker worker --beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# ---------------------------------------------------------------------------
# Instanciation
# ---------------------------------------------------------------------------

celery_app = Celery(
    "qalam_analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ingestion",
    ],
)

# ---------------------------------------------------------------------------
# Configuration générale
# ---------------------------------------------------------------------------

celery_app.conf.update(
    # Sérialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="Europe/Paris",
    enable_utc=True,

    # Résultats
    result_expires=86400,           # 24h – durée de conservation des résultats
    task_ignore_result=False,

    # Fiabilité
    task_acks_late=True,            # acquittement après exécution (évite la perte)
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,   # un seul message à la fois (tâches lourdes)

    # Retry par défaut
    task_max_retries=3,
    task_default_retry_delay=60,    # 60 secondes entre les retries

    # Queues
    task_default_queue="default",
    task_queues={
        "default":  {"exchange": "default",  "routing_key": "default"},
        "ingestion": {"exchange": "ingestion", "routing_key": "ingestion"},
        "reports":   {"exchange": "reports",   "routing_key": "reports"},
    },
)

# ---------------------------------------------------------------------------
# Schedules périodiques (Celery Beat)
# ---------------------------------------------------------------------------

celery_app.conf.beat_schedule = {
    # -----------------------------------------------------------------------
    # Ingestion nocturne – tous les jours à 02h00 (Paris)
    # Récupère et stocke les métriques GA4 de TOUS les sites.
    # -----------------------------------------------------------------------
    "fetch-all-sites-nightly": {
        "task": "app.tasks.ingestion.fetch_all_sites_metrics",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "ingestion"},
    },

    # -----------------------------------------------------------------------
    # Mise à jour des scores de santé – toutes les 6h
    # Recalcule status + health_score sans appeler GA4 (depuis la DB).
    # -----------------------------------------------------------------------
    "update-health-scores-every-6h": {
        "task": "app.tasks.ingestion.update_all_health_scores",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "default"},
    },

    # -----------------------------------------------------------------------
    # Sync rapide quotidienne – 08h00 (données de la veille)
    # Complète la sync nocturne si elle a échoué sur certains sites.
    # -----------------------------------------------------------------------
    "retry-failed-syncs-morning": {
        "task": "app.tasks.ingestion.retry_failed_sites",
        "schedule": crontab(hour=8, minute=0),
        "options": {"queue": "ingestion"},
    },
}
