/**
 * App.jsx — Racine de l'application.
 *
 * Définit le layout principal (Sidebar + contenu) et le routage.
 * Importe les tokens CSS globaux.
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Dashboard  from './pages/Dashboard';
import Overview   from './pages/Overview';
import SiteDetail from './pages/SiteDetail';
import Reports    from './pages/Reports';
import Settings   from './pages/Settings';
import './styles/tokens.css';

// Styles globaux inline (reset minimal + animation pulse)
const globalStyle = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--font-primary);
    background: var(--color-bg-page);
    color: var(--color-text-primary);
    -webkit-font-smoothing: antialiased;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
`;

export default function App() {
  return (
    <BrowserRouter>
      {/* Injection styles globaux */}
      <style>{globalStyle}</style>

      <div style={{ display: 'flex', minHeight: '100vh' }}>
        {/* Sidebar fixe */}
        <Sidebar />

        {/* Contenu principal décalé de la largeur de la sidebar */}
        <div style={{
          marginLeft: 'var(--sidebar-width)',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
        }}>
          <Routes>
            <Route path="/"              element={<Dashboard />}  />
            <Route path="/sites/:id"     element={<SiteDetail />} />
            <Route path="/sites"         element={<Overview />}   />
            <Route path="/rapports"      element={<Reports />}    />
            <Route path="/parametres"    element={<Settings />}   />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
