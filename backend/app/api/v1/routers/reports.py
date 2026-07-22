"""
Router – Rapports.

POST /api/v1/reports/generate  → générer un rapport multi-sites
GET  /api/v1/reports/export    → exporter en PDF (stub)

Correspond au screen_10 : 'Génération de rapports'.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.dependencies import get_current_user, get_db
from app.models.site import Site
from app.models.user import User
from app.schemas.metrics import ReportResponse
from app.services.aggregation import AggregationService

router = APIRouter()


# ---------------------------------------------------------------------------
# Schéma de la requête de rapport
# ---------------------------------------------------------------------------

class ReportRequest(BaseModel):
    """
    Paramètres de génération d'un rapport (panneau gauche, screen_10).

    Attributes:
        period_days: Durée de la période (7, 30 ou 90 jours).
        site_ids:    Liste des IDs de sites à inclure (vide = tous).
    """
    period_days: Literal[7, 30, 90] = 30
    site_ids: list[int] = []


# ---------------------------------------------------------------------------
# POST /api/v1/reports/generate
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=ReportResponse,
    summary="Générer un rapport multi-sites",
    description=(
        "Génère un rapport consolidé pour les sites sélectionnés sur la période choisie. "
        "Retourne la série temporelle de trafic cumulé et un résumé par site. "
        "Correspond au bouton '▶ Générer le rapport' (screen_10)."
    ),
)
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """
    Générateur de rapports (screen_10).

    Flux :
    1. Charge les sites demandés (ou tous si site_ids est vide)
    2. Appelle AggregationService.generate_report()
    3. Retourne la prévisualisation du rapport

    Le rapport contient :
    - Graphique de synthèse : 'Évolution du Trafic Cumulé'
    - Cards par site : visites + tendance %
    """
    # Charger les sites
    if payload.site_ids:
        result = await db.execute(
            select(Site).where(
                Site.id.in_(payload.site_ids),
                Site.is_active == True,  # noqa: E712
            )
        )
    else:
        result = await db.execute(
            select(Site).where(Site.is_active == True)  # noqa: E712
        )

    sites = result.scalars().all()

    if not sites:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun site actif trouvé pour générer le rapport.",
        )

    service = AggregationService(db)
    return await service.generate_report(sites=list(sites), period_days=payload.period_days)


# ---------------------------------------------------------------------------
# GET /api/v1/reports/export – export PDF
# ---------------------------------------------------------------------------

@router.get(
    "/export",
    summary="Exporter un rapport en PDF",
    description=(
        "Déclenche la génération d'un PDF du rapport. "
        "Correspond au bouton '↓ Exporter en PDF' (screen_10). "
        "⚠️ Fonctionnalité à implémenter avec une lib PDF (WeasyPrint, reportlab…)."
    ),
)
async def export_report_pdf(
    period_days: Literal[7, 30, 90] = Query(default=30),
    site_ids: str = Query(
        default="",
        description="IDs de sites séparés par des virgules (ex. '1,2,3'). Vide = tous.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """
    Export PDF du rapport (screen_10 – bouton 'Exporter en PDF').

    TODO: Intégrer WeasyPrint ou une solution de rendu PDF pour générer
    un fichier PDF à partir du ReportResponse et le retourner en
    StreamingResponse avec Content-Type: application/pdf.
    """
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": "Export PDF non encore implémenté.",
            "hint": "Utiliser WeasyPrint ou reportlab pour générer le PDF.",
        },
    )
