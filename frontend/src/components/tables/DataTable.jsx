/**
 * DataTable.jsx — Tableau de données générique.
 *
 * Affiche une liste de lignes avec colonnes configurables.
 *
 * Props :
 *   columns  {Array<{key, label, render?}>} — définition des colonnes
 *   rows     {Array<Object>}                 — données
 *   loading  {boolean}
 *   emptyMsg {string}                        — message si vide
 */

import React from 'react';

function SkeletonRow({ cols }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} style={{ padding: 'var(--space-4) var(--space-4)' }}>
          <div style={{
            height: 14,
            background: 'var(--color-bg-page)',
            borderRadius: 'var(--radius-sm)',
            animation: 'pulse 1.5s ease-in-out infinite',
          }} />
        </td>
      ))}
    </tr>
  );
}

export default function DataTable({ columns = [], rows = [], loading = false, emptyMsg = 'Aucune donnée', onRowClick }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontFamily: 'var(--font-primary)',
        fontSize: 'var(--text-sm)',
      }}>
        {/* En-tête */}
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
            {columns.map(col => (
              <th
                key={col.key}
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  textAlign: col.align ?? 'left',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'var(--weight-semibold)',
                  color: 'var(--color-text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  whiteSpace: 'nowrap',
                }}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>

        {/* Corps */}
        <tbody>
          {loading
            ? Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={i} cols={columns.length} />
              ))
            : rows.length === 0
            ? (
              <tr>
                <td
                  colSpan={columns.length}
                  style={{
                    padding: 'var(--space-10)',
                    textAlign: 'center',
                    color: 'var(--color-text-secondary)',
                    fontSize: 'var(--text-sm)',
                  }}
                >
                  {emptyMsg}
                </td>
              </tr>
            )
            : rows.map((row, rowIdx) => (
              <tr
                key={row.id ?? rowIdx}
                onClick={() => onRowClick && onRowClick(row)}
                style={{ 
                  borderBottom: '1px solid var(--color-border)',
                  cursor: onRowClick ? 'pointer' : 'default',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--color-primary-light)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {columns.map(col => (
                  <td
                    key={col.key}
                    style={{
                      padding: 'var(--space-4) var(--space-4)',
                      color: 'var(--color-text-primary)',
                      textAlign: col.align ?? 'left',
                      verticalAlign: 'middle',
                    }}
                  >
                    {col.render ? col.render(row[col.key], row) : row[col.key] ?? '—'}
                  </td>
                ))}
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  );
}
