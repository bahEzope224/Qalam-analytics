# ============================================================
#  Dockerfile — Backend FastAPI
#  Image légère Python 3.12-slim, sans secrets embarqués.
# ============================================================

# ── Étape 1 : builder (installation des dépendances) ───────
FROM python:3.12-slim AS builder

WORKDIR /app

# Installer les outils de compilation si nécessaire (asyncpg, cryptography…)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement requirements pour profiter du cache Docker
COPY requirements.txt .

# Installer dans un répertoire dédié pour le stage suivant
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Étape 2 : image de production ──────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copier les dépendances compilées depuis builder
COPY --from=builder /install /usr/local

# Copier le code source de l'application
COPY . .

# Variables d'environnement par défaut (surchargées au runtime)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production \
    PORT=8000

# Exposer le port de l'API
EXPOSE 8000

# Lancer Uvicorn en mode production (pas de --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
