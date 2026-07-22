/**
 * SiteDetail.jsx — Vue détaillée d'un site (stretch goal).
 *
 * Endpoint : GET /api/sites/:id?period={7|30|90}
 *
 * Affiche : KPIs clés, graphique de trafic, top pages, donut d'acquisition.
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Topbar from '../components/layout/Topbar';
import StatCard from '../components/cards/StatCard';
import TrafficLineChart from '../components/charts/TrafficLineChart';
import AcquisitionDonutChart from '../components/charts/AcquisitionDonutChart';
import DataTable from '../components/tables/DataTable';
import StatusBadge from '../components/badges/StatusBadge';
import { useApi } from '../hooks/useApi';
import { fetchSiteDetail } from '../services/api';

const PAGES_COLUMNS = [
  { key: 'rank',        label: '#',       align: 'center' },
  { key: 'path',        label: 'Page' },
  { key: 'page_views',  label: 'Vues',    align: 'right',
    render: v => v?.toLocaleString('fr-FR') ?? '—' },
  { key: 'traffic_pct', label: '% trafic', align: 'right',
    render: v => v != null ? `${v}%` : '—' },
];

export default function SiteDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [period, setPeriod] = useState(30);

  const { data, loading, error } = useApi(
    () => fetchSiteDetail(id, period),
    [id, period]
  );

  const kpis     = data?.kpis     ?? {};
  const traffic  = data?.traffic  ?? [];
  const pages    = data?.pages    ?? [];
  const sources  = data?.sources  ?? {};
  const siteName = data?.name     ?? '…';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar title={siteName} period={period} onPeriod={setPeriod} />

      <main style={{ padding: 'var(--space-8)', flex: 1 }}>
        {/* Retour */}
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--color-primary)',
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-medium)',
            marginBottom: 'var(--space-6)',
            padding: 0,
            display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
          }}
        >
          ← Retour à la vue d'ensemble
        </button>

        {error && (
          <div style={{
            background: 'var(--color-status-error-bg)',
            color: 'var(--color-status-error)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-6)',
            fontSize: 'var(--text-sm)',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* KPIs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-8)',
        }}>
          <StatCard label="Visites totales"      value={kpis.sessions}           change={kpis.sessions_change}     loading={loading} />
          <StatCard label="Utilisateurs"         value={kpis.users}              change={kpis.users_change}        loading={loading} />
          <StatCard label="Taux de rebond"       value={kpis.bounce_rate != null ? `${(kpis.bounce_rate * 100).toFixed(1)}%` : '—'} loading={loading} />
          <StatCard label="Durée moy. session"   value={kpis.avg_session_duration != null ? formatDuration(kpis.avg_session_duration) : '—'} loading={loading} />
        </div>

        {/* Graphiques */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: 'var(--space-6)',
          marginBottom: 'var(--space-8)',
        }}>
          {/* Trafic */}
          <div style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <h3 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-base)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
              Évolution du trafic
            </h3>
            <TrafficLineChart data={traffic} loading={loading} />
          </div>

          {/* Sources d'acquisition */}
          <div style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-6)',
            boxShadow: 'var(--shadow-sm)',
          }}>
            <h3 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-base)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
              Sources d'acquisition
            </h3>
            <AcquisitionDonutChart data={sources} loading={loading} />
          </div>
        </div>

        {/* Top pages */}
        <div style={{
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <h3 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-base)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
            Pages les plus visitées
          </h3>
          <DataTable columns={PAGES_COLUMNS} rows={pages} loading={loading} emptyMsg="Aucune page à afficher" />
        </div>
      </main>
    </div>
  );
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s.toString().padStart(2, '0')}s`;
}
