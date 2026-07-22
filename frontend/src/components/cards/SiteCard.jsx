/**
 * SiteCard.jsx — Carte représentant un site dans la vue d'ensemble.
 *
 * Affiche : nom du site, badge de santé, trafic total, tendance.
 * Cliquable pour accéder au détail du site.
 *
 * Props :
 *   site {Object} :
 *     id          {string|number}
 *     name        {string}         — ex. "Certiskool.fr"
 *     url         {string}         — ex. "https://certiskool.fr"
 *     health      {number}         — score de santé en % (0-100)
 *     sessions    {number}         — sessions sur la période
 *     change      {number}         — variation % vs période précédente
 *     status      {'ok'|'warn'|'error'}
 *   onClick {(site) => void}       — callback clic
 */

import React from 'react';
import StatusBadge from '../badges/StatusBadge';

const ExternalIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

export default function SiteCard({ site, onClick }) {
  if (!site) return null;

  const { name, url, health = 0, sessions = 0, change = null, status = 'ok' } = site;

  const isPositive = change !== null && change >= 0;
  const changeColor = change === null
    ? 'var(--color-text-secondary)'
    : isPositive ? 'var(--color-status-ok)' : 'var(--color-status-error)';

  return (
    <div
      onClick={() => onClick?.(site)}
      style={{
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        boxShadow: 'var(--shadow-sm)',
        cursor: 'pointer',
        transition: 'all var(--transition-fast)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.boxShadow = 'var(--shadow-md)';
        e.currentTarget.style.borderColor = 'var(--color-primary)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
        e.currentTarget.style.borderColor = 'var(--color-border)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      {/* En-tête : nom + statut */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{
            fontSize: 'var(--text-base)',
            fontWeight: 'var(--weight-semibold)',
            color: 'var(--color-text-primary)',
            margin: 0,
          }}>
            {name}
          </p>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-secondary)',
                textDecoration: 'none',
              }}
            >
              {url.replace(/^https?:\/\//, '')} <ExternalIcon />
            </a>
          )}
        </div>
        <StatusBadge status={status} />
      </div>

      {/* Score de santé */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>Santé</span>
          <span style={{
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--weight-bold)',
            color: health >= 80 ? 'var(--color-status-ok)' : health >= 50 ? 'var(--color-status-warn)' : 'var(--color-status-error)',
          }}>
            {health}%
          </span>
        </div>
        <div style={{
          height: 6, background: 'var(--color-bg-page)', borderRadius: 'var(--radius-full)', overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${health}%`,
            background: health >= 80 ? 'var(--color-status-ok)' : health >= 50 ? 'var(--color-status-warn)' : 'var(--color-status-error)',
            borderRadius: 'var(--radius-full)',
            transition: 'width var(--transition-slow)',
          }} />
        </div>
      </div>

      {/* Métriques */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Sessions
          </p>
          <p style={{ margin: 0, fontSize: 'var(--text-xl)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
            {sessions.toLocaleString('fr-FR')}
          </p>
        </div>
        {change !== null && (
          <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)', color: changeColor }}>
            {isPositive ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}
