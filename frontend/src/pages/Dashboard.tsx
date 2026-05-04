import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceDot } from 'recharts';
import { KPICard } from '../components/KPICard';
import { IncidentCard } from '../components/IncidentCard';
import { api, wsService } from '../services/api';
import { Incident, Anomaly } from '../types';
import '../styles/Dashboard.css';

interface ChartPoint {
  timestamp: number;
  value: number;
  z_score: number;
  anomaly: boolean;
}

export const Dashboard: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [cpuData, setCpuData] = useState<ChartPoint[]>([]);
  const [memoryData, setMemoryData] = useState<ChartPoint[]>([]);
  const [storageData, setStorageData] = useState<ChartPoint[]>([]);

  const buildCharts = useCallback((data: Anomaly[]) => {
    const toPoints = (metric: string): ChartPoint[] =>
      data
        .filter(a => a?.metric === metric)
        .slice(-30)
        .map(a => ({
          timestamp: a.timestamp,
          value: parseFloat(a.value.toFixed(2)),
          z_score: parseFloat(a.z_score.toFixed(2)),
          anomaly: a.is_anomaly,
        }));

    setCpuData(toPoints('cpu'));
    setMemoryData(toPoints('memory'));
    setStorageData([
      ...data.filter(a => a?.metric === 'storage').slice(-15),
      ...data.filter(a => a?.metric === 'logs').slice(-15),
    ]
      .sort((a, b) => a.timestamp - b.timestamp)
      .map(a => ({
        timestamp: a.timestamp,
        value: parseFloat(a.value.toFixed(2)),
        z_score: parseFloat(a.z_score.toFixed(2)),
        anomaly: a.is_anomaly,
      })));
  }, []);

  const loadData = useCallback(async () => {
    const [inc, anoms] = await Promise.all([api.getIncidents(), api.getAnomalies()]);
    setIncidents(inc);
    setAnomalies(anoms);
    buildCharts(anoms);
  }, [buildCharts]);

  useEffect(() => {
    loadData();
    wsService.connect();
    wsService.subscribe((msg: any) => {
      if (!msg?.type || !msg?.payload) return;
      if (msg.type === 'incident') setIncidents(prev => [msg.payload, ...prev]);
      if (msg.type === 'anomaly') {
        setAnomalies(prev => {
          const updated = [...prev, msg.payload];
          buildCharts(updated);
          return updated;
        });
      }
    });
    const interval = setInterval(loadData, 10000);
    return () => { clearInterval(interval); wsService.disconnect(); };
  }, [loadData, buildCharts]);

  // KPIs from latest values
  const latestCpu    = anomalies.filter(a => a?.metric === 'cpu').slice(-1)[0];
  const latestMem    = anomalies.filter(a => a?.metric === 'memory').slice(-1)[0];
  const totalAlerts  = anomalies.filter(a => a?.is_anomaly).length;
  const cpuVal       = latestCpu  ? parseFloat(latestCpu.value.toFixed(1))  : 0;
  const memVal       = latestMem  ? parseFloat(latestMem.value.toFixed(0))  : 0;
  const activeAnomalies = anomalies.filter(a => a?.is_anomaly);

  const chartTooltipStyle = { backgroundColor: '#1a1a1a', border: '1px solid #333', color: '#e0e0e0' };

  const AnomalyDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload?.anomaly) return null;
    return <circle cx={cx} cy={cy} r={5} fill="#ff6b6b" stroke="#fff" strokeWidth={1} />;
  };

  return (
    <div className="dashboard">

      {/* ── ALERT BANNER ── */}
      {activeAnomalies.length > 0 && (
        <div className="anomaly-banner">
          🚨 {activeAnomalies.length} anomaly{activeAnomalies.length > 1 ? 'ies' : ''} detected —&nbsp;
          {activeAnomalies.slice(-3).map(a => (
            <span key={`${a.pod}-${a.timestamp}`} className="anomaly-tag">
              {a.pod} · {a.metric} · z={a.z_score.toFixed(2)}
            </span>
          ))}
        </div>
      )}

      {/* ── KPI CARDS ── */}
      <div className="kpi-section">
        <KPICard
          title="CPU Usage"
          value={cpuVal}
          unit="%"
          severity={cpuVal > 80 ? 'critical' : cpuVal > 60 ? 'warning' : 'normal'}
          trend={latestCpu?.is_anomaly ? 'up' : 'stable'}
        />
        <KPICard
          title="Memory Usage"
          value={memVal}
          unit=" MB"
          severity={memVal > 400 ? 'critical' : memVal > 300 ? 'warning' : 'normal'}
          trend={latestMem?.is_anomaly ? 'up' : 'stable'}
        />
        <KPICard
          title="Active Incidents"
          value={incidents.length}
          severity={incidents.length > 0 ? 'critical' : 'normal'}
        />
        <KPICard
          title="Total Alerts"
          value={totalAlerts}
          severity={totalAlerts > 5 ? 'critical' : totalAlerts > 0 ? 'warning' : 'normal'}
          trend={totalAlerts > 0 ? 'up' : 'stable'}
        />
      </div>

      {/* ── CHARTS + FEED ── */}
      <div className="content-grid">
        <div className="charts-section">

          {/* CPU */}
          <div className="chart-container">
            <h3>CPU Usage <span className="chart-unit">(%)</span>
              {latestCpu?.is_anomaly && <span className="chart-alert-badge">⚠ ANOMALY</span>}
            </h3>
            {cpuData.length === 0
              ? <div className="chart-empty">Waiting for data…</div>
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={cpuData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={45} />
                    <Tooltip contentStyle={chartTooltipStyle} formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : '%']} />
                    <Line type="monotone" dataKey="value" stroke="#00d4ff" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#555" strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
          </div>

          {/* Memory */}
          <div className="chart-container">
            <h3>Memory Usage <span className="chart-unit">(MB)</span>
              {latestMem?.is_anomaly && <span className="chart-alert-badge">⚠ ANOMALY</span>}
            </h3>
            {memoryData.length === 0
              ? <div className="chart-empty">Waiting for data…</div>
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={memoryData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={55} />
                    <Tooltip contentStyle={chartTooltipStyle} formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : 'MB']} />
                    <Line type="monotone" dataKey="value" stroke="#ff6b6b" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#555" strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
          </div>

          {/* Storage / Logs */}
          <div className="chart-container">
            <h3>Storage / Logs <span className="chart-unit">(value)</span></h3>
            {storageData.length === 0
              ? <div className="chart-empty">Waiting for data…</div>
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={storageData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis stroke="#888" width={45} />
                    <Tooltip contentStyle={chartTooltipStyle} formatter={(v: any, n: string) => [v, n === 'z_score' ? 'Z-Score' : 'Value']} />
                    <Line type="monotone" dataKey="value" stroke="#51cf66" strokeWidth={2} dot={<AnomalyDot />} isAnimationActive={false} />
                    <Line type="monotone" dataKey="z_score" stroke="#555" strokeWidth={1} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
          </div>

        </div>

        {/* ── INCIDENT FEED ── */}
        <div className="incident-feed">
          <h3>Recent Incidents</h3>
          <div className="incident-list">
            {incidents.length === 0
              ? <div className="no-incidents">No incidents detected</div>
              : incidents.slice(0, 10).map(inc => (
                  <IncidentCard key={inc.incident_id} incident={inc} />
                ))
            }
          </div>
        </div>
      </div>
    </div>
  );
};
