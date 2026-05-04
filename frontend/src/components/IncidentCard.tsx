import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Incident } from '../types';
import '../styles/IncidentCard.css';

interface IncidentCardProps {
  incident: Incident;
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident }) => {
  const navigate = useNavigate();

  const getSeverityColor = (confidence: number) => {
    if (confidence >= 0.8) return 'critical';
    if (confidence >= 0.6) return 'high';
    if (confidence >= 0.4) return 'medium';
    return 'low';
  };

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return 'Just now';
    const diff = Date.now() - timestamp * 1000;
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    return `${Math.floor(minutes / 60)}h ago`;
  };

  const severity = getSeverityColor(incident.confidence);

  return (
    <div className={`incident-card ${severity}`}>
      <div className="incident-header">
        <span className={`severity-badge ${severity}`}>
          {severity.toUpperCase()}
        </span>
        <span className="incident-time">{formatTime(incident.timestamp)}</span>
      </div>
      <div className="incident-title">{incident.incident_id}</div>
      <div className="incident-cause">{incident.root_cause}</div>
      <div className="incident-footer">
        <span className="confidence">Confidence: {(incident.confidence * 100).toFixed(0)}%</span>
        <button 
          className="view-details-btn"
          onClick={() => navigate(`/incident/${incident.incident_id}`)}
        >
          View Details →
        </button>
      </div>
    </div>
  );
};
