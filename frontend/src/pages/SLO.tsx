import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SLOData } from '../types';

const fmt = (n: number | null | undefined, decimals = 1) =>
  n != null ? Number(n).toFixed(decimals) : '—';

const Stat: React.FC<{ label: string; value: string; sub?: string; ok?: boolean }> = ({ label, value, sub, ok }) => (
  <div style={{
    background: '#1a1a1a',
    border: '1px solid #333333',
    borderRadius: 6,
    padding: '1.1rem 1.4rem',
    minWidth: 160,
  }}>
    <div style={{ fontSize: 11, color: '#808080', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
    <div style={{ fontSize: 26, fontWeight: 700, color: ok === false ? '#ef4444' : ok === true ? '#10b981' : '#f0f0f0', fontVariantNumeric: 'tabular-nums' }}>
      {value}
    </div>
    {sub && <div style={{ fontSize: 11, color: '#606060', marginTop: 5 }}>{sub}</div>}
  </div>
);

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <section style={{ marginBottom: '1.75rem' }}>
    <div style={{ fontSize: 11, color: '#606060', marginBottom: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: '1px solid #222', paddingBottom: 6 }}>
      {title}
    </div>
    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      {children}
    </div>
  </section>
);

export const SLOPage: React.FC = () => {
  const [slo, setSlo] = useState<SLOData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = () => {
    setError(false);
    api.getSLO().then(d => {
      if (d) { setSlo(d); setError(false); }
      else setError(true);
      setLoading(false);
    }).catch(() => { setError(true); setLoading(false); });
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  if (loading) return (
    <div style={{ padding: '2rem', color: '#808080', background: '#0f0f0f', minHeight: '100%' }}>
      Loading SLO data...
    </div>
  );

  if (error || !slo) return (
    <div style={{ padding: '2rem', background: '#0f0f0f', minHeight: '100%' }}>
      <div style={{ color: '#ef4444', marginBottom: 12 }}>Failed to load SLO data.</div>
      <button
        onClick={load}
        style={{ background: '#1a1a1a', border: '1px solid #333', color: '#f0f0f0', padding: '6px 14px', borderRadius: 4, cursor: 'pointer', fontSize: 13 }}
      >
        Retry
      </button>
    </div>
  );

  const budget = slo.error_budget;
  const budgetOk = (budget?.error_budget_remaining_percent ?? 0) > 0.5;

  return (
    <div style={{ padding: '2rem', color: '#f0f0f0', background: '#0f0f0f', minHeight: '100%' }}>
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Service Level Objectives</div>
        <div style={{ color: '#606060', fontSize: 13 }}>
          Target: {fmt(budget?.slo_target_percent, 1)}% availability &mdash; auto-refreshes every 30s
        </div>
      </div>

      <Section title="Availability">
        <Stat
          label="Availability"
          value={`${fmt(slo.availability_percent)}%`}
          sub={`${slo.resolved ?? 0} / ${slo.total_incidents ?? 0} incidents resolved`}
          ok={(slo.availability_percent ?? 0) >= (budget?.slo_target_percent ?? 99.9)}
        />
        <Stat
          label="Error Budget Used"
          value={`${fmt(budget?.error_budget_used_percent, 3)}%`}
          sub={`${fmt(budget?.error_budget_remaining_percent, 3)}% remaining`}
          ok={budgetOk}
        />
      </Section>

      <Section title="Response Times">
        <Stat label="MTTR (avg)" value={`${fmt(slo.mttr_seconds)}s`} sub={`min ${fmt(slo.mttr_min_seconds)}s / max ${fmt(slo.mttr_max_seconds)}s`} />
        <Stat label="Detection Latency" value={`${fmt(slo.avg_detection_latency_seconds)}s`} sub="avg time to detect" />
      </Section>

      <Section title="Remediation">
        <Stat
          label="Remediation Success"
          value={`${fmt(slo.remediation_success_rate)}%`}
          sub={`${slo.successful ?? 0} / ${slo.total_verifications ?? 0} verified`}
          ok={(slo.remediation_success_rate ?? 0) >= 70}
        />
      </Section>
    </div>
  );
};
