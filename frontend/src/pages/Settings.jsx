/**
 * Settings.jsx — Configuration de l'intégration GA4.
 *
 * Endpoints :
 *   GET  /api/settings/ga4  — charger la config actuelle
 *   POST /api/settings/ga4  — enregistrer la config
 *
 * Affiche :
 *   - Statut de connexion GA4
 *   - Champ de saisie du chemin vers le fichier de compte de service
 *   - Tableau des sites avec leur propriété GA4 et statut de sync
 */

import React, { useState, useEffect } from 'react';
import Topbar from '../components/layout/Topbar';
import StatusBadge from '../components/badges/StatusBadge';
import DataTable from '../components/tables/DataTable';
import { useApi } from '../hooks/useApi';
import { fetchGA4Settings, saveGA4Settings, fetchSettingsSites, deleteSite, updateSite } from '../services/api';

export default function Settings() {
  const { data: ga4Data, loading: ga4Loading, refetch: refetchGA4 } = useApi(fetchGA4Settings, []);
  const { data: sitesData, loading: sitesLoading, refetch: refetchSites } = useApi(fetchSettingsSites, []);

  const [credJson, setCredJson] = useState('');
  const [saving, setSaving]     = useState(false);
  const [saveMsg, setSaveMsg]   = useState(null);

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingSite, setEditingSite]     = useState(null);
  const [isUpdating, setIsUpdating]       = useState(false);

  const SITES_COLUMNS = [
    { key: 'name',            label: 'Site' },
    { key: 'ga4_property_id', label: 'Propriété GA4' },
    { key: 'last_synced_at',  label: 'Dernière sync', render: v => v ? new Date(v).toLocaleString('fr-FR') : '—' },
    { key: 'status',          label: 'Statut',        render: v => {
        let statusColor = 'ok';
        let statusLabel = 'Sain';
        if (v === 'offline') { statusColor = 'error'; statusLabel = 'Hors ligne'; }
        else if (v === 'warning') { statusColor = 'warn'; statusLabel = 'À réviser'; }
        else if (v === 'error') { statusColor = 'error'; statusLabel = 'Erreur'; }
        
        return <StatusBadge status={statusColor} label={statusLabel} />;
      }
    },
    { key: 'actions',         label: 'Actions',       render: (_, row) => (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => handleOpenEdit(row)}
            style={{
              background: 'var(--color-bg-page)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              cursor: 'pointer'
            }}
          >
            Modifier GA4
          </button>
          <button
            onClick={() => handleDelete(row.id)}
            style={{
              background: 'var(--color-status-error-bg)',
              color: 'var(--color-status-error)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              padding: '4px 8px',
              cursor: 'pointer'
            }}
          >
            Supprimer
          </button>
        </div>
      )
    },
  ];

  function handleOpenEdit(site) {
    setEditingSite({ ...site });
    setEditModalOpen(true);
  }

  async function handleUpdateSite(e) {
    e.preventDefault();
    setIsUpdating(true);
    try {
      await updateSite(editingSite.id, {
        name: editingSite.name,
        url: editingSite.url,
        ga4_property_id: editingSite.ga4_property_id,
      });
      setEditModalOpen(false);
      refetchSites();
    } catch (err) {
      alert(`Erreur de modification : ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setSaveMsg(null);
    try {
      await saveGA4Settings({ credentials_json: credJson });
      setSaveMsg({ type: 'ok', text: 'Configuration enregistrée avec succès.' });
      setCredJson(''); // On vide pour la sécurité
      refetchGA4();
    } catch (err) {
      setSaveMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(siteId) {
    if (!window.confirm("Voulez-vous vraiment supprimer ce site ? Toutes ses données seront perdues.")) return;
    try {
      await deleteSite(siteId);
      refetchSites();
    } catch (err) {
      alert(`Erreur de suppression : ${err.message}`);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Topbar title="Paramètres" />

      <main style={{ padding: 'var(--space-8)', flex: 1, maxWidth: 900 }}>
        {/* --- Connexion GA4 --- */}
        <section style={{
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)',
          marginBottom: 'var(--space-6)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: 'var(--text-lg)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)' }}>
                Connexion API Google Analytics 4
              </h2>
              <p style={{ margin: '4px 0 0', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>
                Compte de service Google (fichier JSON chiffré en BDD)
              </p>
            </div>
            {ga4Data && (
              <StatusBadge
                status={ga4Data.connected ? 'ok' : 'error'}
                label={ga4Data.connected ? 'Connecté' : 'Non configuré'}
              />
            )}
          </div>

          {/* Métadonnées de connexion */}
          {ga4Data && (
            <dl style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              gap: 'var(--space-2) var(--space-6)',
              fontSize: 'var(--text-sm)',
              marginBottom: 'var(--space-6)',
            }}>
              <dt style={{ color: 'var(--color-text-secondary)', fontWeight: 'var(--weight-medium)' }}>Source actuelle</dt>
              <dd style={{ margin: 0, color: 'var(--color-text-primary)' }}>
                {ga4Data.source === 'database' ? 'Base de données (chiffré)' : (ga4Data.source === 'file' ? 'Fichier de credentials' : 'Aucune')}
              </dd>
            </dl>
          )}

          {/* Formulaire de mise à jour */}
          <form onSubmit={handleSave}>
            <label style={{ display: 'block', marginBottom: 'var(--space-2)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)', color: 'var(--color-text-primary)' }}>
              Contenu du fichier JSON du compte de service
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <textarea
                value={credJson}
                onChange={e => setCredJson(e.target.value)}
                placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}'
                rows={6}
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--text-sm)',
                  fontFamily: 'monospace',
                  outline: 'none',
                  resize: 'vertical',
                  transition: 'border-color var(--transition-fast)',
                }}
                onFocus={e => e.target.style.borderColor = 'var(--color-primary)'}
                onBlur={e  => e.target.style.borderColor = 'var(--color-border)'}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  disabled={saving || !credJson}
                  style={{
                    padding: 'var(--space-3) var(--space-6)',
                    background: saving || !credJson ? 'var(--color-border)' : 'var(--color-primary)',
                    color: saving || !credJson ? 'var(--color-text-secondary)' : '#fff',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--text-sm)',
                    fontWeight: 'var(--weight-semibold)',
                    cursor: saving || !credJson ? 'not-allowed' : 'pointer',
                    transition: 'background var(--transition-fast)',
                  }}
                >
                  {saving ? 'Enregistrement…' : 'Enregistrer (Chiffrement automatique)'}
                </button>
              </div>
            </div>

            {saveMsg && (
              <p style={{
                marginTop: 'var(--space-3)',
                fontSize: 'var(--text-sm)',
                color: saveMsg.type === 'ok' ? 'var(--color-status-ok)' : 'var(--color-status-error)',
              }}>
                {saveMsg.text}
              </p>
            )}
          </form>
        </section>

        {/* --- Sites --- */}
        <section style={{
          background: 'var(--color-bg-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-6)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <h2 style={{ margin: '0 0 var(--space-4)', fontSize: 'var(--text-lg)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text-primary)' }}>
            Sites gérés
          </h2>
          <DataTable
            columns={SITES_COLUMNS}
            rows={sitesData ?? []}
            loading={sitesLoading}
            emptyMsg="Aucun site configuré"
          />
        </section>

        {/* Modal Modification Site */}
        {editModalOpen && editingSite && (
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
            <form onSubmit={handleUpdateSite} style={{
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
              <h3 style={{ margin: 0, color: 'var(--color-text-primary)' }}>Modifier le site</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                <label style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>Nom du site</label>
                <input 
                  type="text" 
                  required
                  value={editingSite.name}
                  onChange={e => setEditingSite({...editingSite, name: e.target.value})}
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
                  value={editingSite.url}
                  onChange={e => setEditingSite({...editingSite, url: e.target.value})}
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
                  value={editingSite.ga4_property_id}
                  onChange={e => setEditingSite({...editingSite, ga4_property_id: e.target.value})}
                  style={{
                    padding: 'var(--space-2)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)',
                    background: 'var(--color-bg-body)', color: 'var(--color-text-primary)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                <button 
                  type="button" 
                  onClick={() => setEditModalOpen(false)}
                  style={{
                    background: 'transparent', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)',
                    padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                  }}
                >
                  Annuler
                </button>
                <button 
                  type="submit" 
                  disabled={isUpdating}
                  style={{
                    background: 'var(--color-primary)', border: 'none', color: 'white',
                    padding: 'var(--space-2) var(--space-4)', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                    opacity: isUpdating ? 0.7 : 1,
                  }}
                >
                  {isUpdating ? 'Modification...' : 'Modifier'}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}
