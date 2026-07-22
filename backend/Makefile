# ==============================================================================
#  Qalam Analytics – Backend Makefile
#  Usage : make <commande>
# ==============================================================================

# --- Variables ---
PYTHON        := python3
VENV          := .venv
PIP           := $(VENV)/bin/pip
UVICORN       := $(VENV)/bin/uvicorn
CELERY        := $(VENV)/bin/celery
ALEMBIC       := $(VENV)/bin/alembic
PYTEST        := $(VENV)/bin/pytest
APP_MODULE    := app.main:app
WORKER_MODULE := app.worker
HOST          := 0.0.0.0
PORT          := 8000
LOG_LEVEL     := info
 
.DEFAULT_GOAL := help
.PHONY: help install env start start-reload stop \
        worker beat worker-beat \
        migrate migrate-create migrate-rollback \
        test test-cov lint format \
        ingest ingest-site health-scores \
        redis-start clean

# ==============================================================================
#  AIDE
# ==============================================================================

help: ## Affiche cette aide
	@echo ""
	@echo "  \033[1;36mQalam Analytics – Backend\033[0m"
	@echo "  ─────────────────────────────────────────────────"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { \
		printf "  \033[32m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# ==============================================================================
#  INSTALLATION
# ==============================================================================

env: ## Crée l'environnement virtuel Python
	@echo "🐍 Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Venv créé dans $(VENV)/"

install: env ## Installe toutes les dépendances Python
	@echo "📦 Installation des dépendances..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dépendances installées."

setup: install ## Setup complet (venv + deps + .env)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📄 .env créé depuis .env.example – pensez à le configurer !"; \
	else \
		echo "ℹ️  .env existe déjà."; \
	fi

# ==============================================================================
#  SERVEUR API
# ==============================================================================

start: ## Lance le serveur FastAPI (production-like, sans reload)
	@echo "🚀 Démarrage de l'API sur http://$(HOST):$(PORT) ..."
	$(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--log-level $(LOG_LEVEL)

start-reload: ## Lance le serveur FastAPI avec auto-reload (développement)
	@echo "🔄 Démarrage en mode développement (reload activé)..."
	$(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--log-level $(LOG_LEVEL) \
		--reload

start-https: ## Lance le serveur FastAPI avec SSL (nécessite cert.pem et key.pem)
	@echo "🔒 Démarrage avec SSL..."
	$(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port 443 \
		--ssl-keyfile key.pem \
		--ssl-certfile cert.pem \
		--log-level $(LOG_LEVEL)

# ==============================================================================
#  CELERY WORKER & BEAT
# ==============================================================================

worker: ## Lance le worker Celery (files : ingestion + default)
	@echo "⚙️  Démarrage du worker Celery..."
	$(CELERY) -A $(WORKER_MODULE) worker \
		--loglevel=$(LOG_LEVEL) \
		--queues=ingestion,default,reports \
		--concurrency=4 \
		--hostname=worker@%h

beat: ## Lance le scheduler Celery Beat (tâches planifiées)
	@echo "🕐 Démarrage de Celery Beat..."
	$(CELERY) -A $(WORKER_MODULE) beat \
		--loglevel=$(LOG_LEVEL) \
		--pidfile=/tmp/celery-beat.pid \
		--schedule=/tmp/celerybeat-schedule

worker-beat: ## Lance worker + beat dans le même process (dev uniquement ⚠️)
	@echo "⚠️  Mode dev : worker + beat combinés (NE PAS utiliser en production)"
	$(CELERY) -A $(WORKER_MODULE) worker \
		--beat \
		--loglevel=$(LOG_LEVEL) \
		--queues=ingestion,default,reports \
		--concurrency=2

flower: ## Lance Flower – interface web de monitoring Celery (http://localhost:5555)
	@echo "🌸 Démarrage de Flower sur http://localhost:5555 ..."
	$(CELERY) -A $(WORKER_MODULE) flower \
		--port=5555 \
		--broker=$(shell grep REDIS_URL .env | cut -d= -f2 | tr -d '"')

celery-status: ## Affiche l'état des workers Celery actifs
	$(CELERY) -A $(WORKER_MODULE) status

celery-inspect: ## Inspecte les tâches actives / réservées / planifiées
	$(CELERY) -A $(WORKER_MODULE) inspect active
	$(CELERY) -A $(WORKER_MODULE) inspect scheduled

# ==============================================================================
#  DÉCLENCHEMENT MANUEL DES TÂCHES
# ==============================================================================

ingest: ## Déclenche l'ingestion GA4 de TOUS les sites maintenant
	@echo "📥 Ingestion GA4 de tous les sites..."
	$(VENV)/bin/python -c "\
		from app.tasks.ingestion import fetch_all_sites_metrics; \
		result = fetch_all_sites_metrics.delay(); \
		print(f'Tâche envoyée : {result.id}')"

ingest-site: ## Déclenche l'ingestion d'un site spécifique (make ingest-site SITE_ID=1)
	@if [ -z "$(SITE_ID)" ]; then \
		echo "❌ Usage : make ingest-site SITE_ID=<id>"; exit 1; \
	fi
	@echo "📥 Ingestion du site ID=$(SITE_ID)..."
	$(VENV)/bin/python -c "\
		from app.tasks.ingestion import fetch_site_metrics; \
		result = fetch_site_metrics.delay($(SITE_ID)); \
		print(f'Tâche envoyée : {result.id}')"

health-scores: ## Recalcule tous les scores de santé depuis la DB
	@echo "🏥 Recalcul des scores de santé..."
	$(VENV)/bin/python -c "\
		from app.tasks.ingestion import update_all_health_scores; \
		result = update_all_health_scores.delay(); \
		print(f'Tâche envoyée : {result.id}')"

cleanup: ## Supprime les snapshots plus anciens que 365 jours
	@echo "🧹 Nettoyage des anciens snapshots..."
	$(VENV)/bin/python -c "\
		from app.tasks.ingestion import cleanup_old_snapshots; \
		result = cleanup_old_snapshots.delay(); \
		print(f'Tâche envoyée : {result.id}')"

# ==============================================================================
#  BASE DE DONNÉES (ALEMBIC)
# ==============================================================================

migrate: ## Applique toutes les migrations en attente
	@echo "🗄️  Application des migrations Alembic..."
	PYTHONPATH=. $(ALEMBIC) upgrade head

migrate-create: ## Crée une nouvelle migration (make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Usage : make migrate-create MSG=\"description de la migration\""; exit 1; \
	fi
	@echo "📝 Création de la migration : $(MSG)"
	PYTHONPATH=. $(ALEMBIC) revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Annule la dernière migration
	@echo "⏪ Rollback de la dernière migration..."
	PYTHONPATH=. $(ALEMBIC) downgrade -1

migrate-history: ## Affiche l'historique des migrations
	PYTHONPATH=. $(ALEMBIC) history --verbose

migrate-current: ## Affiche la version courante de la DB
	PYTHONPATH=. $(ALEMBIC) current

db-reset: ## ⚠️  DANGER – Remet la DB à zéro (downgrade base puis upgrade head)
	@echo "⚠️  Remise à zéro de la base de données..."
	@read -p "Confirmer ? (oui/non) : " CONFIRM; \
	if [ "$$CONFIRM" = "oui" ]; then \
		PYTHONPATH=. $(ALEMBIC) downgrade base && PYTHONPATH=. $(ALEMBIC) upgrade head; \
		echo "✅ Base remise à zéro."; \
	else \
		echo "Annulé."; \
	fi

# ==============================================================================
#  REDIS
# ==============================================================================

redis-start: ## Démarre Redis en arrière-plan (nécessite Redis installé)
	@echo "🔴 Démarrage de Redis..."
	redis-server --daemonize yes --logfile /tmp/redis.log
	@echo "✅ Redis démarré (port 6379)."

redis-stop: ## Arrête Redis
	redis-cli shutdown
	@echo "🔴 Redis arrêté."

redis-flush: ## Vide toutes les clés Redis (⚠️ purge les résultats Celery)
	@echo "🗑️  Purge du cache Redis..."
	redis-cli flushall
	@echo "✅ Redis vidé."

# ==============================================================================
#  TESTS
# ==============================================================================

test: ## Lance tous les tests unitaires
	@echo "🧪 Lancement des tests..."
	$(PYTEST) tests/ -v --tb=short

test-cov: ## Tests avec rapport de couverture HTML
	@echo "🧪 Tests avec couverture..."
	$(PYTEST) tests/ \
		--cov=app \
		--cov-report=html:htmlcov \
		--cov-report=term-missing \
		--tb=short
	@echo "📊 Rapport HTML dans htmlcov/index.html"

test-fast: ## Tests rapides (sans les tests d'intégration GA4)
	$(PYTEST) tests/ -v -m "not integration" --tb=short

# ==============================================================================
#  QUALITÉ DU CODE
# ==============================================================================

lint: ## Vérifie la qualité du code (ruff)
	@echo "🔍 Analyse du code..."
	$(VENV)/bin/ruff check app/ tests/

format: ## Formate le code (ruff + isort)
	@echo "✨ Formatage du code..."
	$(VENV)/bin/ruff check --fix app/ tests/
	$(VENV)/bin/ruff format app/ tests/

typecheck: ## Vérification des types (mypy)
	@echo "🔎 Vérification des types..."
	$(VENV)/bin/mypy app/ --ignore-missing-imports

# ==============================================================================
#  NETTOYAGE
# ==============================================================================

clean: ## Supprime les fichiers temporaires et caches Python
	@echo "🧹 Nettoyage..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé."

clean-venv: clean ## Supprime aussi l'environnement virtuel
	rm -rf $(VENV)
	@echo "✅ Venv supprimé."
