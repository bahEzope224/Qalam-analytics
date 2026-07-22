# Qalam Analytics — Backend

Plateforme d'analytics interne pour QALAM SOFTWARE, centralisant les données Google Analytics 4 (GA4) de 7 sites vitrines de l'entreprise.

Ce document sert de point d'entrée pour tout développeur rejoignant le projet.

---

## 1. Contexte du projet

- **Objectif** : offrir une vue consolidée de la performance de 7 sites web, sans dépendre d'un outil BI du marché (Power BI, BigQuery).
- **Source de données unique** : Google Analytics 4 (GA4 Data API). Aucune donnée de vente n'est intégrée.
- **Sites couverts** : Certiskool.fr, Pedagobridge, Wyn.ma, Feastnfood.com, Antsnetworking.com, Mysharyspace.com, Qalam-software.fr.
- **MVP fonctionnel** : une vue d'ensemble des 7 sites (trafic, tendance, signal de santé, sélecteur de période 7/30/90 jours, classement par performance).
- **Stretch goals** (non garantis) : vue détaillée par site, page de configuration technique (clés API GA4, gestion des sites).
- **Hors scope confirmé** : gestion de comptes/rôles différenciés, alertes automatiques, export PDF automatisé. *(Authentification simple en attente de validation — voir section 8.)*

---

## 2. Architecture

Le backend suit une architecture en 4 couches :

```
GA4 Data API  →  Ingestion  →  PostgreSQL (raw)  →  Traitement (agrégation)  →  PostgreSQL (marts)  →  API REST (FastAPI)  →  Dashboard
```

1. **Ingestion** — Récupération planifiée des données GA4 pour chaque site (7 propriétés), normalisation avant écriture en base.
2. **Stockage** — PostgreSQL. Tables brutes (`raw_*`) séparées des tables agrégées (`agg_*` / marts) pour éviter de recalculer à chaque requête.
3. **Traitement** — Agrégations avec Pandas/Polars : trafic par période, tendances, sources d'acquisition, pages populaires.
4. **Exposition** — API REST FastAPI, consommée par le dashboard (couche de visualisation à définir).

---

## 3. Stack technique

| Composant | Technologie |
|---|---|
| Langage / Framework API | Python 3.11+ / FastAPI |
| Base de données | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Traitement des données | Pandas / Polars |
| Tâches planifiées | APScheduler (ou Celery si la charge le justifie) |
| Validation des données | Pydantic |
| Tests | Pytest |

---

## 4. Structure du projet

```
backend/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/
│   │   ├── config.py            # Configuration (variables d'environnement)
│   │   └── security.py          # Logique d'authentification (stub actuellement)
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── overview.py  # Endpoints vue d'ensemble
│   │       │   └── sites.py     # Endpoints détail par site
│   │       └── dependencies.py  # Dépendances communes (dont get_current_user)
│   ├── models/                  # Modèles SQLAlchemy
│   ├── schemas/                 # Schémas Pydantic (validation entrée/sortie API)
│   ├── services/
│   │   ├── ga4_client.py        # Client d'appel à l'API GA4
│   │   └── aggregation.py       # Logique de calcul des indicateurs
│   ├── db/
│   │   ├── session.py           # Connexion PostgreSQL
│   │   └── base.py
│   └── tasks/
│       └── ingestion.py         # Jobs planifiés de récupération GA4
├── tests/
├── alembic/                     # Migrations de base de données
├── .env.example
├── requirements.txt
└── README.md
```

---

## 5. Installation et démarrage

```bash
# 1. Cloner le dépôt et se placer dans le dossier backend
cd backend

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Copier le fichier d'exemple d'environnement et le compléter
cp .env.example .env

# 5. Appliquer les migrations
alembic upgrade head

# 6. Lancer le serveur de développement
uvicorn app.main:app --reload
```

L'API est ensuite accessible sur `http://localhost:8000`, avec la documentation interactive générée automatiquement sur `http://localhost:8000/docs`.

---

## 6. Variables d'environnement

| Variable | Description |
|---|---|
| `DATABASE_URL` | URL de connexion PostgreSQL |
| `GA4_SERVICE_ACCOUNT_PATH` | Chemin vers le fichier de clé du compte de service Google |
| `GA4_PROPERTY_IDS` | Mapping site → identifiant de propriété GA4 |
| `AUTH_ENABLED` | `true`/`false` — active ou non la vérification d'authentification (voir section 8) |
| `ENVIRONMENT` | `development` / `production` |

**Ne jamais committer le fichier `.env` ni la clé de compte de service GA4.** Ils doivent rester listés dans `.gitignore`.

---

## 7. Modèle de données (aperçu)

- `sites` — référentiel des 7 sites suivis (nom, identifiant de propriété GA4).
- `raw_traffic` — données brutes remontées depuis GA4 (par site, par jour).
- `agg_site_metrics` — indicateurs agrégés par site et par période (trafic, tendance, taux de rebond).

Le schéma est pensé pour être **multi-sites dès le départ** : aucune requête ni logique métier ne doit supposer un nombre fixe de sites (éviter de coder en dur "7 sites" dans la logique — passer par la table `sites`).

---

## 8. Sécurité

### 8.1 Authentification (état actuel)

L'authentification complète n'a pas été validée par le tuteur de stage au moment de l'écriture de ce document. Pour ne pas bloquer le développement, l'architecture est préparée pour l'accueillir sans refactoring majeur :

```python
from fastapi import Depends

async def get_current_user():
    # Stub actuel : accès libre. Toute la logique d'authentification
    # (vérification JWT/session) sera ajoutée ici sans toucher aux routes.
    return {"authenticated": False}

@router.get("/api/sites/overview")
async def get_overview(user=Depends(get_current_user)):
    ...
```

Toute nouvelle route doit systématiquement passer par cette dépendance, même si elle ne fait rien pour l'instant, pour que l'activation future de l'authentification soit centralisée.

### 8.2 Bonnes pratiques à respecter

- **Secrets** : toutes les clés (base de données, compte de service GA4) doivent passer par des variables d'environnement, jamais en dur dans le code.
- **Validation des entrées** : toute donnée entrante (paramètres de requête, corps de requête) doit être validée via des schémas Pydantic — ne jamais faire confiance à une entrée utilisateur brute.
- **Requêtes SQL** : toujours passer par l'ORM (SQLAlchemy) ou des requêtes paramétrées — jamais de concaténation de chaînes pour construire du SQL.
- **CORS** : restreindre les origines autorisées à celles du dashboard, ne pas laisser `*` en production.
- **HTTPS** : obligatoire dès que la plateforme est déployée au-delà d'un usage local.
- **Principe du moindre privilège** : le compte de service GA4 ne doit avoir accès qu'en lecture aux propriétés nécessaires, rien de plus.
- **Logs** : ne jamais logger de données sensibles (clés, identifiants de session).

---

## 9. Scalabilité

Le projet démarre avec un périmètre restreint (7 sites, pas de gros volume), mais quelques principes évitent de devoir tout refaire si le périmètre grandit :

- **Découpler ingestion et API** : les jobs de récupération GA4 (`tasks/ingestion.py`) doivent tourner indépendamment de l'API — jamais d'appel GA4 synchrone déclenché par une requête utilisateur.
- **Respect des quotas GA4** : l'API GA4 Data API impose des limites de requêtes ; prévoir un système de cache (même simple, en base ou en mémoire) pour éviter de re-solliciter GA4 à chaque appel du dashboard.
- **Async I/O** : privilégier des endpoints et clients HTTP asynchrones (FastAPI + `httpx` en mode async) pour éviter de bloquer le serveur pendant les appels GA4.
- **Indexation base de données** : indexer systématiquement les colonnes utilisées dans les filtres fréquents (`site_id`, `date`).
- **API stateless** : ne stocker aucun état de session côté serveur applicatif, pour permettre de dupliquer l'API sur plusieurs instances si le besoin se présente.
- **Pagination** : toute route retournant une liste (pages populaires, historique) doit être paginée dès sa conception, même si le volume actuel ne le justifie pas encore.
- **Généricité multi-sites** : concevoir chaque fonctionnalité comme si le nombre de sites pouvait passer de 7 à 50 sans changement de code — seule la table `sites` doit varier.

---

## 10. Guidelines de développement

- **Convention de code** : suivre PEP 8, formatage automatique via `black`, imports triés avec `isort`.
- **Typage** : utiliser les type hints Python partout, en particulier pour les schémas Pydantic et les signatures de fonctions.
- **Git** : une branche par fonctionnalité (`feature/nom-fonctionnalite`), commits explicites, pas de commit directement sur `main`.
- **Tests** : toute nouvelle route ou service métier doit être accompagnée d'un test dans `tests/`.
- **Documentation** : toute nouvelle route doit avoir une docstring claire (elle alimente automatiquement `/docs`).

---

## 11. Roadmap indicative

| Fonctionnalité | Statut |
|---|---|
| Vue d'ensemble (MVP) | Priorité 1 |
| Vue détaillée par site | Stretch goal |
| Page de configuration technique (GA4, sites) | Probablement nécessaire, à confirmer |
| Authentification simple | En attente de validation par le tuteur |
| Reporting / export | Hors scope actuel — exploratoire uniquement |
| Gestion de comptes/rôles | Hors scope confirmé |

---

## 12. Contact

- **Auteur** : BAH Ibrahima
- **Entreprise** : QALAM SOFTWARE
- **Tuteur de stage** : Ayoub MEKOUAR

Pour toute question sur les choix produit ou le périmètre du projet, se référer au cahier des charges (Google Docs) avant de développer une nouvelle fonctionnalité non listée ci-dessus.