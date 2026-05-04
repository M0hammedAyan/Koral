import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Incidents } from './pages/Incidents';
import { IncidentDetails } from './pages/IncidentDetails';
import { DependencyGraph } from './pages/DependencyGraph';
import { Settings } from './pages/Settings';
import { api } from './services/api';
import './App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded'>('healthy');

  useEffect(() => {
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    try {
      const incidents = await api.getIncidents();
      setSystemStatus(incidents.length > 0 ? 'degraded' : 'healthy');
    } catch {
      setSystemStatus('degraded');
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <BrowserRouter>
      <div className="app">
        <Header systemStatus={systemStatus} onRefresh={handleRefresh} />
        <div className="app-body">
          <Sidebar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/incident/:id" element={<IncidentDetails />} />
              <Route path="/graph" element={<DependencyGraph />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
