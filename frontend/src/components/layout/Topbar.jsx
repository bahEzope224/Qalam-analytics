/**
 * Topbar.jsx — Barre supérieure commune à tous les écrans.
 *
 * Contient :
 *   - Titre de la page courante
 *   - Sélecteur de période (7 / 30 / 90 jours)
 *   - Avatar utilisateur
 *
 * Props :
 *   title    {string}        — titre de la page
 *   period   {7|30|90}       — période sélectionnée
 *   onPeriod {(p: number) => void} — callback changement de période
 */

import React from 'react';

const PERIODS = [
  { value: 7,  label: '7 j' },
  { value: 30, label: '30 j' },
  { value: 90, label: '90 j' },
];

export default function Topbar({ title = '', period = 30, onPeriod }) {
  return (
    <header style={{
      height: 'var(--topbar-height)',
      background: 'var(--color-bg-card)',
      borderBottom: '1px solid var(--color-border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 var(--space-8)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: 'var(--shadow-sm)',
    }}>
      {/* Titre */}
      <h1 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-xl)',
        fontWeight: 'var(--weight-bold)',
        color: 'var(--color-text-primary)',
        margin: 0,
      }}>
        {title}
      </h1>

      {/* Actions droite */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        {/* Sélecteur de période */}
        {onPeriod && (
          <div style={{
            display: 'flex',
            gap: 'var(--space-2)',
            alignItems: 'center',
            marginRight: 'var(--space-4)',
          }}>
            {PERIODS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => onPeriod(value)}
                style={{
                  padding: 'var(--space-2) var(--space-4)',
                  borderRadius: '4px',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 'var(--text-sm)',
                  fontWeight: period === value ? 'var(--weight-medium)' : 'var(--weight-regular)',
                  color: period === value ? '#fff' : 'var(--color-text-secondary)',
                  background: period === value ? '#000' : 'transparent',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {label}
              </button>
            ))}
            {/* Icone calendrier */}
            <div style={{ color: 'var(--color-text-secondary)', cursor: 'pointer', marginLeft: 'var(--space-2)' }}>
              📅
            </div>
          </div>
        )}

        {/* Avatar utilisateur */}
        <div style={{
          width: 36, height: 36,
          borderRadius: 'var(--radius-full)',
          background: 'var(--color-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff',
          fontSize: 'var(--text-sm)',
          fontWeight: 'var(--weight-bold)',
          cursor: 'pointer',
          userSelect: 'none',
        }}>
          IB
        </div>
      </div>
    </header>
  );
}
