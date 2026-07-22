"""Déclaration de la Base SQLAlchemy pour Alembic.

Ce module réunit la classe Base et l'ensemble des modèles
afin qu'Alembic (env.py) les détecte pour les migrations.
Les modèles de l'application doivent importer Base depuis app.db.base_class.
"""

from app.db.base_class import Base  # noqa: F401

# Import de tous les modèles pour qu'Alembic puisse les détecter
from app.models.user import User                          # noqa: F401
from app.models.site import Site                          # noqa: F401
from app.models.metrics_snapshot import MetricsSnapshot  # noqa: F401
from app.models.page_metrics import PageMetrics          # noqa: F401
from app.models.system_setting import SystemSetting      # noqa: F401
