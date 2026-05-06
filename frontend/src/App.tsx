import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Incidents } from './pages/Incidents';
import { IncidentDetails } from './pages/IncidentDetails';
import { DependencyGraph } from './pages/DependencyGraph';
import { FixHistory } from './pages/FixHistory';
import { Settings } from './pages/Settings';
import { api } from './services/api';
import axios from 'axios';
import './App.css';

const client = axios.create({ baseURL: '' });

function App() {
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded'>('healthy');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    try {
      await client.get('/health');
      setSystemStatus('healthy');
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
        <Header systemStatus={systemStatus} onRefresh={handleRefresh} onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <div className="app-body">
          <Sidebar collapsed={sidebarCollapsed} />
          <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/incidents" element={<Incidents />} />
              <Route path="/incident/:id" element={<IncidentDetails />} />
              <Route path="/graph" element={<DependencyGraph />} />
              <Route path="/fixes" element={<FixHistory />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
