import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/Sidebar.css';

export const Sidebar: React.FC<{ collapsed: boolean }> = ({ collapsed }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: 'dashboard' },
    { path: '/incidents', label: 'Incidents', icon: 'alert' },
    { path: '/graph', label: 'Dependency Graph', icon: 'network' },
    { path: '/fixes', label: 'Fix History', icon: 'tools' },
    { path: '/remediation', label: 'Remediation', icon: 'remediation' },
    { path: '/settings', label: 'Settings', icon: 'settings' }
  ];

  const getIconSvg = (iconName: string) => {
    const icons: Record<string, JSX.Element> = {
      dashboard: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7"/>
          <rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/>
        </svg>
      ),
      alert: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      ),
      network: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"/>
          <circle cx="6" cy="6" r="2"/>
          <circle cx="18" cy="6" r="2"/>
          <circle cx="6" cy="18" r="2"/>
          <circle cx="18" cy="18" r="2"/>
          <line x1="10.5" y1="10.5" x2="7.5" y2="7.5"/>
          <line x1="13.5" y1="10.5" x2="16.5" y2="7.5"/>
          <line x1="10.5" y1="13.5" x2="7.5" y2="16.5"/>
          <line x1="13.5" y1="13.5" x2="16.5" y2="16.5"/>
        </svg>
      ),
      tools: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
        </svg>
      ),
      remediation: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="9"/>
          <path d="M12 7v5l3 2"/>
        </svg>
      ),
      settings: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v6m0 6v6m5.2-13.2l-4.2 4.2m0 6l4.2 4.2M23 12h-6m-6 0H1m18.2-5.2l-4.2 4.2m0 6l4.2 4.2"/>
        </svg>
      )
    };
    return icons[iconName] || icons.dashboard;
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <nav>
        {menuItems.map(item => (
          <div
            key={item.path}
            className={`menu-item ${location.pathname === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}
          >
            <span className="icon">{getIconSvg(item.icon)}</span>
            <span className="label">{item.label}</span>
          </div>
        ))}
      </nav>
    </aside>
  );
};
