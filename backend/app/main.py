"""
Point d'entrée principal de la plateforme Analytics Interne.

Cette API FastAPI expose les indicateurs GA4 agrégés pour les sites
gérés par l'ESN, avec authentification JWT, versioning et documentation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.routers import overview, sites, settings as settings_router, reports


# ---------------------------------------------------------------------------
# Lifespan : startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application :
    - Startup  : initialisation de la connexion DB, cache, etc.
    - Shutdown : libération des ressources.
    """
    # --- STARTUP ---
    # TODO: initialiser la connexion DB (session SQLAlchemy async)
    # TODO: vérifier la disponibilité de l'API GA4
    print(f"🚀  Démarrage de '{settings.APP_NAME}' en mode '{settings.ENV}'")
    yield
    # --- SHUTDOWN ---
    print("🛑  Arrêt de l'application – libération des ressources.")


# ---------------------------------------------------------------------------
# Création de l'application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API interne de la plateforme Analytics. "
        "Expose les métriques GA4 agrégées pour tous les sites gérés par l'ESN."
    ),
    version=settings.API_VERSION,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------

# CORS – à restreindre aux origines du front-end en production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protection basique des hôtes acceptés (désactivé si wildcard '*' pour éviter les faux positifs)
if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# ---------------------------------------------------------------------------
# Handlers d'erreurs globaux
# ---------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Ressource introuvable.", "path": str(request.url)},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur. Veuillez réessayer plus tard."},
    )


# ---------------------------------------------------------------------------
# Inclusion des routers versionnés
# ---------------------------------------------------------------------------

API_PREFIX = f"/api/{settings.API_VERSION}"

app.include_router(
    overview.router,
    prefix=f"{API_PREFIX}/overview",
    tags=["Vue d'ensemble"],
)

app.include_router(
    sites.router,
    prefix=f"{API_PREFIX}/sites",
    tags=["Sites"],
)

app.include_router(
    settings_router.router,
    prefix=f"{API_PREFIX}/settings",
    tags=["Paramètres"],
)

app.include_router(
    reports.router,
    prefix=f"{API_PREFIX}/reports",
    tags=["Rapports"],
)

# ---------------------------------------------------------------------------
# Inclusion des routers de compatibilité (sans /v1 pour le frontend)
# ---------------------------------------------------------------------------

app.include_router(
    sites.router,
    prefix="/api/sites",
    tags=["Sites (Compat)"],
)

app.include_router(
    settings_router.router,
    prefix="/api/settings",
    tags=["Paramètres (Compat)"],
)

app.include_router(
    reports.router,
    prefix="/api/reports",
    tags=["Rapports (Compat)"],
)


# ---------------------------------------------------------------------------
# Routes utilitaires (health check, version)
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"], summary="Vérification racine")
async def root():
    """Endpoint racine – confirme que l'API est opérationnelle."""
    return {
        "app": settings.APP_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "env": settings.ENV,
        "docs": "/docs" if settings.ENV != "production" else "désactivé en production",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """
    Endpoint de santé utilisé par les outils de monitoring (Kubernetes, UptimeRobot…).
    Retourne 200 si l'API répond correctement.
    """
    # TODO: ajouter vérification de la connexion DB et disponibilité GA4
    return {"status": "healthy"}
