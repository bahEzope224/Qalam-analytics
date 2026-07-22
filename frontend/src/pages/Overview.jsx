/**
 * Overview.jsx — Vue d'ensemble : grille des 7 sites Qalam.
 *
 * Endpoint : GET /api/sites/overview?period={7|30|90}
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Topbar from '../components/layout/Topbar';
import DataTable from '../components/tables/DataTable';
import StatusBadge from '../components/badges/StatusBadge';
import WWWGlobeIcon from '../components/icons/WWWGlobeIcon';
import { useApi } from '../hooks/useApi';
import { fetchSitesList, addSite } from '../services/api';

export default function Overview() {
  const [period, setPeriod] = useState(30);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newSite, setNewSite] = useState({ name: '', url: 'https://', ga4_property_id: '' });
  const [isAdding, setIsAdding] = useState(false);
  const navigate = useNavigate();

  const { data: sites, loading, error, refresh } = useApi(
    () => fetchSitesList(period),
    [period]
  );

  const OVERVIEW_COLUMNS = [
    { 
      key: 'name', 
      label: 'Site web',
      render: (v) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ 
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            width: 32, height: 32, borderRadius: 'var(--radius-md)', background: 'var(--color-bg-page)',
            color: 'var(--color-text-secondary)'
          }}>
            <WWWGlobeIcon size={20} />
          </span>
          <span style={{ fontWeight: 'var(--weight-medium)', color: 'var(--color-text-primary)' }}>{v}</span>
        </div>
      )
    },
    { 
      key: 'status', 
      label: 'Statut', 
      render: v => <StatusBadge status={v === 'offline' ? 'error' : (v === 'warning' ? 'warning' : 'ok')} label={v === 'offline' ? 'Hors ligne' : (v === 'warning' ? 'À réviser' : 'Sain')} />
    },
    { 
      key: 'total_visits', 
      label: `Visites totales (${period}j)`,
      render: v => v != null ? v.toLocaleString('fr-FR') : '--'
    },
    { 
      key: 'bounce_rate', 
      label: 'Taux de rebond',
      render: v => v != null ? `${(v * 100).toFixed(1)}%` : '--'
    },
    { 
      key: 'avg_session_duration', 
      label: 'Session moyenne',
      render: v => {
        if (v == null) return '--';
        const m = Math.floor(v / 60);
        const s = Math.floor(v % 60);
        return `${m}m ${s.toString().padStart(2, '0')}s`;
      }
    },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (_, row) => (
        <button 
          onClick={(e) => { e.stopPropagation(); navigate(`/sites/${row.id}`); }}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 'var(--text-lg)', color: 'var(--color-text-secondary)', padding: 'var(--space-1) var(--space-2)' }}
        >
          ⋮
        </button>
      )
    }
  ];

  const handleAddSite = async (e) => {
    e.preventDefault();
    setIsAdding(true);
    try {
      const { addSite } = await import('../services/api');
      await addSite(newSite);
      setIsAddModalOpen(false);
      setNewSite({ name: '', url: 'https://', ga4_property_id: '' });
      refresh();
    } catch (err) {
      alert(`Erreur lors de l'ajout : ${err.message}`);
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar
        title="Tableau de bord"
        period={period}
        onPeriod={setPeriod}
      />

      <main style={{ padding: 'var(--space-8)', flex: 1, position: 'relative' }}>
        {/* En-tête de section */}
        <div style={{ 
          marginBottom: 'var(--space-6)', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <div>
            <h2 style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'var(--text-2xl)',
              fontWeight: 'var(--weight-bold)',
              color: 'var(--color-text-primary)',
              margin: '0 0 var(--space-1)',
            }}>
              Sites gérés
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', margin: 0 }}>
              {sites?.length ?? 7} sites · période : {period} derniers jours
            </p>
          </div>
          <button
            onClick={() => setIsAddModalOpen(true)}
            style={{
              background: 'var(--color-primary)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-2) var(--space-4)',
              fontSize: 'var(--text-sm)',
              fontWeight: 'var(--weight-medium)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              transition: 'background 0.2s',
            }}
          >
            <span>+ Ajouter un site</span>
          </button>
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

        {/* Tableau de bord */}
        <div style={{
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <DataTable
            columns={OVERVIEW_COLUMNS}
            rows={sites ?? []}
            loading={loading}
            emptyMsg="Aucun site configuré"
            onRowClick={(row) => navigate(`/sites/${row.id}`)}
          />
        </div>

        {/* Modal Ajout */}
        {isAddModalOpen && (
          <div style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}>
            <form onSubmit={handleAddSite} style={{
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-6)',
              width: '400px',
              maxWidth: '90%',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
            }}>
              <h3 style={{ margin: 0, color: 'var(--color-text-primary)' }}>Ajouter un nouveau site</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                <label style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>Nom du site</label>
                <input 
                  type="text" 
                  required
                  value={newSite.name}
                  onChange={e => setNewSite({...newSite, name: e.target.value})}
                  style={{
                    padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)',
                    background: 'var(--color-bg-body)', color: 'var(--color-text-primary)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                <label style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>URL</label>
                <input 
                  type="url" 
                  required
                  value={newSite.url}
                  onChange={e => setNewSite({...newSite, url: e.target.value})}
                  style={{
                    padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)',
                    background: 'var(--color-bg-body)', color: 'var(--color-text-primary)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                <label style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>Propriété GA4 (ex: 123456789)</label>
                <input 
                  type="text" 
                  required
                  value={newSite.ga4_property_id}
                  onChange={e => setNewSite({...newSite, ga4_property_id: e.target.value})}
                  style={{
                    padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)',
                    background: 'var(--color-bg-body)', color: 'var(--color-text-primary)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button 
                  type="button" 
                  onClick={() => setIsAddModalOpen(false)}
                  style={{
                    background: 'transparent', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)',
                    padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  }}
                >
                  Annuler
                </button>
                <button 
                  type="submit" 
                  disabled={isAdding}
                  style={{
                    background: 'var(--color-primary)', border: 'none', color: 'white',
                    padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                    opacity: isAdding ? 0.7 : 1,
                  }}
                >
                  {isAdding ? 'Ajout...' : 'Ajouter'}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
