/**
 * AcquisitionDonutChart.jsx — Donut chart des sources d'acquisition.
 *
 * Utilise Recharts. Affiche la répartition organic / direct / social / referral.
 *
 * Props :
 *   data    {Object}   — ex. { organic: 45, direct: 25, social: 18, referral: 12 }
 *   loading {boolean}
 */

import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const CHANNEL_LABELS = {
  organic:  'Organique',
  direct:   'Direct',
  social:   'Social',
  referral: 'Référent',
};

const CHANNEL_COLORS = {
  organic:  '#7C3AED',
  direct:   '#10B981',
  social:   '#F59E0B',
  referral: '#6B7280',
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div style={{
      background: 'var(--color-bg-card)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-2) var(--space-3)',
      boxShadow: 'var(--shadow-md)',
    }}>
      <p style={{ margin: 0, fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
        {item.name}
      </p>
      <p style={{ margin: '2px 0 0', fontSize: 'var(--text-sm)', color: item.payload.fill }}>
        {item.value.toFixed(1)} %
      </p>
    </div>
  );
}

function CustomLegend({ payload }) {
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      {payload.map(entry => (
        <li key={entry.value} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: entry.color, flexShrink: 0 }} />
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>{entry.value}</span>
          <span style={{ marginLeft: 'auto', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text-primary)' }}>
            {entry.payload.value.toFixed(1)}%
          </span>
        </li>
      ))}
    </ul>
  );
}

export default function AcquisitionDonutChart({ data = {}, loading = false }) {
  if (loading) {
    return (
      <div style={{
        height: 220,
        background: 'var(--color-bg-page)',
        borderRadius: 'var(--radius-md)',
        animation: 'pulse 1.5s ease-in-out infinite',
      }} />
    );
  }

  const chartData = Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name:  CHANNEL_LABELS[key] ?? key,
      value,
      fill:  CHANNEL_COLORS[key] ?? '#9CA3AF',
    }));

  if (!chartData.length) {
    return (
      <div style={{
        height: 220,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)',
      }}>
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
      <ResponsiveContainer width={160} height={160}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%" cy="50%"
            innerRadius={50}
            outerRadius={75}
            dataKey="value"
            startAngle={90}
            endAngle={-270}
            strokeWidth={0}
          >
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ flex: 1 }}>
        <CustomLegend payload={chartData.map(d => ({ value: d.name, color: d.fill, payload: d }))} />
      </div>
    </div>
  );
}
