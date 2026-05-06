import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import '../styles/FixHistory.css';

interface Fix {
  id?: number;
  incident_id: string;
  fix_type: string;
  fix_description: string;
  applied_by: string;
  success: boolean;
  error_message?: string;
  kubectl_command?: string;
  timestamp: number;
  created_at: string;
}

interface FixStats {
  total_fixes: number;
  ai_fixes: number;
  developer_fixes: number;
  successful_fixes: number;
  failed_fixes: number;
  success_rate: number;
}

export const FixHistory: React.FC = () => {
  const [fixes, setFixes] = useState<Fix[]>([]);
  const [stats, setStats] = useState<FixStats | null>(null);
  const [filter, setFilter] = useState<'all' | 'ai' | 'developer'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [filter]);

  const loadData = async () => {
    try {
      const filterParam = filter === 'all' ? undefined : filter === 'ai' ? 'AI' : 'Developer';
      const [fixesData, statsData] = await Promise.all([
        api.getFixHistory(100, filterParam),
        api.getFixStats()
      ]);
      setFixes(fixesData);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load fix history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (ts: number) => {
    const date = new Date(ts * 1000);
    return date.toLocaleString();
  };

  const getAppliedByColor = (appliedBy: string) => {
    return appliedBy === 'AI' ? '#00d4ff' : '#51cf66';
  };

  if (loading) {
    return <div className="loading">Loading fix history...</div>;
  }

  return (
    <div className="fix-history">
      <div className="fix-history-header">
        <h1>Fix History</h1>
        <p className="fix-history-subtitle">
          Track all fixes applied by AI and developers
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="fix-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.total_fixes}</div>
            <div className="stat-label">Total Fixes</div>
          </div>
          <div className="stat-card ai">
            <div className="stat-value">{stats.ai_fixes}</div>
            <div className="stat-label">AI Auto-Fixes</div>
          </div>
          <div className="stat-card developer">
            <div className="stat-value">{stats.developer_fixes}</div>
            <div className="stat-label">Developer Fixes</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{stats.success_rate}%</div>
            <div className="stat-label">Success Rate</div>
          </div>
        </div>
      )}

      {/* Filter Buttons */}
      <div className="fix-filters">
        <button
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Fixes
        </button>
        <button
          className={`filter-btn ${filter === 'ai' ? 'active' : ''}`}
          onClick={() => setFilter('ai')}
        >
          AI Fixes
        </button>
        <button
          className={`filter-btn ${filter === 'developer' ? 'active' : ''}`}
          onClick={() => setFilter('developer')}
        >
          Developer Fixes
        </button>
      </div>

      {/* Fix List */}
      <div className="fix-list">
        {fixes.length === 0 ? (
          <div className="no-fixes">
            <div>No fixes recorded yet</div>
            <div className="no-fixes-sub">
              Fixes will appear here when AI auto-fixes issues or developers record manual fixes
            </div>
          </div>
        ) : (
          fixes.map((fix, idx) => (
            <div key={idx} className={`fix-card ${fix.success ? 'success' : 'failed'}`}>
              <div className="fix-card-header">
                <div className="fix-card-title">
                  <span
                    className="fix-applied-by"
                    style={{ color: getAppliedByColor(fix.applied_by) }}
                  >
                    {fix.applied_by === 'AI' ? (
                      <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '6px', verticalAlign: 'middle' }}>
                          <rect x="3" y="11" width="18" height="10" rx="2"/>
                          <circle cx="12" cy="5" r="2"/>
                          <path d="M12 7v4"/>
                          <line x1="8" y1="16" x2="8" y2="16"/>
                          <line x1="16" y1="16" x2="16" y2="16"/>
                        </svg>
                        AI
                      </>
                    ) : (
                      <>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '6px', verticalAlign: 'middle' }}>
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                          <circle cx="12" cy="7" r="4"/>
                        </svg>
                        Developer
                      </>
                    )}
                  </span>
                  <span className="fix-type">{fix.fix_type.replace(/_/g, ' ')}</span>
                </div>
                <div className="fix-status">
                  {fix.success ? (
                    <span className="status-success">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '4px', verticalAlign: 'middle' }}>
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Success
                    </span>
                  ) : (
                    <span className="status-failed">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '4px', verticalAlign: 'middle' }}>
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                      Failed
                    </span>
                  )}
                </div>
              </div>

              <div className="fix-card-body">
                <div className="fix-description">{fix.fix_description}</div>

                {fix.kubectl_command && (
                  <div className="fix-command">
                    <div className="fix-command-label">Command:</div>
                    <code>{fix.kubectl_command}</code>
                    <button
                      className="copy-btn-small"
                      onClick={() => {
                        navigator.clipboard.writeText(fix.kubectl_command || '');
                      }}
                    >
                      Copy
                    </button>
                  </div>
                )}

                {fix.error_message && (
                  <div className="fix-error">
                    <strong>Error:</strong> {fix.error_message}
                  </div>
                )}

                <div className="fix-card-footer">
                  <span className="fix-incident-id">
                    Incident: <code>{fix.incident_id}</code>
                  </span>
                  <span className="fix-timestamp">
                    {formatTimestamp(fix.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
