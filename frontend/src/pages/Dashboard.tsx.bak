import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/KPICard';
import { IncidentCard } from '../components/IncidentCard';
import { AIAssistant } from '../components/AIAssistant';
import { api, wsService } from '../services/api';
import { Incident, Anomaly } from '../types';
import '../styles/Dashboard.css';

interface ChartPoint {
  timestamp: number;
  value: number;
  z_score: number;
  anomaly: boolean;
}

// ── Live clock ────────────────────────────────────────────────────────
function useLiveClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return time;
}

export const Dashboard: React.FC = () => {
  const [incidents, setIncidents]     = useState<Incident[]>([]);
  const [anomalies, setAnomalies]     = useState<Anomaly[]>([]);
  const [cpuData, setCpuData]         = useState<ChartPoint[]>([]);
  const [memoryData, setMemoryData]   = useState<ChartPoint[]>([]);
  const [storageData, setStorageData] = useState<ChartPoint[]>([]);
  const [wsStatus, setWsStatus]       = useState<'connecting' | 'live' | 'reconnecting'>('connecting');
  const [lastUpdate, setLastUpdate]   = useState<Date | null>(null);
  const [showInfo, setShowInfo]       = useState<'anomaly' | 'incident' | null>(null);
  const anomaliesRef = useRef<Anomaly[]>([]);
  const now = useLiveClock();

  // Keep ref in sync so WebSocket handler always has latest anomalies
  useEffect(() => { anomaliesRef.current = anomalies; }, [anomalies]);

  const buildCharts = useCallback((data: Anomaly[]) => {
    const toPoints = (metric: string): ChartPoint[] =>
      data
        .filter(a => a?.metric === metric)
        .slice(-40)
        .map(a => ({
          timestamp: a.timestamp,
          value: parseFloat(a.value.toFixed(2)),
          z_score: parseFloat(a.z_score.toFixed(2)),
          anomaly: a.is_anomaly,
        }));

    setCpuData(toPoints('cpu'));
    setMemoryData(toPoints('memory'));
    setStorageData([
      ...data.filter(a => a?.metric === 'storage' || a?.metric === 'pvc_io').slice(-20),
      ...data.filter(a => a?.metric === 'logs'    || a?.metric === 'log_error').slice(-20),
    ]
      .sort((a, b) => a.timestamp - b.timestamp)
      .map(a => ({
        timestamp: a.timestamp,
        value: parseFloat(a.value.toFixed(2)),
        z_score: parseFloat(a.z_score.toFixed(2)),
        anomaly: a.is_anomaly,
      })));
  }, []);

  // Initial load
  const loadData = useCallback(async () => {
    const [inc, anoms] = await Promise.all([api.getIncidents(), api.getAnomalies()]);
    setIncidents(inc);
    setAnomalies(anoms);
    buildCharts(anoms);
    setLastUpdate(new Date());
  }, [buildCharts]);

  // WebSocket — drives ALL live updates, no polling needed
  useEffect(() => {
    loadData();

    wsService.connect(
      () => setWsStatus('live'),
      () => setWsStatus('reconnecting'),
    );

    wsService.subscribe((msg: any) => {
      if (!msg?.type || !msg?.payload) return;

      if (msg.type === 'anomaly') {
        setAnomalies(prev => {
          const updated = [...prev, msg.payload];
          buildCharts(updated);
          return updated;
        });
        setLastUpdate(new Date());
      }

      if (msg.type === 'incident' || msg.type === 'incident_ai') {
        setIncidents(prev => {
          const idx = prev.findIndex(i => i.incident_id === msg.payload.incident_id);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { ...updated[idx], ...msg.payload };
            return updated;
          }
          return [msg.payload, ...prev];
        });
        setLastUpdate(new Date());
      }
    });

    // Fallback poll every 30s only (WebSocket handles real-time)
    const interval = setInterval(loadData, 30000);
    return () => { clearInterval(interval); wsService.disconnect(); };
  }, [loadData, buildCharts]);

  // KPIs
  const latestCpu       = anomalies.filter(a => a?.metric === 'cpu').slice(-1)[0];
  const latestMem       = anomalies.filter(a => a?.metric === 'memory').slice(-1)[0];
  const totalAlerts     = anomalies.filter(a => a?.is_anomaly).length;
  const cpuVal          = latestCpu ? parseFloat(latestCpu.value.toFixed(1)) : 0;
  const memVal          = latestMem ? parseFloat(latestMem.value.toFixed(0)) : 0;
  const activeAnomalies = anomalies.filter(a => a?.is_anomaly);

  const chartTooltipStyle = { backgroundColor: '#1a1a1a', border: '1px solid #333', color: '#e0e0e0' };

  const AnomalyDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload?.anomaly) return null;
    return <circle cx={cx} cy={cy} r={5} fill="#ff6b6b" stroke="#fff" strokeWidth={1} />;
  };

  const formatLastUpdate = () => {
    if (!lastUpdate) return 'Never';
    const diff = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);
    if (diff < 5)  return 'Just now';
    if (diff < 60) return `${diff}s ago`;
    return `${Math.floor(diff / 60)}m ago`;
  };

  return (
    <div className="dashboard">

      {/* ── TOP BAR: live status + clock ── */}
      <div className="dashboard-topbar">
        <div className="live-status">
          <span className={`live-dot ${wsStatus}`}></span>
          <span className="live-label">
            {wsStatus === 'live' ? 'LIVE' : wsStatus === 'reconnecting' ? 'RECONNECTING...' : 'CONNECTING...'}
          </span>
          {lastUpdate && (
            <span className="last-update">Updated {formatLastUpdate()}</span>
          )}
        </div>
        <div className="live-clock">
          {now.toLocaleTimeString()} &nbsp;·&nbsp; {now.toLocaleDateString()}
        </div>
      </div>

      {/* ── ANOMALY BANNER ── */}
      {activeAnomalies.length > 0 && (
        <div className="anomaly-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <strong>{activeAnomalies.length} anomal{activeAnomalies.length > 1 ? 'ies' : 'y'} detected</strong>
          <span className="banner-sep">—</span>
          {activeAnomalies.slice(-3).map(a => (
            <span key={`${a.pod}-${a.timestamp}`} className="anomaly-tag">
              {a.pod} · {a.metric} · z={a.z_score.toFixed(2)}
            </span>
          ))}
          <button className="info-btn" onClick={() => setShowInfo(showInfo === 'anomaly' ? null : 'anomaly')}>
            What is this?
          </button>
        </div>
      )}

      {/* ── INLINE EXPLANATION PANELS ── */}
      {showInfo === 'anomaly' && (
        <div className="info-panel anomaly-info">
          <button className="info-close" onClick={() => setShowInfo(null)}>x</button>
          <h4>What is an Anomaly?</h4>
          <p>
            An <strong>anomaly</strong> is when a metric (CPU, memory, storage, logs) behaves
            significantly differently from its recent normal pattern.
          </p>
          <p>
            KORAL measures this using a <strong>z-score</strong> — how many standard deviations
            the current value is from the average of the last 30 readings.
            A z-score above <strong>2.5</strong> means the value is unusually high or low.
          </p>
          <div className="info-example">
            <span className="info-example-label">Example:</span>
            CPU normally runs at 50%. Suddenly it hits 95%.
            Z-score = 4.2 → flagged as anomaly → red dot appears on chart.
          </div>
          <p className="info-note">
            An anomaly is a <strong>signal</strong>. It does not always mean something is broken —
            it means something unusual happened and needs attention.
          </p>
        </div>
      )}

      {showInfo === 'incident' && (
        <div className="info-panel incident-info">
          <button className="info-close" onClick={() => setShowInfo(null)}>x</button>
          <h4>What is an Incident?</h4>
          <p>
            An <strong>incident</strong> is created when the AI correlation engine analyses an anomaly
            and determines its <strong>root cause</strong>.
          </p>
          <p>
            While an anomaly just says "something is wrong", an incident says
            <strong> what</strong> is wrong, <strong>why</strong> it happened,
            and <strong>which pods</strong> are affected.
          </p>
          <div className="info-example">
            <span className="info-example-label">Example:</span>
            Anomaly: CPU spike on pod-A (z=4.2)<br />
            Incident: "CPU Saturation — pod-A is consuming 98% CPU due to a runaway process.
            Confidence: 84%. Action: check for infinite loops or scale the deployment."
          </div>
          <div className="info-severity">
            <span className="sev critical">CRITICAL</span> Immediate action required — developer alerted<br />
            <span className="sev high">HIGH</span> Needs attention soon — AI explains and recommends<br />
            <span className="sev medium">MEDIUM</span> AI auto-handles and reports what it did<br />
            <span className="sev low">LOW</span> Informational — monitored automatically
          </div>
        </div>
      )}

      {/* ── KPI CARDS ── */}
      <div className="kpi-section">
        <KPICard title="CPU Usage"       value={cpuVal} unit="%"
          severity={cpuVal > 80 ? 'critical' : cpuVal > 60 ? 'warning' : 'normal'}
          trend={latestCpu?.is_anomaly ? 'up' : 'stable'} />
        <KPICard title="Memory Usage"    value={memVal} unit=" MB"
          severity={memVal > 400 ? 'critical' : memVal > 300 ? 'warning' : 'normal'}
          trend={latestMem?.is_anomaly ? 'up' : 'stable'} />
        <KPICard title="Active Incidents" value={incidents.length}
          severity={incidents.length > 0 ? 'critical' : 'normal'} />
        <KPICard title="Total Anomalies" value={totalAlerts}
          severity={totalAlerts > 5 ? 'critical' : totalAlerts > 0 ? 'warning' : 'normal'}
          trend={totalAlerts > 0 ? 'up' : 'stable'} />
      </div>

      {/* ── MAIN GRID ── */}
      <div className="content-grid">

        {/* Charts */}
        <div className="charts-section">

          <div className="chart-container">
            <div className="chart-header">
              <h3>CPU Usage <span className="chart-unit">(%)</span>
                {latestCpu?.is_anomaly && <span className="chart-alert-badge">ANOMALY</span>}
              </h3>
              <span className="chart-live-badge">LIVE</span>
            </div>
            {cpuData.length === 0
              ? <div className="chart-empty">Waiting for data...</div>
              : (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={cpuData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={40} domain={[0, 100]} />
                    <Tooltip contentStyle={chartTooltipStyle}
                      formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : 'CPU %']}
                      labelFormatter={(l) => new Date(l * 1000).toLocaleTimeString()} />
                    <Line type="monotone" dataKey="value"   stroke="#00d4ff" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#444"    strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            <div className="chart-legend">
              <span className="legend-line cpu"></span> CPU value &nbsp;&nbsp;
              <span className="legend-line zscore"></span> Z-Score &nbsp;&nbsp;
              <span className="legend-dot-red"></span> Anomaly point
            </div>
          </div>

          <div className="chart-container">
            <div className="chart-header">
              <h3>Memory Usage <span className="chart-unit">(MB)</span>
                {latestMem?.is_anomaly && <span className="chart-alert-badge">ANOMALY</span>}
              </h3>
              <span className="chart-live-badge">LIVE</span>
            </div>
            {memoryData.length === 0
              ? <div className="chart-empty">Waiting for data...</div>
              : (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={memoryData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={50} />
                    <Tooltip contentStyle={chartTooltipStyle}
                      formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : 'Memory MB']}
                      labelFormatter={(l) => new Date(l * 1000).toLocaleTimeString()} />
                    <Line type="monotone" dataKey="value"   stroke="#ff6b6b" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#444"    strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            <div className="chart-legend">
              <span className="legend-line mem"></span> Memory value &nbsp;&nbsp;
              <span className="legend-line zscore"></span> Z-Score &nbsp;&nbsp;
              <span className="legend-dot-red"></span> Anomaly point
            </div>
          </div>

          <div className="chart-container">
            <div className="chart-header">
              <h3>Storage / Logs <span className="chart-unit">(value)</span></h3>
              <span className="chart-live-badge">LIVE</span>
            </div>
            {storageData.length === 0
              ? <div className="chart-empty">Waiting for data...</div>
              : (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={storageData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={40} />
                    <Tooltip contentStyle={chartTooltipStyle}
                      formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : 'Value']}
                      labelFormatter={(l) => new Date(l * 1000).toLocaleTimeString()} />
                    <Line type="monotone" dataKey="value"   stroke="#51cf66" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#444"    strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
          </div>
        </div>

        {/* Incident Feed */}
        <div className="incident-feed">
          <div className="feed-header">
            <h3>Incidents</h3>
            <button className="info-btn" onClick={() => setShowInfo(showInfo === 'incident' ? null : 'incident')}>
              What is an incident?
            </button>
          </div>
          <div className="feed-subtitle">
            Updates automatically — no refresh needed
          </div>
          <div className="incident-list">
            {incidents.length === 0
              ? (
                <div className="no-incidents">
                  <div>No incidents yet</div>
                  <div className="no-incidents-sub">
                    Incidents appear here automatically when the AI detects and analyses an anomaly
                  </div>
                </div>
              )
              : incidents.slice(0, 15).map(inc => (
                  <IncidentCard key={inc.incident_id} incident={inc} />
                ))
            }
          </div>
        </div>

        {/* AI Assistant */}
        <div className="ai-panel">
          <AIAssistant />
        </div>

      </div>
    </div>
  );
};
