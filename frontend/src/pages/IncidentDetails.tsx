import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Incident } from '../types';
import '../styles/IncidentDetails.css';

export const IncidentDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<Incident | null>(null);

  useEffect(() => {
    if (id) {
      api.getIncidentById(id).then(setIncident);
    }
  }, [id]);

  if (!incident) {
    return <div className="loading">Loading incident details...</div>;
  }

  const confidencePercent = (incident.confidence * 100).toFixed(0);

  return (
    <div className="incident-details">
      <div className="details-header">
        <h1>{incident.incident_id}</h1>
        <div className="confidence-badge">
          Confidence: {confidencePercent}%
        </div>
      </div>

      <div className="root-cause-section">
        <h2>Root Cause</h2>
        <div className="root-cause-box">
          {incident.root_cause}
        </div>
      </div>

      <div className="affected-pods-section">
        <h3>Affected Pods</h3>
        <div className="pod-list">
          {incident.affected_pods.map(pod => (
            <div key={pod} className="pod-badge">{pod}</div>
          ))}
        </div>
      </div>

      <div className="timeline-section">
        <h3>Timeline</h3>
        <div className="timeline">
          <div className="timeline-item">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <div className="timeline-time">T+0s</div>
              <div className="timeline-text">Anomaly detected</div>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-dot"></div>
            <div className="timeline-content">
              <div className="timeline-time">T+15s</div>
              <div className="timeline-text">Correlation analysis completed</div>
            </div>
          </div>
          <div className="timeline-item">
            <div className="timeline-dot active"></div>
            <div className="timeline-content">
              <div className="timeline-time">T+30s</div>
              <div className="timeline-text">Root cause identified</div>
            </div>
          </div>
        </div>
      </div>

      <div className="action-buttons">
        <button className="btn-secondary" onClick={() => navigate('/')}>
          ← Back to Dashboard
        </button>
        <button className="btn-primary" onClick={() => navigate('/graph')}>
          View Dependency Graph →
        </button>
      </div>
    </div>
  );
};
