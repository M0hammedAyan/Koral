import React from 'react';
import '../styles/Header.css';

interface HeaderProps {
  systemStatus: 'healthy' | 'degraded';
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ systemStatus, onRefresh }) => {
  return (
    <header className="header">
      <div className="header-left">
        <h1>KORAL</h1>
        <span className="subtitle">Kubernetes Observability with Real-time AI Logic</span>
      </div>
      <div className="header-right">
        <div className={`status-indicator ${systemStatus}`}>
          <span className="status-dot"></span>
          {systemStatus === 'healthy' ? 'System Healthy' : 'Issues Detected'}
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          ↻
        </button>
      </div>
    </header>
  );
};
