"""
Router – Paramètres (Settings).

GET  /api/v1/settings/ga4           → statut connexion GA4
POST /api/v1/settings/ga4/test      → tester la connexion GA4
GET  /api/v1/settings/sites         → liste sites suivis avec statut sync (screen_2)
POST /api/v1/settings/sync/{site_id}→ déclencher une sync manuelle

Correspond au screen_2 : 'Paramètres'.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_admin, get_current_user, get_db
from app.models.site import Site, SiteStatus
from app.models.user import User
from app.schemas.site import SiteSchema
from app.services.ga4_client import GA4Client
from app.core.config import settings

router = APIRouter()



class GA4ConnectionStatus(BaseModel):
    """Statut de la connexion à l'API GA4."""
    connected: bool
    source: str | None = None
    last_test_at: datetime | None = None
    message: str

class GA4CredentialsPayload(BaseModel):
    """Payload pour enregistrer la clé JSON GA4."""
    credentials_json: str


class SyncResult(BaseModel):
    """Résultat d'une synchronisation manuelle."""
    site_id: int
    site_name: str
    success: bool
    message: str
    synced_at: datetime


# ---------------------------------------------------------------------------
# GET /api/v1/settings/ga4 – statut de la connexion
# ---------------------------------------------------------------------------

@router.get(
    "/ga4",
    response_model=GA4ConnectionStatus,
    summary="Statut de la connexion GA4",
    description=(
        "Retourne l'état de la connexion à l'API Google Analytics 4. "
        "Affiche le badge '• Connecté' dans la section Paramètres (screen_2)."
    ),
)
async def get_ga4_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GA4ConnectionStatus:
    """
    Vérifie si les credentials GA4 sont configurés en BDD ou via fichier.
    """
    from app.models.system_setting import SystemSetting
    import os

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "google_credentials"))
    setting = result.scalar_one_or_none()
    
    if setting and setting.value:
        return GA4ConnectionStatus(
            connected=True,
            source="database",
            message="Clé configurée en base de données.",
        )

    creds_exist = os.path.isfile(settings.GA4_CREDENTIALS_PATH)
    return GA4ConnectionStatus(
        connected=creds_exist,
        source="file" if creds_exist else None,
        message="Credentials trouvés (fichier)." if creds_exist else "Aucune configuration GA4 trouvée.",
    )

@router.post(
    "/ga4",
    summary="Sauvegarder les credentials GA4",
    description="Chiffre et sauvegarde le fichier JSON du compte de service GA4.",
)
async def save_ga4_credentials(
    payload: GA4CredentialsPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> dict:
    from app.models.system_setting import SystemSetting
    from app.core.crypto import encrypt_value

    try:
        import json
        # Validation sommaire du JSON
        json.loads(payload.credentials_json)
        encrypted = encrypt_value(payload.credentials_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Format JSON invalide.")

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "google_credentials"))
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = encrypted
    else:
        setting = SystemSetting(key="google_credentials", value=encrypted)
        db.add(setting)

    await db.commit()
    return {"message": "Credentials enregistrés avec succès."}


# ---------------------------------------------------------------------------
# POST /api/v1/settings/ga4/test – tester la connexion
# ---------------------------------------------------------------------------

@router.post(
    "/ga4/test",
    response_model=GA4ConnectionStatus,
    summary="Tester la connexion GA4",
    description=(
        "Effectue un appel de test réel vers l'API GA4 pour valider les credentials. "
        "Déclenché par le bouton 'Tester la connexion' (screen_2)."
    ),
)
async def test_ga4_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GA4ConnectionStatus:
    """
    Bouton 'Tester la connexion' dans l'écran Paramètres (screen_2).

    Utilise la propriété GA4 par défaut configurée en settings.
    """
    if not settings.GA4_DEFAULT_PROPERTY_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GA4_DEFAULT_PROPERTY_ID non configuré dans les variables d'environnement.",
        )

    now = datetime.now(timezone.utc)
    try:
        client = await GA4Client.create(property_id=settings.GA4_DEFAULT_PROPERTY_ID, db=db)
        ok = client.test_connection()
        return GA4ConnectionStatus(
            connected=ok,
            source="test",
            last_test_at=now,
            message="Connexion réussie." if ok else "Échec de la connexion. Vérifiez les credentials.",
        )
    except Exception as exc:
        return GA4ConnectionStatus(
            connected=False,
            source="test",
            last_test_at=now,
            message=f"Erreur : {str(exc)}",
        )


# ---------------------------------------------------------------------------
# GET /api/v1/settings/sites – liste des sites suivis (screen_2)
# ---------------------------------------------------------------------------

@router.get(
    "/sites",
    response_model=list[SiteSchema],
    summary="Sites suivis avec statut de synchronisation",
    description=(
        "Retourne la liste des sites avec leur statut de synchronisation GA4 "
        "(Synchronisé / Attention / Erreur). Correspond à la section "
        "'Sites suivis' dans l'écran Paramètres (screen_2)."
    ),
)
async def list_tracked_sites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SiteSchema]:
    """
    Tableau 'Sites suivis' (screen_2).

    Colonnes : Nom du site | ID propriété GA4 | Statut | Actions.
    """
    result = await db.execute(select(Site).order_by(Site.name))
    sites = result.scalars().all()

    return [
        SiteSchema(
            id=s.id,
            name=s.name,
            url=s.url,
            ga4_property_id=s.ga4_property_id,
            status=s.status,
            health_score=s.health_score,
            is_active=s.is_active,
            last_synced_at=s.last_synced_at,
            created_at=s.created_at,
        )
        for s in sites
    ]


# ---------------------------------------------------------------------------
# POST /api/v1/settings/sync/{site_id} – synchronisation manuelle
# ---------------------------------------------------------------------------

@router.post(
    "/sync/{site_id}",
    response_model=SyncResult,
    summary="Déclencher une synchronisation manuelle",
    description="Force la récupération des données GA4 pour un site spécifique. Admin uniquement.",
)
async def sync_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SyncResult:
    """
    Synchronisation manuelle d'un site (hors cycle automatique Celery).

    Appelle `AggregationService.snapshot_site()` pour mettre à jour
    les métriques du jour et le score de santé.
    """
    from app.services.aggregation import AggregationService

    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Site ID {site_id} introuvable.",
        )

    now = datetime.now(timezone.utc)
    try:
        service = AggregationService(db)
        await service.snapshot_site(site)
        site.last_synced_at = now

        return SyncResult(
            site_id=site.id,
            site_name=site.name,
            success=True,
            message=f"Synchronisation réussie. Score de santé : {site.health_score}%.",
            synced_at=now,
        )
    except Exception as exc:
        site.status = SiteStatus.error
        return SyncResult(
            site_id=site.id,
            site_name=site.name,
            success=False,
            message=f"Erreur de synchronisation : {str(exc)}",
            synced_at=now,
        )
