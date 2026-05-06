import React from 'react';
import '../styles/Header.css';

interface HeaderProps {
  systemStatus: 'healthy' | 'degraded';
  onRefresh: () => void;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ systemStatus, onRefresh, onToggleSidebar }) => {
  return (
    <header className="header">
      <div className="header-left">
        <button className="sidebar-toggle" onClick={onToggleSidebar}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div className="header-logo">
          <div className="header-logo-icon">K</div>
          <div>
            <div className="header-title">KORAL</div>
            <div className="header-subtitle">Kubernetes Observability Platform</div>
          </div>
        </div>
      </div>
      <div className="header-right">
        <div className="system-status">
          <div className={`status-indicator ${systemStatus}`}></div>
          <span className={`status-text ${systemStatus}`}>
            {systemStatus === 'healthy' ? 'Operational' : 'Degraded'}
          </span>
        </div>
        <div className="header-actions">
          <button className="header-btn" onClick={onRefresh}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>
    </header>
  );
};
