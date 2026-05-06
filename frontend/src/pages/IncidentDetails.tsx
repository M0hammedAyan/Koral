import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Incident } from '../types';
import '../styles/IncidentDetails.css';

const PLAYBOOKS: Record<string, {
  title: string;
  what_happened: string;
  steps: { label: string; cmd: string }[];
  escalate_if: string;
}> = {
  cpu_saturation: {
    title: 'CPU Saturation Fix',
    what_happened: 'A pod is consuming abnormally high CPU. This causes slowdowns for all other pods on the same node and can lead to request timeouts.',
    steps: [
      { label: '1. Check which pod is consuming CPU', cmd: 'kubectl top pods -n {namespace} --sort-by=cpu' },
      { label: '2. Check recent logs for errors', cmd: 'kubectl logs {pod} -n {namespace} --tail=100' },
      { label: '3. Describe the pod and check events', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '4. Restart the pod (quick fix)', cmd: 'kubectl rollout restart deployment/{pod} -n {namespace}' },
      { label: '5. Scale up if traffic is the cause', cmd: 'kubectl scale deployment/{pod} --replicas=3 -n {namespace}' },
    ],
    escalate_if: 'Pod keeps restarting after rollout restart, or CPU stays above 90% after scaling.',
  },
  memory_pressure_or_oom: {
    title: 'Memory Pressure / OOM Fix',
    what_happened: 'A pod is using too much memory and may be OOM-killed by Kubernetes. This causes crashes and restarts.',
    steps: [
      { label: '1. Check memory usage across pods', cmd: 'kubectl top pods -n {namespace} --sort-by=memory' },
      { label: '2. Check restart count and status', cmd: 'kubectl get pod {pod} -n {namespace}' },
      { label: '3. Describe pod — look for OOM events', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '4. Check logs before crash', cmd: 'kubectl logs {pod} -n {namespace} --previous --tail=50' },
      { label: '5. Restart the pod', cmd: 'kubectl rollout restart deployment/{pod} -n {namespace}' },
    ],
    escalate_if: 'Pod keeps getting OOM-killed after restart. Memory leak in application code needs a developer fix.',
  },
  storage_io_bottleneck: {
    title: 'Storage I/O Bottleneck Fix',
    what_happened: 'A pod is reading or writing to disk at an abnormal rate. This slows down the entire node and can fill up the disk.',
    steps: [
      { label: '1. Check PVC usage', cmd: 'kubectl get pvc -n {namespace}' },
      { label: '2. Check pod events', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '3. Check logs for write storms', cmd: 'kubectl logs {pod} -n {namespace} --tail=100' },
      { label: '4. Restart the pod', cmd: 'kubectl rollout restart deployment/{pod} -n {namespace}' },
    ],
    escalate_if: 'Disk is full or PVC is at capacity. Needs storage expansion or log rotation fix.',
  },
  application_crash_loop: {
    title: 'Application Crash Loop Fix',
    what_happened: 'The pod is crashing repeatedly. Kubernetes keeps restarting it but it keeps failing.',
    steps: [
      { label: '1. Check restart count and status', cmd: 'kubectl get pod {pod} -n {namespace}' },
      { label: '2. Read crash logs (previous container)', cmd: 'kubectl logs {pod} -n {namespace} --previous --tail=50' },
      { label: '3. Describe pod for events', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '4. Check all pods in namespace', cmd: 'kubectl get pods -n {namespace}' },
    ],
    escalate_if: 'Always escalate crash loops — the application code or config has a bug that needs a developer fix.',
  },
  application_error_spike: {
    title: 'Application Error Spike Fix',
    what_happened: 'The application is generating errors at an abnormal rate. Users may be seeing failures.',
    steps: [
      { label: '1. Tail live error logs', cmd: 'kubectl logs {pod} -n {namespace} --tail=100' },
      { label: '2. Check previous container logs', cmd: 'kubectl logs {pod} -n {namespace} --previous --tail=50' },
      { label: '3. Check pod events', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '4. Restart the pod', cmd: 'kubectl rollout restart deployment/{pod} -n {namespace}' },
    ],
    escalate_if: 'Errors continue after restart. Application bug needs code fix and redeployment.',
  },
  network_latency_degradation: {
    title: 'Network Latency Fix',
    what_happened: 'Pods are taking longer than normal to communicate. Users experience slow responses.',
    steps: [
      { label: '1. Check all pod statuses', cmd: 'kubectl get pods -n {namespace}' },
      { label: '2. Check network policies', cmd: 'kubectl get networkpolicy -n {namespace}' },
      { label: '3. Check service endpoints', cmd: 'kubectl get endpoints -n {namespace}' },
      { label: '4. Check node resource usage', cmd: 'kubectl top nodes' },
    ],
    escalate_if: 'Latency stays high after investigation. May need network policy or infrastructure change.',
  },
  unknown_anomalous_behavior: {
    title: 'Unknown Anomaly Investigation',
    what_happened: 'An unusual pattern was detected but the root cause could not be automatically classified.',
    steps: [
      { label: '1. Check all pod statuses', cmd: 'kubectl get pods -n {namespace}' },
      { label: '2. Check recent cluster events', cmd: 'kubectl get events -n {namespace} --sort-by=.lastTimestamp' },
      { label: '3. Check pod logs', cmd: 'kubectl logs {pod} -n {namespace} --tail=100' },
      { label: '4. Describe the pod', cmd: 'kubectl describe pod {pod} -n {namespace}' },
      { label: '5. Check resource usage', cmd: 'kubectl top pods -n {namespace}' },
    ],
    escalate_if: 'Escalate if you cannot identify the cause within 15 minutes.',
  },
};

const DEFAULT_PLAYBOOK = PLAYBOOKS['unknown_anomalous_behavior'];

const ROOT_CAUSE_LABELS: Record<string, string> = {
  cpu_saturation: 'CPU Saturation',
  memory_pressure_or_oom: 'Memory Pressure / OOM',
  storage_io_bottleneck: 'Storage I/O Bottleneck',
  network_latency_degradation: 'Network Latency Degradation',
  application_crash_loop: 'Application Crash Loop',
  service_latency_spike: 'Service Latency Spike',
  pod_restart_spike: 'Pod Restart Spike',
  application_error_spike: 'Application Error Spike',
  unknown_anomalous_behavior: 'Unknown Anomalous Behavior',
};

export const IncidentDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [resolved, setResolved] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [checkedSteps, setCheckedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (id) api.getIncidentById(decodeURIComponent(id)).then(setIncident);
  }, [id]);

  if (!incident) {
    return <div className="loading">Loading incident...</div>;
  }

  const pod = incident.affected_pods?.[0] ?? 'unknown-pod';
  const namespace = incident.namespace ?? 'koral-system';
  const playbook = PLAYBOOKS[incident.root_cause] ?? DEFAULT_PLAYBOOK;
  const severity = incident.severity ?? 'medium';

  const fillCmd = (cmd: string) =>
    cmd.replace(/{pod}/g, pod).replace(/{namespace}/g, namespace);

  const copyCmd = (cmd: string) => {
    const filled = fillCmd(cmd);
    navigator.clipboard.writeText(filled).catch(() => {});
    setCopied(filled);
    setTimeout(() => setCopied(null), 2000);
  };

  const toggleStep = (i: number) => {
    setCheckedSteps(prev => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  };

  const aiText = (incident.ai_message || incident.ai_explanation || '')
    .replace(/\*\*/g, '').trim();

  const severityColor: Record<string, string> = {
    critical: '#ff6b6b', high: '#ffa500', medium: '#ffeb3b', low: '#51cf66',
  };
  const color = severityColor[severity] ?? '#888';

  return (
    <div className="incident-details">
      <div className="details-header">
        <div>
          <div className="details-back" onClick={() => navigate('/')}>
            &larr; Back to Dashboard
          </div>
          <h1 className="details-title">{incident.incident_id}</h1>
          <div className="details-meta">
            <span className={`severity-pill ${severity}`}>{severity.toUpperCase()}</span>
            <span className="details-meta-item">Namespace: <code>{namespace}</code></span>
            <span className="details-meta-item">Metric: <code>{incident.primary_metric}</code></span>
            <span className="details-meta-item">Confidence: {incident.confidence != null ? `${(incident.confidence * 100).toFixed(0)}%` : '—'}</span>
          </div>
        </div>
        {resolved && (
          <div className="resolved-badge">RESOLVED</div>
        )}
      </div>

      {aiText && (
        <div className="ai-analysis-box">
          <div className="ai-analysis-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9"/>
              <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
            <span>AI Analysis</span>
            <span className="ai-model-tag">{(incident as any).ai_model ?? 'AI'}</span>
          </div>
          <div className="ai-analysis-text">{aiText}</div>
        </div>
      )}

      <div className="section">
        <h2 className="section-title">What Happened</h2>
        <div className="what-happened-box" style={{ borderLeftColor: color }}>
          <div className="what-happened-cause">
            {ROOT_CAUSE_LABELS[incident.root_cause] ?? incident.root_cause}
          </div>
          <p>{playbook.what_happened}</p>
          {incident.summary && (
            <p className="what-happened-summary">{incident.summary}</p>
          )}
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">Affected Pods</h2>
        <div className="pod-list">
          {incident.affected_pods.map(p => (
            <div key={p} className="pod-chip" style={{ borderColor: color }}>
              <span className="pod-dot" style={{ background: color }}></span>
              {p}
            </div>
          ))}
        </div>
      </div>

      <div className="section">
        <h2 className="section-title">
          Fix Runbook — {playbook.title}
          <span className="runbook-progress">
            {checkedSteps.size}/{playbook.steps.length} steps done
          </span>
        </h2>
        <div className="runbook">
          {playbook.steps.map((step, i) => (
            <div
              key={i}
              className={`runbook-step ${checkedSteps.has(i) ? 'done' : ''}`}
              onClick={() => toggleStep(i)}
            >
              <div className="step-check">
                {checkedSteps.has(i) ? '✓' : i + 1}
              </div>
              <div className="step-body">
                <div className="step-label">{step.label}</div>
                <div className="step-cmd-row">
                  <code className="step-cmd">{fillCmd(step.cmd)}</code>
                  <button
                    className={`copy-btn ${copied === fillCmd(step.cmd) ? 'copied' : ''}`}
                    onClick={e => { e.stopPropagation(); copyCmd(step.cmd); }}
                  >
                    {copied === fillCmd(step.cmd) ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="escalate-box">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <div>
            <strong>Escalate if:</strong> {playbook.escalate_if}
          </div>
        </div>
      </div>

      <div className="resolve-section">
        {!resolved ? (
          <button className="resolve-btn" onClick={() => setResolved(true)}>
            Mark as Resolved
          </button>
        ) : (
          <div className="resolved-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span>Incident marked as resolved. Good work!</span>
          </div>
        )}
        <button className="btn-secondary" onClick={() => navigate('/graph')}>
          View Dependency Graph
        </button>
      </div>
    </div>
  );
};
