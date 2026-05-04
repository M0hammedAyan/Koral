import React, { useState } from 'react';
import '../styles/Settings.css';

export const Settings: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [cpuThreshold, setCpuThreshold] = useState(2.5);
  const [memoryThreshold, setMemoryThreshold] = useState(2.5);
  const [storageThreshold, setStorageThreshold] = useState(2.5);

  const handleSave = () => {
    localStorage.setItem('settings', JSON.stringify({
      autoRefresh,
      cpuThreshold,
      memoryThreshold,
      storageThreshold
    }));
    alert('Settings saved successfully!');
  };

  return (
    <div className="settings">
      <h1>Settings</h1>

      <div className="settings-section">
        <h2>Display Options</h2>
        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh Dashboard
          </label>
          <span className="setting-description">
            Automatically refresh data every 10 seconds
          </span>
        </div>
      </div>

      <div className="settings-section">
        <h2>Anomaly Detection Thresholds</h2>
        
        <div className="setting-item">
          <label>CPU Z-Score Threshold</label>
          <input
            type="number"
            step="0.1"
            min="1.0"
            max="5.0"
            value={cpuThreshold}
            onChange={(e) => setCpuThreshold(parseFloat(e.target.value))}
          />
          <span className="setting-description">
            Current: {cpuThreshold} (Higher = fewer alerts)
          </span>
        </div>

        <div className="setting-item">
          <label>Memory Z-Score Threshold</label>
          <input
            type="number"
            step="0.1"
            min="1.0"
            max="5.0"
            value={memoryThreshold}
            onChange={(e) => setMemoryThreshold(parseFloat(e.target.value))}
          />
          <span className="setting-description">
            Current: {memoryThreshold}
          </span>
        </div>

        <div className="setting-item">
          <label>Storage Z-Score Threshold</label>
          <input
            type="number"
            step="0.1"
            min="1.0"
            max="5.0"
            value={storageThreshold}
            onChange={(e) => setStorageThreshold(parseFloat(e.target.value))}
          />
          <span className="setting-description">
            Current: {storageThreshold}
          </span>
        </div>
      </div>

      <div className="settings-actions">
        <button className="btn-primary" onClick={handleSave}>
          Save Settings
        </button>
        <button className="btn-secondary" onClick={() => window.location.reload()}>
          Reset to Defaults
        </button>
      </div>
    </div>
  );
};
