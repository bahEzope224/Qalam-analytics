# ============================================================
#  Dockerfile — Frontend React/Vite
#  Build statique servi par Nginx.
# ============================================================

# ── Étape 1 : build Vite ───────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copier uniquement les manifestes de dépendances (cache Docker)
COPY package.json package-lock.json* ./

RUN npm ci --silent

# Copier le reste du code source
COPY . .

# L'URL de l'API est injectée au build via ARG → VITE_API_URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


# ── Étape 2 : serveur Nginx léger ──────────────────────────
FROM nginx:1.27-alpine AS runtime

# Configuration Nginx pour React Router (SPA)
COPY --from=builder /app/dist /usr/share/nginx/html

# Remplacer la config Nginx par défaut pour gérer le fallback SPA
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    # Compression gzip\n\
    gzip on;\n\
    gzip_types text/css application/javascript image/svg+xml;\n\
\n\
    # Cache long sur les assets versionnés par Vite (hash dans le nom)\n\
    location ~* \\.(js|css|png|svg|ico|woff2?)$ {\n\
        expires 1y;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
\n\
    # SPA fallback : toute route inconnue → index.html\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
