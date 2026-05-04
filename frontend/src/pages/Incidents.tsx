import React, { useState, useEffect } from 'react';
import { IncidentCard } from '../components/IncidentCard';
import { api } from '../services/api';
import { Incident } from '../types';
import '../styles/Incidents.css';

export const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high'>('all');

  useEffect(() => {
    api.getIncidents().then(setIncidents);
  }, []);

  const filteredIncidents = incidents.filter(inc => {
    if (filter === 'all') return true;
    if (filter === 'critical') return inc.confidence >= 0.8;
    if (filter === 'high') return inc.confidence >= 0.6 && inc.confidence < 0.8;
    return true;
  });

  return (
    <div className="incidents-page">
      <div className="incidents-header">
        <h1>All Incidents</h1>
        <div className="filter-buttons">
          <button 
            className={filter === 'all' ? 'active' : ''} 
            onClick={() => setFilter('all')}
          >
            All ({incidents.length})
          </button>
          <button 
            className={filter === 'critical' ? 'active' : ''} 
            onClick={() => setFilter('critical')}
          >
            Critical
          </button>
          <button 
            className={filter === 'high' ? 'active' : ''} 
            onClick={() => setFilter('high')}
          >
            High
          </button>
        </div>
      </div>

      <div className="incidents-grid">
        {filteredIncidents.length === 0 ? (
          <div className="no-incidents">No incidents found</div>
        ) : (
          filteredIncidents.map(incident => (
            <IncidentCard key={incident.incident_id} incident={incident} />
          ))
        )}
      </div>
    </div>
  );
};
