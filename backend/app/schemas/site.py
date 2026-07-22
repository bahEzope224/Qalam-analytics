"""
Schémas Pydantic – Site.

Couvre les réponses API pour :
- screen_3 : liste "Sites Gérés" (tableau multi-sites)
- screen_4 : tableau de bord (cards par site)
- screen_2 : paramètres (CRUD des sites suivis)
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, HttpUrl, Field, field_validator

from app.models.site import SiteStatus


# ---------------------------------------------------------------------------
# Schémas de base
# ---------------------------------------------------------------------------

class SiteBase(BaseModel):
    """Champs communs partagés entre création et mise à jour."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Certiskool.fr"])
    url: str = Field(..., examples=["https://certiskool.fr"])
    ga4_property_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        examples=["258493021"],
        description="Identifiant numérique de la propriété GA4 (sans le préfixe 'properties/').",
    )


# ---------------------------------------------------------------------------
# Création / mise à jour
# ---------------------------------------------------------------------------

class SiteCreate(SiteBase):
    """
    Payload pour créer un nouveau site.
    Utilisé sur : POST /api/v1/sites/
    Correspond au bouton '+ Ajouter un site' (screen_2 et screen_3).
    """
    pass


class SiteUpdate(BaseModel):
    """
    Payload pour mettre à jour un site existant (PATCH partiel).
    Utilisé sur : PATCH /api/v1/sites/{site_id}
    Correspond au bouton 'Modifier' dans screen_2.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    url: str | None = None
    ga4_property_id: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Réponses API
# ---------------------------------------------------------------------------

class SiteSchema(BaseModel):
    """
    Représentation publique d'un site – réponse standard.

    Utilisé dans :
    - screen_3 : ligne du tableau "Sites Gérés"
      → name, status, total_visits, bounce_rate, avg_session_duration
    - screen_2 : ligne du tableau "Sites suivis"
      → name, ga4_property_id, status, last_synced_at
    """
    id: int
    name: str
    url: str
    ga4_property_id: str
    status: SiteStatus
    health_score: int = Field(..., ge=0, le=100, description="Score de santé (0–100).")
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime

    # Métriques synthétiques agrégées (calculées à la volée, non stockées ici)
    # Présentes dans screen_3 : Visites totales 30j, Taux de rebond, Session moyenne
    total_visits: int | None = Field(
        None, description="Sessions totales sur les 30 derniers jours."
    )
    bounce_rate_pct: float | None = Field(
        None, description="Taux de rebond moyen en pourcentage (ex. 34.2)."
    )
    avg_session_duration_seconds: float | None = Field(
        None, description="Durée moyenne de session en secondes (ex. 134 = 2m 14s)."
    )

    model_config = {"from_attributes": True}


class SiteDashboardCard(BaseModel):
    """
    Card de tableau de bord par site – screen_4 'Vue d'ensemble des sites'.

    Affiche : score de santé, visites totales, tendance vs période précédente.
    """
    id: int
    name: str
    status: SiteStatus
    health_score: int = Field(..., ge=0, le=100)
    total_visits: int
    trend_pct: float = Field(
        ..., description="Variation % vs la période précédente. Ex. +12.5 ou -4.1."
    )

    model_config = {"from_attributes": True}


class SiteStatusUpdate(BaseModel):
    """
    Mise à jour manuelle du statut d'un site.
    Utilisé en interne par les tâches d'ingestion.
    """
    status: SiteStatus
    health_score: int = Field(..., ge=0, le=100)
