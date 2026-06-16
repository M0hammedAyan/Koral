import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SLOData } from '../types';

const fmt = (n: number, decimals = 1) => n.toFixed(decimals);

const Stat: React.FC<{ label: string; value: string; sub?: string; ok?: boolean }> = ({ label, value, sub, ok }) => (
  <div style={{ background: '#1e293b', borderRadius: 8, padding: '1.2rem 1.5rem', minWidth: 160 }}>
    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: ok === false ? '#f87171' : ok === true ? '#4ade80' : '#e2e8f0' }}>
      {value}
    </div>
    {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>{sub}</div>}
  </div>
);

export const SLOPage: React.FC = () => {
  const [slo, setSlo] = useState<SLOData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSLO().then(d => { setSlo(d); setLoading(false); });
    const t = setInterval(() => api.getSLO().then(setSlo), 30000);
    return () => clearInterval(t);
  }, []);

  if (loading) return <div style={{ padding: '2rem', color: '#94a3b8' }}>Loading SLO data...</div>;
  if (!slo) return <div style={{ padding: '2rem', color: '#f87171' }}>Failed to load SLO data.</div>;

  const budgetOk = slo.error_budget.error_budget_remaining_percent > 0.5;

  return (
    <div style={{ padding: '2rem', color: '#e2e8f0' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: '0.25rem' }}>Service Level Objectives</h1>
      <p style={{ color: '#64748b', marginBottom: '2rem', fontSize: 14 }}>
        Target: {fmt(slo.error_budget.slo_target_percent, 1)}% availability
      </p>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: 14, color: '#94a3b8', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Availability
        </h2>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Stat
            label="Availability"
            value={`${fmt(slo.availability_percent)}%`}
            sub={`${slo.resolved}/${slo.total_incidents} incidents resolved`}
            ok={slo.availability_percent >= slo.error_budget.slo_target_percent}
          />
          <Stat
            label="Error Budget Used"
            value={`${fmt(slo.error_budget.error_budget_used_percent, 3)}%`}
            sub={`${fmt(slo.error_budget.error_budget_remaining_percent, 3)}% remaining`}
            ok={budgetOk}
          />
        </div>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: 14, color: '#94a3b8', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Response Times
        </h2>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Stat label="MTTR (avg)" value={`${fmt(slo.mttr_seconds)}s`} sub={`min ${fmt(slo.mttr_min_seconds)}s / max ${fmt(slo.mttr_max_seconds)}s`} />
          <Stat label="Detection Latency" value={`${fmt(slo.avg_detection_latency_seconds)}s`} sub="avg time to detect" />
        </div>
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: 14, color: '#94a3b8', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: 1 }}>
          Remediation
        </h2>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Stat
            label="Remediation Success"
            value={`${fmt(slo.remediation_success_rate)}%`}
            sub={`${slo.successful}/${slo.total_verifications} verified`}
            ok={slo.remediation_success_rate >= 70}
          />
        </div>
      </section>

      <div style={{ fontSize: 12, color: '#475569', marginTop: '2rem' }}>
        Auto-refreshes every 30s
      </div>
    </div>
  );
};
