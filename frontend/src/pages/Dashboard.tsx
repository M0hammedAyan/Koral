import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { KPICard } from '../components/KPICard';
import { api, wsService } from '../services/api';
import { Incident, Anomaly } from '../types';
import '../styles/Dashboard.css';

interface ChartPoint {
  timestamp: number;
  value: number;
  z_score: number;
  anomaly: boolean;
}

interface Suggestion {
  id: string;
  severity: 'critical' | 'high' | 'medium';
  title: string;
  description: string;
  autoFixable: boolean;
  action?: () => Promise<void>;
}

interface HistoryEntry {
  id: string;
  action: string;
  actor: 'ai' | 'developer';
  timestamp: number;
  reason: string;
  status: 'success' | 'failed';
}

// Live clock hook
function useLiveClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return time;
}

// Format time for display
const formatTime = (date: Date) => {
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit',
    hour12: false 
  });
};

const formatTimestamp = (ts: number) => {
  const now = Date.now();
  const diff = Math.floor((now - ts) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
};

export const Dashboard: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [cpuData, setCpuData] = useState<ChartPoint[]>([]);
  const [memoryData, setMemoryData] = useState<ChartPoint[]>([]);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'live' | 'reconnecting'>('connecting');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const anomaliesRef = useRef<Anomaly[]>([]);
  const now = useLiveClock();

  useEffect(() => { anomaliesRef.current = anomalies; }, [anomalies]);

  // Generate AI suggestions based on current incidents
  const generateSuggestions = useCallback((incs: Incident[]) => {
    const newSuggestions: Suggestion[] = [];

    // Critical incidents
    const criticalIncs = incs.filter(i => i.severity === 'critical');
    criticalIncs.forEach((inc, idx) => {
      newSuggestions.push({
        id: `crit-${idx}`,
        severity: 'critical',
        title: inc.namespace ? `Critical: ${inc.namespace}` : 'Critical Incident',
        description: inc.summary || `${inc.affected_pods?.[0] || 'System'} experiencing critical issue`,
        autoFixable: false,
      });
    });

    // High severity
    const highIncs = incs.filter(i => i.severity === 'high');
    highIncs.slice(0, 2).forEach((inc, idx) => {
      newSuggestions.push({
        id: `high-${idx}`,
        severity: 'high',
        title: `High: ${inc.namespace || 'Service'}`,
        description: inc.summary || 'Elevated issue detected',
        autoFixable: true,
      });
    });

    // Medium issues (autofix suggested)
    const mediumAnoms = anomalies.filter(a => a.is_anomaly && a.z_score < 3).slice(0, 1);
    mediumAnoms.forEach((anom, idx) => {
      newSuggestions.push({
        id: `medium-${idx}`,
        severity: 'medium',
        title: `Auto-fix: ${anom.metric}`,
        description: `${anom.metric} anomaly can be auto-corrected`,
        autoFixable: true,
      });
    });

    setSuggestions(newSuggestions);
  }, [anomalies]);

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
  }, []);

  const loadData = useCallback(async () => {
    try {
      const [inc, anoms] = await Promise.all([api.getIncidents(), api.getAnomalies()]);
      setIncidents(inc || []);
      setAnomalies(anoms || []);
      buildCharts(anoms || []);
      generateSuggestions(inc || []);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Load error:', err);
    }
  }, [buildCharts, generateSuggestions]);

  // WebSocket setup
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
        generateSuggestions([msg.payload, ...incidents]);
        setLastUpdate(new Date());
      }
    });

    const interval = setInterval(loadData, 30000);
    return () => { 
      clearInterval(interval); 
      wsService.disconnect(); 
    };
  }, [loadData, buildCharts, generateSuggestions]);

  // KPIs
  const latestCpu = anomalies.filter(a => a?.metric === 'cpu').slice(-1)[0];
  const latestMem = anomalies.filter(a => a?.metric === 'memory').slice(-1)[0];
  const criticalCount = incidents.filter(i => i.severity === 'critical').length;
  const cpuVal = latestCpu ? parseFloat(latestCpu.value.toFixed(1)) : 0;
  const memVal = latestMem ? parseFloat(latestMem.value.toFixed(0)) : 0;

  const handleApplySuggestion = (suggestion: Suggestion) => {
    const entry: HistoryEntry = {
      id: `fix-${Date.now()}`,
      action: `Applied: ${suggestion.title}`,
      actor: 'ai',
      timestamp: Date.now(),
      reason: suggestion.description,
      status: 'success',
    };
    setHistory(prev => [entry, ...prev].slice(0, 20));
    setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
  };

  return (
    <div className="dashboard">
      {/* TOP BAR */}
      <div className="dashboard-topbar">
        <div className="topbar-left">
          <div className="live-status">
            <span className={`live-dot ${wsStatus}`}></span>
            <span className="live-label">
              {wsStatus === 'live' ? 'LIVE' : 'RECONNECTING...'}
            </span>
          </div>
          <div className="clock">{formatTime(now)}</div>
        </div>
        <div className="last-update">
          {lastUpdate && `Updated: ${formatTime(lastUpdate)}`}
        </div>
      </div>

      {/* CONTENT */}
      <div className="dashboard-content">
        
        {/* LEFT: MAIN MONITORING */}
        <div className="content-left">
          
          {/* KPI Cards */}
          <div className="kpi-row">
            <div className="kpi-card">
              <div className="kpi-label">CPU Usage</div>
              <div className="kpi-value">
                {cpuVal}
                <span className="kpi-unit">%</span>
                <span className={`kpi-status ${cpuVal > 80 ? 'critical' : cpuVal > 50 ? 'warning' : 'normal'}`}></span>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Memory</div>
              <div className="kpi-value">
                {memVal}
                <span className="kpi-unit">%</span>
                <span className={`kpi-status ${memVal > 80 ? 'critical' : memVal > 60 ? 'warning' : 'normal'}`}></span>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Incidents</div>
              <div className="kpi-value">
                {incidents.length}
                <span className={`kpi-status ${criticalCount > 0 ? 'critical' : criticalCount > 0 ? 'warning' : 'normal'}`}></span>
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Anomalies</div>
              <div className="kpi-value">
                {anomalies.filter(a => a.is_anomaly).length}
                <span className="kpi-status normal"></span>
              </div>
            </div>
          </div>

          {/* Incidents Section */}
          <div className="incidents-section">
            <div className="section-header">
              <div>
                <div className="section-title">Incidents</div>
                <div className="section-meta">{incidents.length} active incidents</div>
              </div>
            </div>
            <div className="incidents-list">
              {incidents.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-text">No incidents detected</div>
                </div>
              ) : (
                incidents.slice(0, 8).map(inc => (
                  <div key={inc.incident_id} className={`incident-card ${inc.severity || 'normal'}`}>
                    <div className="incident-header">
                      <div className="incident-title">
                        {inc.affected_pods?.[0] || inc.namespace || 'System'}
                      </div>
                      <span className={`incident-badge ${inc.severity || 'normal'}`}>
                        {inc.severity || 'normal'}
                      </span>
                    </div>
                    <div className="incident-details">
                      <span>{inc.namespace}</span>
                      <span className="incident-time">{formatTimestamp(inc.timestamp)}</span>
                    </div>
                    {inc.summary && (
                      <div className="incident-ai-snippet">{inc.summary}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Charts */}
          <div className="charts-section">
            <div className="section-title" style={{ marginBottom: '1rem' }}>CPU Trend</div>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={cpuData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                <XAxis dataKey="timestamp" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #475569', borderRadius: '8px', color: '#e0e0e0' }} />
                <Line type="monotone" dataKey="value" stroke="#0ea5e9" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* RIGHT: SIDEBAR (AI PANEL + HISTORY) */}
        <div className="dashboard-sidebar">
          
          {/* AI SUGGESTIONS PANEL */}
          <div className="ai-panel">
            <div className="ai-header">
              <div className="ai-icon">AI</div>
              <div className="ai-title">KORAL AI Panel</div>
            </div>
            <div className="suggestions-list">
              {suggestions.length === 0 ? (
                <div style={{ color: '#cbd5e1', fontSize: '0.85rem', textAlign: 'center', padding: '1rem' }}>
                  All systems nominal
                </div>
              ) : (
                suggestions.map(sug => (
                  <div key={sug.id} className="suggestion-item">
                    <div>
                      <span className={`suggestion-severity ${sug.severity}`}></span>
                      <strong>{sug.title}</strong>
                    </div>
                    <div className="suggestion-text">{sug.description}</div>
                    {sug.autoFixable && (
                      <div className="suggestion-action">
                        <button 
                          className="btn-small btn-apply"
                          onClick={() => handleApplySuggestion(sug)}
                        >
                          Apply Fix
                        </button>
                        <button 
                          className="btn-small btn-dismiss"
                          onClick={() => setSuggestions(prev => prev.filter(s => s.id !== sug.id))}
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* HISTORY PANEL */}
          <div className="history-panel">
            <div className="history-title">Fix History</div>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-text">No fixes yet</div>
                </div>
              ) : (
                history.map(entry => (
                  <div key={entry.id} className={`history-item ${entry.actor}`}>
                    <div className={`history-actor ${entry.actor}`}>
                      {entry.actor === 'ai' ? 'KORAL AI' : 'DEVELOPER'}
                    </div>
                    <div className="history-action">{entry.action}</div>
                    <div className="history-reason">{entry.reason}</div>
                    <div className="history-time">{formatTimestamp(entry.timestamp)}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
