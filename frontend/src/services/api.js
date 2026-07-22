/**
 * api.js — Client HTTP vers le backend FastAPI.
 *
 * Toutes les requêtes vers /api/* passent par ce module.
 * Centralise la base URL, les headers, et la gestion d'erreurs.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

/**
 * Wrapper générique autour de fetch.
 * Lance une Error avec le message de l'API en cas de statut non-2xx.
 *
 * @param {string} path   — chemin relatif (ex. "/api/sites/overview")
 * @param {RequestInit} [options] — options fetch standard
 * @returns {Promise<any>} — body JSON parsé
 */
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const err = await response.json();
      message = err.detail ?? err.message ?? message;
    } catch {
      // ignore parse error
    }
    throw new Error(message);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Endpoints — Vue d'ensemble
// ---------------------------------------------------------------------------

/**
 * Récupère les données agrégées de tous les sites pour la vue d'ensemble.
 *
 * @param {7|30|90} period — période en jours
 * @returns {Promise<Object[]>} — liste de cartes site
 */
export function fetchOverview(period = 30) {
  return request(`/api/sites/overview?period=${period}`);
}

/**
 * Récupère la liste détaillée des sites (tableau).
 *
 * @param {7|30|90} period — période en jours
 * @returns {Promise<Object[]>} — liste des sites avec KPIs détaillés
 */
export function fetchSitesList(period = 30) {
  return request(`/api/sites/?period=${period}`);
}

// ---------------------------------------------------------------------------
// Endpoints — Détail par site
// ---------------------------------------------------------------------------

/**
 * Récupère les données détaillées d'un site.
 *
 * @param {string|number} siteId — identifiant du site
 * @param {7|30|90} period — période en jours
 */
export function fetchSiteDetail(siteId, period = 30) {
  return request(`/api/sites/${siteId}?period=${period}`);
}

// ---------------------------------------------------------------------------
// Endpoints — Paramètres GA4
// ---------------------------------------------------------------------------

/**
 * Récupère la configuration GA4 courante.
 */
export function fetchGA4Settings() {
  return request('/api/settings/ga4');
}

/**
 * Récupère la liste des sites pour la page de configuration (incluant statut).
 */
export function fetchSettingsSites() {
  return request('/api/settings/sites');
}

/**
 * Enregistre la configuration GA4.
 *
 * @param {Object} payload — corps de la requête
 */
export function saveGA4Settings(payload) {
  return request('/api/settings/ga4', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Endpoints — Gestion des sites (admin)
// ---------------------------------------------------------------------------

/**
 * Ajoute un nouveau site en base.
 * @param {Object} payload - { name: string, url: string, ga4_property_id: string }
 */
export function addSite(payload) {
  return request('/api/sites/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Met à jour un site existant.
 * @param {string|number} siteId - ID du site
 * @param {Object} payload - Données à mettre à jour
 */
export function updateSite(siteId, payload) {
  return request(`/api/sites/${siteId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

/**
 * Supprime un site.
 * @param {string|number} siteId - ID du site à supprimer
 */
export function deleteSite(siteId) {
  // retourne text vide sur un DELETE HTTP 204
  const url = `${BASE_URL}/api/sites/${siteId}`;
  return fetch(url, { method: 'DELETE' }).then(res => {
    if (!res.ok) throw new Error("Erreur de suppression");
    return true;
  });
}
