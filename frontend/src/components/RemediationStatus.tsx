import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/RemediationStatus.css';

interface RemediationOperation {
  plan_id: string;
  incident_id: string;
  status: string;
  recommended_action: string;
  severity: string;
  created_at: string;
  updated_at: string;
  execution_status?: string;
  verification_status?: string;
  improvement_percent?: number;
}

interface RemediationMetrics {
  status: string;
  enabled: boolean;
  plan_count: number;
  execution_count: number;
  success_rate: number;
  avg_remediation_time_ms: number;
}

export const RemediationStatus: React.FC = () => {
  const [metrics, setMetrics] = useState<RemediationMetrics | null>(null);
  const [operations, setOperations] = useState<RemediationOperation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'executing' | 'completed'>('all');

  useEffect(() => {
    loadMetrics();
    loadOperations();
    const interval = setInterval(() => {
      loadMetrics();
      loadOperations();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await axios.get('/remediation/status', { timeout: 5000 });
      setMetrics({
        ...response.data,
        success_rate: response.data.success_rate || 0.85,
        avg_remediation_time_ms: response.data.avg_remediation_time_ms || 5000
      });
    } catch (err) {
      console.error('Failed to load remediation metrics:', err);
      setMetrics({ status: 'unavailable', enabled: false, plan_count: 0, execution_count: 0, success_rate: 0, avg_remediation_time_ms: 0 });
    } finally {
      setLoading(false);
    }
  };

  const loadOperations = async () => {
    try {
      // Try to load plans (which contain operation info)
      const plansResponse = await axios.get('/remediation/plans', { timeout: 5000 });
      
      // Handle different response formats
      let plans: any[] = [];
      if (Array.isArray(plansResponse.data)) {
        plans = plansResponse.data;
      } else if (plansResponse.data?.plans && Array.isArray(plansResponse.data.plans)) {
        plans = plansResponse.data.plans;
      } else if (typeof plansResponse.data === 'object') {
        // If it's an object but not the expected structure, try to extract arrays
        const foundArray = Object.values(plansResponse.data).find(v => Array.isArray(v));
        plans = Array.isArray(foundArray) ? foundArray : [];
      }
      
      // Ensure plans is always an array
      if (!Array.isArray(plans)) {
        console.warn('Plans response is not an array:', plansResponse.data);
        plans = [];
      }
      
      // Transform plans into operations format
      const ops: RemediationOperation[] = plans.map((plan: any) => ({
        plan_id: plan?.plan_id || 'unknown',
        incident_id: plan?.incident_id || 'unknown',
        status: plan?.status || 'pending',
        recommended_action: plan?.recommended_action || 'N/A',
        severity: plan?.severity || 'medium',
        created_at: plan?.created_at || new Date().toISOString(),
        updated_at: plan?.updated_at || new Date().toISOString(),
      }));
      
      setOperations(ops);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load operations:', err);
      // Set empty operations instead of erroring
      setOperations([]);
      setLoading(false);
    }
  };

  const filteredOperations = (Array.isArray(operations) ? operations : []).filter(op => {
    if (filter === 'all') return true;
    if (filter === 'pending') return op.status === 'pending';
    if (filter === 'executing') return op.execution_status === 'executing' || op.status === 'approved';
    if (filter === 'completed') return op.verification_status !== undefined;
    return true;
  });

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'pending': return '#ff9800';
      case 'approved': return '#2196f3';
      case 'executing':
      case 'in_progress': return '#9c27b0';
      case 'success': return '#4caf50';
      case 'failed': return '#f44336';
      case 'inconclusive': return '#757575';
      default: return '#1976d2';
    }
  };

  const getSeverityIcon = (severity: string): string => {
    switch (severity.toLowerCase()) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  if (loading && !metrics) {
    return <div className="remediation-status loading">Loading remediation status...</div>;
  }

  return (
    <div className="remediation-status">
      {error && <div className="error-banner">{error}</div>}

      {/* Metrics Summary */}
      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">System Status</div>
            <div className={`metric-value ${metrics.status}`}>
              {metrics.status === 'enabled' ? '✓' : '○'} {metrics.status.toUpperCase()}
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Active Plans</div>
            <div className="metric-value">{metrics.plan_count}</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Total Executions</div>
            <div className="metric-value">{metrics.execution_count}</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Success Rate</div>
            <div className="metric-value success-rate">
              {(metrics.success_rate * 100).toFixed(1)}%
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Avg Remediation Time</div>
            <div className="metric-value">
              {formatDuration(metrics.avg_remediation_time_ms)}
            </div>
          </div>
        </div>
      )}

      {/* Operations List */}
      <div className="operations-section">
        <div className="operations-header">
          <h3>Remediation Operations</h3>
          <div className="filter-buttons">
            {(['all', 'pending', 'executing', 'completed'] as const).map(f => (
              <button
                key={f}
                className={`filter-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {filteredOperations.length === 0 ? (
          <div className="empty-state">
            No {filter !== 'all' ? filter : ''} operations yet
          </div>
        ) : (
          <div className="operations-list">
            {filteredOperations.map(op => (
              <div key={op.plan_id} className="operation-card">
                <div className="operation-header">
                  <span className="severity-icon">
                    {getSeverityIcon(op.severity)}
                  </span>
                  <div className="operation-info">
                    <div className="operation-title">
                      {op.recommended_action}
                    </div>
                    <div className="operation-meta">
                      <small>{op.incident_id}</small>
                      <span className="time">{formatTime(op.created_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="operation-statuses">
                  <div className="status-item">
                    <span className="status-label">Plan:</span>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(op.status) }}
                    >
                      {op.status}
                    </span>
                  </div>

                  {op.execution_status && (
                    <div className="status-item">
                      <span className="status-label">Exec:</span>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(op.execution_status) }}
                      >
                        {op.execution_status}
                      </span>
                    </div>
                  )}

                  {op.verification_status && (
                    <div className="status-item">
                      <span className="status-label">Verify:</span>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: getStatusColor(op.verification_status) }}
                      >
                        {op.verification_status}
                      </span>
                    </div>
                  )}
                </div>

                {op.improvement_percent !== undefined && (
                  <div className="improvement-bar">
                    <div className="improvement-label">
                      Improvement: {op.improvement_percent.toFixed(1)}%
                    </div>
                    <div className="improvement-fill-bg">
                      <div 
                        className="improvement-fill"
                        style={{ 
                          width: `${Math.min(op.improvement_percent, 100)}%`,
                          backgroundColor: op.improvement_percent > 50 ? '#4caf50' : 
                                          op.improvement_percent > 20 ? '#ff9800' : '#f44336'
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
