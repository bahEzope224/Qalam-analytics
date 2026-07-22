"""
Smoke tests — vérifie que l'application FastAPI démarre correctement.

Ces tests sont volontairement minimalistes : ils servent uniquement à
garantir que le pipeline CI ne s'arrête pas avec "no tests ran" (exit 4).
Des tests métier seront ajoutés au fur et à mesure du développement.
"""


def test_app_imports() -> None:
    """L'application FastAPI doit être importable sans erreur."""
    from app.main import app  # noqa: F401  (import utilisé pour la vérification)

    assert app is not None


def test_settings_load() -> None:
    """Les settings doivent se charger depuis les variables d'environnement."""
    from app.core.config import settings

    # En CI, DATABASE_URL est injecté via le job env:
    assert settings.DATABASE_URL is not None
    assert len(str(settings.DATABASE_URL)) > 0
