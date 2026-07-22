/**
 * StatCard.jsx — Carte de statistique clé (KPI).
 *
 * Affiche un label, une valeur principale et une variation optionnelle
 * (flèche haut/bas + %).
 *
 * Props :
 *   label     {string}            — ex. "VISITES TOTALES"
 *   value     {string|number}     — ex. "42,150" ou 42150
 *   change    {number|null}       — variation en % (positif = hausse)
 *   icon      {React.ReactNode}   — icône optionnelle
 *   loading   {boolean}
 */

import React from 'react';

const ArrowUp = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
  </svg>
);

const ArrowDown = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
);

export default function StatCard({ label = '', value = '—', change = null, icon = null, loading = false }) {
  const isPositive = change !== null && change >= 0;
  const changeColor = change === null
    ? 'var(--color-text-secondary)'
    : isPositive ? 'var(--color-status-ok)' : 'var(--color-status-error)';

  return (
    <div style={{
      background: 'var(--color-bg-card)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-6)',
      boxShadow: 'var(--shadow-sm)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-3)',
      transition: 'box-shadow var(--transition-fast)',
    }}
    onMouseEnter={e => e.currentTarget.style.boxShadow = 'var(--shadow-md)'}
    onMouseLeave={e => e.currentTarget.style.boxShadow = 'var(--shadow-sm)'}
    >
      {/* Header label + icône */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 'var(--weight-semibold)',
          color: 'var(--color-text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}>
          {label}
        </span>
        {icon && (
          <div style={{
            width: 32, height: 32,
            background: 'var(--color-primary-light)',
            borderRadius: 'var(--radius-md)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-primary)',
          }}>
            {icon}
          </div>
        )}
      </div>

      {/* Valeur principale */}
      {loading ? (
        <div style={{
          height: 36,
          background: 'var(--color-bg-page)',
          borderRadius: 'var(--radius-md)',
          animation: 'pulse 1.5s ease-in-out infinite',
        }} />
      ) : (
        <span style={{
          fontSize: 'var(--text-3xl)',
          fontWeight: 'var(--weight-bold)',
          color: 'var(--color-text-primary)',
          fontFamily: 'var(--font-display)',
          lineHeight: 'var(--leading-tight)',
        }}>
          {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
        </span>
      )}

      {/* Variation */}
      {change !== null && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--space-1)',
          color: changeColor,
          fontSize: 'var(--text-sm)',
          fontWeight: 'var(--weight-medium)',
        }}>
          {isPositive ? <ArrowUp /> : <ArrowDown />}
          <span>{Math.abs(change).toFixed(1)}% vs période précédente</span>
        </div>
      )}
    </div>
  );
}
