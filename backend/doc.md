# 📘 Documentation Technique – Backend Analytics Platform

> API FastAPI interne exposant les métriques **Google Analytics 4 (GA4)** pour les sites web gérés par l'ESN.

---

## Table des matières

1. [Architecture générale](#1-architecture-générale)
2. [Démarrage rapide](#2-démarrage-rapide)
3. [Point d'entrée – `main.py`](#3-point-dentrée--mainpy)
4. [Configuration – `core/config.py`](#4-configuration--coreconfigpy)
5. [Sécurité – `core/security.py`](#5-sécurité--coresecuritypy)
6. [Dépendances API – `api/v1/dependencies.py`](#6-dépendances-api--apiv1dependenciespy)
7. [Routers API](#7-routers-api)
   - [Overview – `routers/overview.py`](#71-overview--routersoverviewpy)
   - [Sites – `routers/sites.py`](#72-sites--routerssitespy)
8. [Services](#8-services)
   - [Client GA4 – `services/ga4_client.py`](#81-client-ga4--servicesga4_clientpy)
   - [Agrégation – `services/aggregation.py`](#82-agrégation--servicesaggregationpy)
9. [Base de données](#9-base-de-données)
   - [Session – `db/session.py`](#91-session--dbsessionpy)
   - [Base – `db/base.py`](#92-base--dbbasepy)
10. [Tâches planifiées – `tasks/ingestion.py`](#10-tâches-planifiées--tasksingestionpy)
11. [Modèles et Schémas](#11-modèles-et-schémas)
12. [Variables d'environnement](#12-variables-denvironnement)
13. [Conventions et règles de développement](#13-conventions-et-règles-de-développement)

---

## 1. Architecture générale

```
backend/
├── app/
│   ├── main.py                  # Point d'entrée FastAPI
│   ├── core/
│   │   ├── config.py            # Variables d'environnement (pydantic-settings)
│   │   └── security.py          # JWT : création & vérification de tokens
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── overview.py  # GET /api/v1/overview – métriques globales
│   │       │   └── sites.py     # GET /api/v1/sites – métriques par site
│   │       └── dependencies.py  # get_current_user, get_db, etc.
│   ├── models/                  # ORM SQLAlchemy (tables DB)
│   ├── schemas/                 # Pydantic : validation entrée/sortie
│   ├── services/
│   │   ├── ga4_client.py        # Appels à l'API Data GA4
│   │   └── aggregation.py       # Calcul des KPIs agrégés
│   ├── db/
│   │   ├── session.py           # Moteur & SessionLocal async
│   │   └── base.py              # Déclaration de Base pour Alembic
│   └── tasks/
│       └── ingestion.py         # Jobs Celery de récupération GA4
├── tests/
├── alembic/                     # Migrations de base de données
├── .env.example
├── requirements.txt
└── doc.md                       # Ce fichier
```

**Flux de données principal :**

```
Client HTTP
    │
    ▼
FastAPI (main.py)
    │  Middleware CORS / Auth
    ▼
Router (overview / sites)
    │  Dépendance get_current_user
    ▼
Service (ga4_client + aggregation)
    │
    ▼
API Google Analytics 4  <-->  DB PostgreSQL (cache / historique)
```

---

## 2. Démarrage rapide

```bash
# 1. Copier les variables d'environnement
cp .env.example .env

# 2. Créer et activer l'environnement virtuel
python -m venv .venv && source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'API en développement
uvicorn app.main:app --reload --port 8000
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Vérification racine |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI (dev uniquement) |
| `http://localhost:8000/redoc` | ReDoc (dev uniquement) |

---

## 3. Point d'entrée – `main.py`

**Fichier :** `app/main.py`

### `lifespan(app: FastAPI)` — *async context manager*

Gère le cycle de vie complet de l'application via `@asynccontextmanager`.

| Phase | Rôle | À compléter |
|-------|------|-------------|
| **Startup** | Initialisation des ressources | Connexion DB, vérification GA4 |
| **Shutdown** | Libération propre | Fermeture des sessions, flush cache |

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    yield
    # SHUTDOWN
```

> ⚠️ Toujours utiliser `lifespan` plutôt que les anciens `@app.on_event("startup")` (dépréciés depuis FastAPI 0.93).

---

### `not_found_handler(request, exc)` — *exception handler 404*

Intercepte toutes les erreurs 404 et retourne une réponse JSON homogène :

```json
{
  "detail": "Ressource introuvable.",
  "path": "http://localhost:8000/mauvaise-route"
}
```

---

### `internal_error_handler(request, exc)` — *exception handler 500*

Intercepte les erreurs 500 non gérées. En production, **ne jamais exposer le traceback** dans la réponse — c'est garanti ici.

---

### `root()` — `GET /`

Retourne l'état de l'application : nom, version, environnement actif.

**Réponse exemple :**
```json
{
  "app": "Analytics Platform API",
  "version": "v1",
  "status": "running",
  "env": "development",
  "docs": "/docs"
}
```

---

### `health_check()` — `GET /health`

Endpoint léger pour le monitoring (Kubernetes liveness probe, UptimeRobot, etc.).

**À enrichir avec :**
- Vérification de la connexion PostgreSQL
- Ping Redis
- Test d'accessibilité de l'API GA4

**Réponse :** `{ "status": "healthy" }` — HTTP 200

---

### Middlewares enregistrés

| Middleware | Rôle | Config |
|------------|------|--------|
| `CORSMiddleware` | Autorise les requêtes cross-origin | `settings.ALLOWED_ORIGINS` |
| `TrustedHostMiddleware` | Bloque les hôtes non déclarés | `settings.ALLOWED_HOSTS` |

---

## 4. Configuration – `core/config.py`

**Fichier :** `app/core/config.py`

### Classe `Settings(BaseSettings)`

Classe unique de configuration chargée automatiquement depuis le fichier `.env`. Une instance globale `settings` est exportée et importée dans toute l'application.

```python
from app.core.config import settings

print(settings.APP_NAME)   # "Analytics Platform API"
print(settings.ENV)        # "development"
```

#### Variables disponibles

| Variable | Type | Défaut | Description |
|----------|------|--------|-------------|
| `APP_NAME` | `str` | `"Analytics Platform API"` | Nom affiché dans les docs |
| `API_VERSION` | `str` | `"v1"` | Préfixe de versioning des routes |
| `ENV` | `str` | `"development"` | Environnement actif |
| `SECRET_KEY` | `str` | *(à changer)* | Clé de signature JWT |
| `ALGORITHM` | `str` | `"HS256"` | Algorithme JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `60` | Durée de vie du token |
| `DATABASE_URL` | `str` | `postgresql+asyncpg://...` | URL de connexion PostgreSQL async |
| `GA4_CREDENTIALS_PATH` | `str` | `credentials/ga4_service_account.json` | Compte de service Google |
| `GA4_DEFAULT_PROPERTY_ID` | `str` | `""` | ID de propriété GA4 par défaut |
| `ALLOWED_ORIGINS` | `List[str]` | `[localhost:3000, localhost:5173]` | Origines CORS autorisées |
| `ALLOWED_HOSTS` | `List[str]` | `["*"]` | Hôtes de confiance |
| `REDIS_URL` | `str` | `redis://localhost:6379/0` | URL Redis |

> 🔒 **Règle de sécurité :** `SECRET_KEY` doit être définie en variable d'environnement système en staging/production. Ne jamais versionner le `.env` réel.

---

## 5. Sécurité – `core/security.py`

**Fichier :** `app/core/security.py` — *stub à implémenter*

### `create_access_token(data: dict, expires_delta: timedelta | None) → str`

Génère un JWT signé avec `SECRET_KEY` et `ALGORITHM`.

```python
token = create_access_token(data={"sub": user.email})
```

### `verify_token(token: str) → dict`

Décode et valide un JWT. Lève `HTTPException(401)` si invalide ou expiré.

### `hash_password(plain: str) → str`

Hache un mot de passe avec `bcrypt` via `passlib`.

### `verify_password(plain: str, hashed: str) → bool`

Vérifie la correspondance mot de passe / hash.

---

## 6. Dépendances API – `api/v1/dependencies.py`

**Fichier :** `app/api/v1/dependencies.py` — *stub à implémenter*

### `get_current_user(token: str) → User`

Dépendance FastAPI injectée dans tous les endpoints protégés.

```python
@router.get("/protected")
async def endpoint(user: User = Depends(get_current_user)):
    ...
```

**Logique :**
1. Extrait le Bearer token de l'en-tête `Authorization`
2. Appelle `security.verify_token(token)`
3. Récupère l'utilisateur en base via son `sub`
4. Lève `HTTPException(401)` si l'utilisateur est inactif ou introuvable

### `get_db() → AsyncSession`

Générateur de session SQLAlchemy async. Garantit la fermeture de la session après chaque requête.

```python
@router.get("/data")
async def endpoint(db: AsyncSession = Depends(get_db)):
    ...
```

---

## 7. Routers API

Tous les routers sont montés sous le préfixe `/api/v1/`.

### 7.1 Overview – `routers/overview.py`

**Fichier :** `app/api/v1/routers/overview.py`

| Méthode | Route | Fonction | Description |
|---------|-------|----------|-------------|
| `GET` | `/api/v1/overview/` | `get_overview()` | Métriques agrégées de tous les sites |

#### `get_overview() → dict`

Retourne les KPIs consolidés : sessions totales, utilisateurs, taux de rebond moyen, pages vues, évolution vs période précédente.

**Implémentation prévue :**
```python
metrics = await aggregation_service.get_global_metrics(period="last_30_days")
return metrics
```

---

### 7.2 Sites – `routers/sites.py`

**Fichier :** `app/api/v1/routers/sites.py`

| Méthode | Route | Fonction | Description |
|---------|-------|----------|-------------|
| `GET` | `/api/v1/sites/` | `list_sites()` | Liste tous les sites gérés |
| `GET` | `/api/v1/sites/{site_id}` | `get_site(site_id)` | Métriques détaillées d'un site |

#### `list_sites() → list[SiteSchema]`

Retourne la liste des sites avec leurs métadonnées. Paramètres prévus : `page`, `limit`.

#### `get_site(site_id: str) → SiteDetailSchema`

Retourne les métriques complètes d'un site. Paramètres prévus : `start_date`, `end_date`, `metrics`.

---

## 8. Services

### 8.1 Client GA4 – `services/ga4_client.py`

**Fichier :** `app/services/ga4_client.py` — *à implémenter*

#### `GA4Client.__init__(credentials_path: str, property_id: str)`

Initialise le client authentifié via un compte de service Google.

#### `GA4Client.run_report(dimensions, metrics, date_ranges) → RunReportResponse`

Lance une requête GA4 Data API et retourne la réponse brute.

```python
client = GA4Client(
    credentials_path=settings.GA4_CREDENTIALS_PATH,
    property_id="properties/123456789"
)
report = await client.run_report(
    dimensions=["date", "sessionSource"],
    metrics=["sessions", "activeUsers", "bounceRate"],
    date_ranges=[{"start_date": "30daysAgo", "end_date": "today"}]
)
```

#### `GA4Client.get_realtime(property_id: str) → dict`

Récupère les données temps-réel (utilisateurs actifs, pages courantes).

---

### 8.2 Agrégation – `services/aggregation.py`

**Fichier :** `app/services/aggregation.py` — *à implémenter*

#### `get_global_metrics(period: str) → GlobalMetricsSchema`

Agrège les métriques de tous les sites pour la période donnée.

#### `get_site_metrics(property_id: str, start_date: str, end_date: str) → SiteMetricsSchema`

Calcule les KPIs pour un site spécifique.

#### `compute_trend(current: float, previous: float) → float`

Calcule la variation en pourcentage entre deux périodes.

```python
compute_trend(1200, 1000)  # → +20.0
compute_trend(800, 1000)   # → -20.0
```

---

## 9. Base de données

### 9.1 Session – `db/session.py`

**Fichier :** `app/db/session.py` — *à implémenter*

```python
engine = create_async_engine(settings.DATABASE_URL, echo=settings.ENV == "development")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### 9.2 Base – `db/base.py`

**Fichier :** `app/db/base.py`

Exporte `Base = DeclarativeBase()` utilisé par tous les modèles SQLAlchemy et importé par Alembic pour les migrations.

```python
from app.db.base import Base
from app.models import *   # nécessaire pour qu'Alembic détecte les tables
```

---

## 10. Tâches planifiées – `tasks/ingestion.py`

**Fichier :** `app/tasks/ingestion.py` — *à implémenter*

### `fetch_all_sites_metrics()`

Tâche Celery périodique (ex. toutes les nuits à 02h00) qui :
1. Récupère la liste de tous les sites depuis la DB
2. Pour chaque site, appelle `GA4Client.run_report()`
3. Transforme les données via `aggregation_service`
4. Insère / met à jour les enregistrements en base

### `fetch_site_metrics(site_id: str)`

Version unitaire pour un seul site (retry ou déclenchement manuel).

**Configuration Celery beat :**
```python
CELERYBEAT_SCHEDULE = {
    "fetch-all-sites-nightly": {
        "task": "app.tasks.ingestion.fetch_all_sites_metrics",
        "schedule": crontab(hour=2, minute=0),
    }
}
```

---

## 11. Modèles et Schémas

### `models/` — SQLAlchemy ORM

| Modèle (prévu) | Table | Description |
|----------------|-------|-------------|
| `Site` | `sites` | Informations d'un site client (nom, URL, GA4 property ID) |
| `User` | `users` | Utilisateurs internes de la plateforme |
| `MetricsSnapshot` | `metrics_snapshots` | Snapshot journalier des métriques GA4 par site |

### `schemas/` — Pydantic

| Schéma (prévu) | Usage | Description |
|----------------|-------|-------------|
| `SiteSchema` | Réponse API | Représentation publique d'un site |
| `SiteCreateSchema` | Entrée API | Création d'un nouveau site |
| `SiteDetailSchema` | Réponse API | Site + métriques détaillées |
| `GlobalMetricsSchema` | Réponse API | KPIs agrégés multi-sites |
| `TokenSchema` | Auth | Access token JWT retourné au login |
| `UserSchema` | Auth | Données utilisateur courantes |

---

## 12. Variables d'environnement

Voir `.env.example` pour le fichier complet.

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `SECRET_KEY` | ✅ Oui | Clé JWT — générer avec `openssl rand -hex 32` |
| `DATABASE_URL` | ✅ Oui | URL PostgreSQL async |
| `GA4_CREDENTIALS_PATH` | ✅ Oui | Fichier JSON compte de service Google |
| `GA4_DEFAULT_PROPERTY_ID` | ✅ Oui | ID de propriété GA4 (format `properties/XXXXXX`) |
| `ENV` | Non | `development` par défaut |
| `REDIS_URL` | Non | Requis si Celery activé |
| `ALLOWED_ORIGINS` | Non | À restreindre en production |

---

## 13. Conventions et règles de développement

### Structure des réponses API

```json
// Succès
{ "data": { ... }, "meta": { "total": 42, "page": 1 } }

// Erreur
{ "detail": "Message d'erreur clair.", "code": "ERROR_CODE" }
```

### Versioning

- Toutes les routes sont préfixées `/api/v1/`
- En cas de breaking change, créer un router `api/v2/` sans supprimer `v1`

### Authentification

- Toutes les routes (sauf `/`, `/health`, `/docs`) nécessitent un Bearer JWT
- Injecter via `Depends(get_current_user)` dans chaque router

### Codes HTTP

| Code | Quand l'utiliser |
|------|-----------------|
| `200` | Succès standard |
| `201` | Ressource créée |
| `400` | Données invalides côté client |
| `401` | Non authentifié |
| `403` | Authentifié mais non autorisé |
| `404` | Ressource introuvable |
| `422` | Validation Pydantic échouée |
| `500` | Erreur serveur interne |

### Tests

```bash
# Lancer tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=app --cov-report=html
```

---

*Document maintenu à jour au fil du développement. Dernière mise à jour : juillet 2026.*
