import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Incident } from '../types';
import '../styles/IncidentCard.css';

interface Props { incident: Incident; }

const ROOT_CAUSE_LABELS: Record<string, string> = {
  cpu_saturation:             'CPU Saturation',
  memory_pressure_or_oom:     'Memory Pressure / OOM',
  storage_io_bottleneck:      'Storage I/O Bottleneck',
  network_latency_degradation:'Network Latency Degradation',
  application_crash_loop:     'Application Crash Loop',
  service_latency_spike:      'Service Latency Spike',
  pod_restart_spike:          'Pod Restart Spike',
  application_error_spike:    'Application Error Spike',
  unknown_anomalous_behavior: 'Unknown Anomalous Behavior',
};

const AI_ACTION_INFO: Record<string, { label: string; color: string; icon: string }> = {
  auto_fix:        { label: 'AI Auto-Fixed',        color: '#51cf66', icon: '[OK]'  },
  report:          { label: 'AI Reported to You',   color: '#ffa500', icon: '[!!]'  },
  alert_developer: { label: 'Developer Alerted',    color: '#ff6b6b', icon: '[!!!]' },
};

export const IncidentCard: React.FC<Props> = ({ incident }) => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);

  const formatTime = (ts?: number | string) => {
    if (!ts) return 'Just now';
    const t = typeof ts === 'string' ? Date.parse(ts) : ts * 1000;
    const diff = Math.floor((Date.now() - t) / 60000);
    if (diff < 1)  return 'Just now';
    if (diff < 60) return `${diff}m ago`;
    return `${Math.floor(diff / 60)}h ago`;
  };

  const severity   = incident.severity ?? 'medium';
  const confidence = incident.confidence != null
    ? `${(incident.confidence * 100).toFixed(0)}%` : '—';
  const aiAction   = AI_ACTION_INFO[incident.ai_action ?? ''];
  const hasAI      = !!(incident.ai_explanation || incident.ai_message);

  // Clean up ai_message — remove markdown bold markers for display
  const aiText = (incident.ai_message || incident.ai_explanation || '')
    .replace(/\*\*/g, '')
    .trim();

  return (
    <div className={`incident-card ${severity}`}>

      {/* Header */}
      <div className="incident-header">
        <span className={`severity-badge ${severity}`}>{severity.toUpperCase()}</span>
        <span className="incident-time">{formatTime(incident.created_at ?? incident.timestamp)}</span>
      </div>

      {/* ID + Root Cause */}
      <div className="incident-title">{incident.incident_id}</div>
      <div className="incident-cause">
        {ROOT_CAUSE_LABELS[incident.root_cause] ?? incident.root_cause}
      </div>

      {/* Summary */}
      {incident.summary && (
        <div className="incident-summary">{incident.summary}</div>
      )}

      {/* AI Action badge */}
      {aiAction && (
        <div className="ai-action-badge" style={{ color: aiAction.color, borderColor: aiAction.color + '44' }}>
          {aiAction.icon} {aiAction.label}
        </div>
      )}

      {/* AI Explanation — expandable */}
      {hasAI && (
        <div className="ai-explanation-section">
          <button className="ai-expand-btn" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Hide AI Analysis' : 'Show AI Analysis'}
          </button>
          {expanded && (
            <div className="ai-explanation-text">
              {aiText.split('\n').filter(Boolean).map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="incident-footer">
        <span className="confidence">Confidence: {confidence}</span>
        <button
          className="view-details-btn"
          onClick={() => navigate(`/incident/${encodeURIComponent(incident.incident_id)}`)}
        >
          Details
        </button>
      </div>
    </div>
  );
};
