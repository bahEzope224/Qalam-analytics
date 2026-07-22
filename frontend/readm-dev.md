# Qalam Analytics — Frontend

Interface web du dashboard Qalam Analytics, construite en **React**, consommant l'API REST du backend FastAPI.

Ce document décrit le design system, les écrans issus des mockups, et les guidelines pour tout développeur rejoignant le projet.

---

## 1. Contexte

- Dashboard interne centralisant les données GA4 de 7 sites vitrines de QALAM SOFTWARE.
- Consomme l'API REST exposée par le backend (voir `README.md` du backend pour les endpoints).
- Les mockups de référence ont été générés avec Google Stitch à partir de prompts textuels décrivant chaque écran.

---

## 2. Design system

### 2.1 Couleurs

⚠️ **Point important** : les mockups ont été crée en noir et blanc, mais la couleur primaire de la plateforme doit être **violet**, pas noir. Tous les éléments actuellement noirs dans les mockups (boutons principaux, icône active de la sidebar, logo) doivent être recolorés en violet à l'implémentation.

| Rôle | Couleur | Usage |
|---|---|---|
| Primaire | `#7C3AED` | Boutons principaux, éléments actifs (nav sélectionnée), logo |
| Primaire (hover/dark) | `#6D28D9` | États hover/pressed des éléments primaires |
| Primaire (fond clair) | `#F5F3FF` | Fonds d'accent légers, surbrillance discrète |
| Fond de page | `#F8F9FA` | Arrière-plan général des écrans |
| Fond des cartes | `#FFFFFF` | Cartes, tableaux, panneaux |
| Bordures | `#E5E7EB` | Séparateurs, contours de cartes |
| Texte principal | `#111827` | Titres, valeurs chiffrées |
| Texte secondaire | `#6B7280` | Labels, sous-titres |
| Statut positif | `#10B981` | "Sain", "Connecté", "Synchronisé" |
| Statut attention | `#F59E0B` | "Attention", "À réviser" |
| Statut erreur | `#EF4444` | "Erreur", "Hors ligne" |

Les couleurs de statut (vert/orange/rouge) restent identiques à celles des mockups — seule la couleur d'accent "de marque" (actuellement noire) devient violette.

### 2.2 Typographie

- Police '<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@0,100..900;1,100..900&family=Finlandica+Headline:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">'.
- Valeurs chiffrées clés : gras, grande taille (ex : `42,150`).
- Labels de cartes statistiques : petite taille, majuscules, texte secondaire (ex : `VISITES TOTALES`).

### 2.3 Composants UI communs (identifiés dans les mockups)

- **Sidebar de navigation** — logo + items (Dashboard, Websites/Sites, Reports, Settings), item actif mis en évidence par une barre latérale colorée.
- **Barre supérieure** — sélecteur de période (7/30/90 jours), et selon l'écran : recherche, notifications, aide, avatar utilisateur.
- **Carte de statistique** — label secondaire + valeur principale + variation (flèche haut/bas + %).
- **Badge de statut** — pastille colorée + texte court (vert/orange/rouge).
- **Carte de site** (vue d'ensemble) — nom du site, badge de santé en %, trafic, tendance.
- **Tableau de données** — utilisé pour la liste des sites et la gestion GA4 (colonnes alignées, statut en badge, action à droite).
- **Graphique d'évolution** — courbe simple, utilisée pour le trafic dans le temps.
- **Graphique de répartition** — donut chart, utilisé pour les sources d'acquisition.

---

## 3. Écrans (issus des mockups)

### 3.1 Vue d'ensemble — `mockups/overview.png`
**Statut : MVP confirmé.**
Grille de 7 cartes (une par site), avec trafic, tendance vs période précédente, et un badge de santé en %. Sélecteur de période global et tri (par trafic / par tendance) en haut à droite.

### 3.2 Détail par site — `mockups/site-detail.png`
**Statut : stretch goal.**
Vue drill-down d'un site (ex : Certiskool.fr) : cartes de stats clés (visites totales, tendance, taux de rebond), graphique d'évolution du trafic, tableau des pages les plus visitées, donut des sources d'acquisition.

### 3.3 Sites gérés — `mockups/sites-list.png`
**Statut : variante de la vue d'ensemble, à trancher.**
Version tableau (plutôt que cartes) listant les 7 sites avec statut, visites, taux de rebond, session moyenne. À arbitrer avec Ayoub : cette vue coexiste-t-elle avec la vue d'ensemble en cartes, ou est-ce une alternative à ne garder qu'en une seule version ?

### 3.4 Paramètres — `mockups/settings.png`
**Statut : probablement nécessaire (config technique).**
Connexion API GA4 (statut, clé de compte de service, dernière synchronisation) et tableau de gestion des 7 sites (identifiant de propriété GA4, statut de synchronisation).

### 3.5 Rapports — `mockups/reports.png`
**Statut : exploratoire, hors scope validé.** Ne pas développer sans validation explicite d'Ayoub — conservé uniquement à titre d'illustration d'une idée future (génération de rapport synthétique avec export PDF).

---

## 4. ⚠️ Incohérences à trancher avant développement

Les mockups ont été générés séparément (prompts Stitch indépendants) et ne sont **pas parfaitement cohérents entre eux**. À clarifier avant de coder l'UI définitive :

- **Nom/tagline** : "Qalam Analytics — Data Insight" vs "Qalam Anlytics — Data insight" (coquille) vs "Qalam Analytics Engine" selon les écrans. → Fixer un nom et un logo uniques.
- **Langue de la sidebar** : certains écrans utilisent des labels français ("Tableau de bord", "Sites", "Rapports", "Paramètres"), d'autres de l'anglais ("Dashboard", "Websites", "Reports", "Settings"). → Choisir une langue unique pour l'interface.
- **Contenu de la barre supérieure** : varie selon l'écran (recherche, onglets Overview/Real-time/Audience, bouton Export, sélecteur de période). → Définir une barre supérieure standard commune à tous les écrans.
- **Vue d'ensemble en cartes vs en tableau** : `overview.png` et `sites-list.png` répondent au même besoin avec deux traitements visuels différents. → N'en garder qu'un pour le MVP.

---

## 5. Arborescence du projet (React)

```
frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx
│   │   │   └── Topbar.jsx
│   │   ├── cards/
│   │   │   ├── StatCard.jsx
│   │   │   └── SiteCard.jsx
│   │   ├── badges/
│   │   │   └── StatusBadge.jsx
│   │   ├── charts/
│   │   │   ├── TrafficLineChart.jsx
│   │   │   └── AcquisitionDonutChart.jsx
│   │   └── tables/
│   │       └── DataTable.jsx
│   ├── pages/
│   │   ├── Overview.jsx
│   │   ├── SiteDetail.jsx
│   │   ├── Settings.jsx
│   │   └── Reports.jsx        # non branché tant que non validé par Ayoub
│   ├── hooks/
│   │   └── useApi.js
│   ├── services/
│   │   └── api.js             # client HTTP vers le backend FastAPI
│   └── styles/
│       └── tokens.css          # variables CSS du design system (voir section 2.1)
├── public/
├── package.json
└── FRONTEND_README.md
```

---

## 6. Installation et démarrage

```bash
cd frontend
npm install
npm run dev
```

Variable d'environnement à définir (`.env`) :

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## 7. Consommation de l'API backend

| Écran | Endpoint backend attendu |
|---|---|
| Vue d'ensemble | `GET /api/sites/overview?period={7|30|90}` |
| Détail par site | `GET /api/sites/{site_id}?period={7|30|90}` |
| Paramètres | `GET/POST /api/settings/ga4` |

Se référer au `README.md` du backend pour le détail des schémas de réponse au fur et à mesure qu'ils sont implémentés.

---

## 8. Guidelines de développement

- **Un composant, une responsabilité** — éviter les pages monolithiques ; réutiliser `StatCard`, `StatusBadge`, `SiteCard` plutôt que de dupliquer du JSX.
- **Couleurs uniquement via les tokens** (`styles/tokens.css`) — ne jamais coder une couleur en dur dans un composant, pour pouvoir ajuster le violet de marque en un seul endroit.
- **États de chargement et d'erreur** — chaque appel API doit prévoir un état de chargement et un état d'erreur, pas seulement le cas de succès.
- **Accessibilité** — contrastes suffisants (attention particulière avec le violet sur fond clair), focus clavier visible sur les éléments interactifs.
- **Ne pas développer les écrans hors scope** (Rapports, gestion de comptes/rôles) sans validation explicite — voir section 3.5 et le cahier des charges.

---

## 9. Contact

- **Auteur** : BAH Ibrahima
- **Entreprise** : QALAM SOFTWARE
- **Tuteur de stage** : Ayoub MEKOUAR