/**
 * TrafficLineChart.jsx — Graphique d'évolution du trafic (courbe).
 *
 * Utilise Recharts (à installer via `npm install recharts`).
 * Affiche les sessions par jour sur la période sélectionnée.
 *
 * Props :
 *   data    {Array<{date: string, sessions: number}>}
 *   loading {boolean}
 *   height  {number}   — hauteur du graphique en px (défaut 260)
 */

import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  AreaChart,
} from 'recharts';

// Formatage de la date GA4 "2024-01-15" → "15 jan"
const SHORT_MONTHS = ['jan','fév','mar','avr','mai','jun','jul','aoû','sep','oct','nov','déc'];
function formatDate(dateStr) {
  const [, month, day] = dateStr.split('-');
  return `${parseInt(day)} ${SHORT_MONTHS[parseInt(month) - 1]}`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--color-bg-card)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-3) var(--space-4)',
      boxShadow: 'var(--shadow-md)',
    }}>
      <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
        {formatDate(label)}
      </p>
      <p style={{
        margin: '4px 0 0',
        fontSize: 'var(--text-base)',
        fontWeight: 'var(--weight-bold)',
        color: 'var(--color-text-primary)',
      }}>
        {payload[0].value.toLocaleString('fr-FR')} sessions
      </p>
    </div>
  );
}

export default function TrafficLineChart({ data = [], loading = false, height = 260 }) {
  if (loading) {
    return (
      <div style={{
        height,
        background: 'var(--color-bg-page)',
        borderRadius: 'var(--radius-md)',
        animation: 'pulse 1.5s ease-in-out infinite',
      }} />
    );
  }

  if (!data.length) {
    return (
      <div style={{
        height,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--text-sm)',
      }}>
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="trafficGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#7C3AED" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}    />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="sessions"
          stroke="#7C3AED"
          strokeWidth={2.5}
          fill="url(#trafficGradient)"
          dot={false}
          activeDot={{ r: 5, fill: '#7C3AED', strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
