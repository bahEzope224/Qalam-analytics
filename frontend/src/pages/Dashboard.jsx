import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Topbar from '../components/layout/Topbar';
import SiteCard from '../components/cards/SiteCard';
import { useApi } from '../hooks/useApi';
import { fetchOverview } from '../services/api';

export default function Dashboard() {
  const [period, setPeriod] = useState(30);
  const [sortBy, setSortBy] = useState('trafic'); // 'trafic' ou 'tendance'
  const navigate = useNavigate();

  const { data: sites, loading, error } = useApi(
    () => fetchOverview(period), // TODO: pass sortBy to API if supported, or sort on client
    [period]
  );

  // Client-side sorting if needed
  const sortedSites = React.useMemo(() => {
    if (!sites) return [];
    const list = [...sites];
    if (sortBy === 'trafic') {
      list.sort((a, b) => (b.total_visits || 0) - (a.total_visits || 0));
    } else if (sortBy === 'tendance') {
      list.sort((a, b) => (b.trend_pct || 0) - (a.trend_pct || 0));
    }
    return list;
  }, [sites, sortBy]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar title="Qalam Analytics" period={period} onPeriod={setPeriod} />

      <main style={{ padding: 'var(--space-8)', flex: 1, position: 'relative' }}>
        {/* En-tête de page */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
          <div>
            <h2 style={{
              fontSize: 'var(--text-3xl)',
              fontWeight: 'var(--weight-bold)',
              color: 'var(--color-text-primary)',
              margin: '0 0 var(--space-1)',
            }}>
              Vue d'ensemble des sites
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', margin: 0 }}>
              Surveillance des performances et de la santé du réseau.
            </p>
          </div>
          
          {/* Toggle de tri */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: 'var(--color-bg-border)', // A adjust
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
          }}>
            <span style={{ padding: 'var(--space-2) var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', background: 'var(--color-bg-page)' }}>
              Trier par :
            </span>
            <button
              onClick={() => setSortBy('trafic')}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-sm)',
                border: 'none',
                background: sortBy === 'trafic' ? 'var(--color-bg-card)' : 'var(--color-border)',
                fontWeight: sortBy === 'trafic' ? 'var(--weight-semibold)' : 'var(--weight-regular)',
                cursor: 'pointer',
              }}
            >
              Trafic
            </button>
            <button
              onClick={() => setSortBy('tendance')}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                fontSize: 'var(--text-sm)',
                border: 'none',
                background: sortBy === 'tendance' ? 'var(--color-bg-card)' : 'var(--color-border)',
                fontWeight: sortBy === 'tendance' ? 'var(--weight-semibold)' : 'var(--weight-regular)',
                cursor: 'pointer',
              }}
            >
              Tendance
            </button>
          </div>
        </div>

        {/* Erreur */}
        {error && (
          <div style={{
            background: 'var(--color-status-error-bg)',
            color: 'var(--color-status-error)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-6)',
            fontSize: 'var(--text-sm)',
          }}>
            ⚠️ Impossible de charger les données : {error}
          </div>
        )}

        {/* Grille de cartes */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 'var(--space-6)',
        }}>
          {loading
            // Squelette : 7 cartes vides pendant le chargement
            ? Array.from({ length: 7 }).map((_, i) => (
                <div key={i} style={{
                  height: 200,
                  background: 'var(--color-bg-card)',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--color-border)',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }} />
              ))
            : sortedSites.map(site => (
                <SiteCard
                  key={site.id}
                  site={site}
                  onClick={() => navigate(`/sites/${site.id}`)}
                />
              ))
          }
        </div>
      </main>
    </div>
  );
}
