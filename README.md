<div align="center">

<h1>🌐 Qalam Analytics</h1>
<p><strong>Plateforme interne de surveillance des performances web</strong><br/>Tableau de bord centralisé connecté à Google Analytics 4</p>

[![CI](https://github.com/bahEzope224/Qalam-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/bahEzope224/Qalam-analytics/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://docker.com)

</div>

---

## 📋 Présentation

**Qalam Analytics** est une plateforme interne permettant de surveiller en temps réel les performances et la santé des sites web d'un portefeuille. Elle agrège les données Google Analytics 4 de chaque site et les présente dans une interface moderne et centralisée.

### Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| 📊 **Vue d'ensemble** | Grille de cartes par site avec trafic, tendance et score de santé |
| 📋 **Tableau des sites** | Liste détaillée avec KPIs (visites, taux de rebond, durée de session) |
| 🔍 **Détail d'un site** | Graphiques de trafic, pages populaires, sources d'acquisition |
| ⚙️ **Paramètres** | Gestion de la clé de compte de service GA4 et des sites |
| 🔐 **Authentification** | JWT avec gestion des rôles admin/utilisateur |
| 🔒 **Sécurité** | Credentials GA4 chiffrés en base de données (Fernet) |

---

## 🏗️ Architecture

```
analytic-plateform/
├── backend/                  # API FastAPI (Python 3.12)
│   ├── app/
│   │   ├── api/v1/routers/  # sites, overview, settings, reports
│   │   ├── core/            # config, sécurité, crypto
│   │   ├── models/          # SQLAlchemy : Site, User, SystemSetting
│   │   ├── schemas/         # Pydantic : validation I/O
│   │   └── services/        # GA4Client, AggregationService
│   ├── alembic/             # Migrations de base de données
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                 # Interface React 18 + Vite
│   ├── src/
│   │   ├── components/      # Topbar, Sidebar, DataTable, SiteCard…
│   │   ├── pages/           # Dashboard, Overview, SiteDetail, Settings
│   │   ├── services/        # api.js (appels HTTP)
│   │   ├── hooks/           # useApi
│   │   └── styles/          # tokens.css (design system)
│   ├── Dockerfile
│   └── package.json
│
├── .github/workflows/
│   ├── ci.yml               # Lint + Tests + Build
│   └── cd.yml               # Build Docker + Deploy SSH
└── docker-compose.yml       # Stack complète
```

---

## 🚀 Démarrage rapide

### Prérequis

- **Python** 3.12+
- **Node.js** 20+
- **PostgreSQL** 16+
- **Redis** 7+ *(optionnel — cache et tâches planifiées)*

### Installation locale

```bash
# 1. Cloner le dépôt
git clone https://github.com/bahEzope224/Qalam-analytics.git
cd Qalam-analytics

# 2. ── BACKEND ──────────────────────────────────────────
cd backend
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate

pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# → Éditer .env avec vos valeurs (DATABASE_URL, SECRET_KEY…)

# 4. Appliquer les migrations
alembic upgrade head

# 5. Lancer l'API
uvicorn app.main:app --reload
# API disponible sur http://localhost:8000
# Documentation interactive : http://localhost:8000/docs

# 6. ── FRONTEND ─────────────────────────────────────────
cd ../frontend
npm install
npm run dev
# Interface disponible sur http://localhost:5174
```

---

## 🐳 Démarrage avec Docker

```bash
# Copier et configurer les variables d'environnement
cp backend/.env.example backend/.env

# Lancer toute la stack
docker compose up --build

# Appliquer les migrations (première fois)
docker compose exec backend alembic upgrade head
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| API | http://localhost:8000 |
| Docs API | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

---

## 🔗 Connexion à Google Analytics 4

1. Créer un **compte de service** sur [Google Cloud Console](https://console.cloud.google.com/) et activer l'API **Google Analytics Data**.
2. Télécharger la clé JSON du compte de service.
3. Dans Google Analytics → Administration → **Gestion des accès à la propriété** : ajouter l'e-mail du compte de service avec le rôle **Lecteur**.
4. Dans Qalam Analytics → **Paramètres** : coller le contenu JSON dans la zone prévue et enregistrer.
5. Ajouter vos sites avec leur URL et leur **ID de propriété GA4** (9 chiffres).

---

## ⚙️ Variables d'environnement

| Variable | Description | Exemple |
|---|---|---|
| `SECRET_KEY` | Clé JWT (32 chars min) | `openssl rand -hex 32` |
| `DATABASE_URL` | URL PostgreSQL async | `postgresql+asyncpg://user:pass@localhost/db` |
| `GA4_CREDENTIALS_PATH` | Chemin vers le JSON GA4 *(optionnel)* | `credentials/sa.json` |
| `ALLOWED_ORIGINS` | Origines CORS autorisées (JSON) | `["http://localhost:5174"]` |
| `REDIS_URL` | URL Redis pour le cache | `redis://localhost:6379/0` |
| `ENV` | Environnement | `development` \| `production` |

> Copier `backend/.env.example` → `backend/.env` et adapter les valeurs.

---

## 🔄 CI/CD — GitHub Actions

### Pipeline CI (`.github/workflows/ci.yml`)
Déclenché sur chaque push/PR vers `main` ou `develop` :

```
Ruff lint → Pytest (PostgreSQL de service) → Build Vite
```

### Pipeline CD (`.github/workflows/cd.yml`)
Déclenché sur chaque tag `vX.Y.Z` ou manuellement :

```
Build image Docker → Push Docker Hub → Deploy SSH → alembic upgrade head
```

#### Secrets GitHub requis

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Identifiant Docker Hub |
| `DOCKERHUB_TOKEN` | Token d'accès Docker Hub |
| `DEPLOY_HOST` | IP / hostname du serveur de production |
| `DEPLOY_USER` | Utilisateur SSH |
| `DEPLOY_SSH_KEY` | Clé privée SSH |

---

## 🛠️ Stack technique

### Backend
| Technologie | Rôle |
|---|---|
| **FastAPI 0.115** | Framework API REST asynchrone |
| **SQLAlchemy 2.0** | ORM async avec asyncpg |
| **Alembic** | Migrations de base de données |
| **PostgreSQL 16** | Base de données principale |
| **Redis 7** | Cache et broker Celery |
| **google-analytics-data** | SDK officiel GA4 |
| **python-jose** | Tokens JWT |
| **passlib/bcrypt** | Hachage des mots de passe |
| **Fernet (cryptography)** | Chiffrement des credentials GA4 |

### Frontend
| Technologie | Rôle |
|---|---|
| **React 18** | UI Component Library |
| **Vite 5** | Bundler + Dev Server |
| **React Router 6** | Navigation SPA |
| **Recharts** | Graphiques (trafic, acquisition) |
| **CSS Variables** | Design system (tokens) |

---

## 📄 Licence

Ce projet est développé en interne par **Qalam Software** — © 2026. Tous droits réservés.
