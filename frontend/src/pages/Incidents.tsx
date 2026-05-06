import React, { useState, useEffect } from 'react';
import { IncidentCard } from '../components/IncidentCard';
import { api, wsService } from '../services/api';
import { Incident } from '../types';
import '../styles/Incidents.css';

export const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium'>('all');
  const [showExplainer, setShowExplainer] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    api.getIncidents().then(data => {
      setIncidents(data);
      setLastUpdate(new Date().toLocaleTimeString());
    });

    // Live updates via WebSocket
    wsService.subscribe((msg: any) => {
      if (msg?.type === 'incident' || msg?.type === 'incident_ai') {
        setIncidents(prev => {
          const idx = prev.findIndex(i => i.incident_id === msg.payload.incident_id);
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { ...updated[idx], ...msg.payload };
            return updated;
          }
          return [msg.payload, ...prev];
        });
        setLastUpdate(new Date().toLocaleTimeString());
      }
    });
  }, []);

  const filteredIncidents = incidents.filter(inc => {
    if (filter === 'all')      return true;
    if (filter === 'critical') return inc.severity === 'critical';
    if (filter === 'high')     return inc.severity === 'high';
    if (filter === 'medium')   return inc.severity === 'medium';
    return true;
  });

  const countBySeverity = (s: string) => incidents.filter(i => i.severity === s).length;

  return (
    <div className="incidents-page">

      <div className="incidents-header">
        <div>
          <h1>All Incidents</h1>
          <div className="incidents-subtitle">
            Updates live — no refresh needed
            {lastUpdate && <span className="last-update-small"> · Last update: {lastUpdate}</span>}
          </div>
        </div>
        <button className="info-btn-large" onClick={() => setShowExplainer(!showExplainer)}>
          {showExplainer ? 'Hide explanation' : 'What are incidents?'}
        </button>
      </div>

      {/* Explainer */}
      {showExplainer && (
        <div className="incident-explainer">
          <div className="explainer-grid">
            <div className="explainer-block">
              <div className="explainer-icon">&#128268;</div>
              <h4>Anomaly</h4>
              <p>
                A single metric reading that is statistically unusual — CPU, memory, storage, or logs
                behaving differently from the last 30 readings. Measured by z-score.
                <br /><br />
                <strong>Think of it as:</strong> a smoke detector going off.
              </p>
            </div>
            <div className="explainer-arrow">&#8594;</div>
            <div className="explainer-block">
              <div className="explainer-icon">&#128196;</div>
              <h4>Incident</h4>
              <p>
                Created when the AI analyses an anomaly and identifies the root cause.
                An incident tells you <strong>what</strong> broke, <strong>why</strong>,
                which pods are affected, and what to do.
                <br /><br />
                <strong>Think of it as:</strong> the fire report after the alarm.
              </p>
            </div>
            <div className="explainer-arrow">&#8594;</div>
            <div className="explainer-block">
              <div className="explainer-icon">&#129302;</div>
              <h4>AI Action</h4>
              <p>
                Based on severity, the AI either auto-fixes the issue, reports it to you,
                or alerts the developer immediately.
                <br /><br />
                <strong>Think of it as:</strong> the fire brigade deciding what to do.
              </p>
            </div>
          </div>
          <div className="severity-explainer">
            <div className="sev-row critical"><span>CRITICAL</span> System is down or about to crash — developer alerted immediately</div>
            <div className="sev-row high"><span>HIGH</span> Serious degradation — AI explains and recommends action</div>
            <div className="sev-row medium"><span>MEDIUM</span> Unusual behaviour — AI auto-handles and reports what it did</div>
            <div className="sev-row low"><span>LOW</span> Minor deviation — logged and monitored automatically</div>
          </div>
        </div>
      )}

      {/* Filter buttons */}
      <div className="filter-bar">
        {([
          { key: 'all',      label: 'All',      count: incidents.length },
          { key: 'critical', label: 'Critical', count: countBySeverity('critical') },
          { key: 'high',     label: 'High',     count: countBySeverity('high') },
          { key: 'medium',   label: 'Medium',   count: countBySeverity('medium') },
        ] as const).map(({ key, label, count }) => (
          <button
            key={key}
            className={`filter-btn ${filter === key ? 'active' : ''} ${key}`}
            onClick={() => setFilter(key)}
          >
            {label}
            <span className="filter-count">{count}</span>
          </button>
        ))}
      </div>

      <div className="incidents-grid">
        {filteredIncidents.length === 0 ? (
          <div className="no-incidents-full">
            <div className="no-inc-icon">&#10003;</div>
            <div>No {filter === 'all' ? '' : filter} incidents</div>
            <div className="no-inc-sub">
              {filter === 'all'
                ? 'No incidents have been detected yet. The system is monitoring your cluster.'
                : `No ${filter} severity incidents at this time.`}
            </div>
          </div>
        ) : (
          filteredIncidents.map(incident => (
            <IncidentCard key={incident.incident_id} incident={incident} />
          ))
        )}
      </div>
    </div>
  );
};
