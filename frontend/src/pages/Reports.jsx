/**
 * Reports.jsx — Écran Rapports (hors scope validé).
 *
 * Affiché dans la navigation mais non développé sans validation d'Ayoub.
 * Affiche un placeholder informatif.
 */

import React from 'react';
import Topbar from '../components/layout/Topbar';

export default function Reports() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar title="Rapports" />

      <main style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-12)',
        gap: 'var(--space-4)',
      }}>
        {/* Icône */}
        <div style={{
          width: 72, height: 72,
          background: 'var(--color-primary-light)',
          borderRadius: 'var(--radius-xl)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--color-primary)',
        }}>
          <svg width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0120 9.414V19a2 2 0 01-2 2z" />
          </svg>
        </div>

        <div style={{ textAlign: 'center', maxWidth: 420 }}>
          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'var(--text-2xl)',
            fontWeight: 'var(--weight-bold)',
            color: 'var(--color-text-primary)',
            margin: '0 0 var(--space-2)',
          }}>
            Rapports — Bientôt disponible
          </h2>
          <p style={{
            fontSize: 'var(--text-base)',
            color: 'var(--color-text-secondary)',
            lineHeight: 'var(--leading-normal)',
            margin: 0,
          }}>
            Cet écran est en cours de conception. Il permettra la génération de rapports synthétiques
            avec export PDF. Validation requise avant développement.
          </p>
        </div>
      </main>
    </div>
  );
}
