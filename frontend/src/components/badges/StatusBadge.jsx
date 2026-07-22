/**
 * StatusBadge.jsx — Pastille colorée indiquant l'état d'un site ou d'un service.
 *
 * Props :
 *   status  {'ok' | 'warn' | 'error'}
 *   label   {string|null}  — texte personnalisé (sinon utilise le label par défaut)
 *   size    {'sm' | 'md'}
 */

import React from 'react';

const STATUS_CONFIG = {
  ok: {
    label: 'Sain',
    color: 'var(--color-status-ok)',
    bg:    'var(--color-status-ok-bg)',
  },
  warn: {
    label: 'Attention',
    color: 'var(--color-status-warn)',
    bg:    'var(--color-status-warn-bg)',
  },
  error: {
    label: 'Erreur',
    color: 'var(--color-status-error)',
    bg:    'var(--color-status-error-bg)',
  },
};

export default function StatusBadge({ status = 'ok', label = null, size = 'md' }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.ok;
  const text   = label ?? config.label;

  const fontSize = size === 'sm' ? 'var(--text-xs)' : 'var(--text-xs)';
  const padding  = size === 'sm' ? '2px 8px' : '3px 10px';

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding,
      borderRadius: 'var(--radius-full)',
      background: config.bg,
      color: config.color,
      fontSize,
      fontWeight: 'var(--weight-semibold)',
      whiteSpace: 'nowrap',
      lineHeight: 1.6,
    }}>
      {/* Pastille */}
      <span style={{
        width: 7, height: 7,
        borderRadius: '50%',
        background: config.color,
        flexShrink: 0,
      }} />
      {text}
    </span>
  );
}
