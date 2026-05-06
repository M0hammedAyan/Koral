export interface Anomaly {
  timestamp: number;
  pod: string;
  namespace: string;
  metric: string;
  value: number;
  unit: string;
  z_score: number;
  is_anomaly: boolean;
  window_size: number;
  source: string;
}

export interface Correlation {
  pod_A: string;
  pod_B: string;
  correlation: number;
  lag: number;
}

export interface Incident {
  incident_id: string;
  timestamp: number;
  namespace: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  root_cause: string;
  summary: string;
  affected_pods: string[];
  primary_metric: string;
  confidence: number;
  evidence_count?: number;
  created_at?: number | string;
  ai_explanation?: string;
  ai_message?: string;
  ai_action?: string;
  ai_model?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  status: 'normal' | 'problem';
}

export interface GraphEdge {
  source: string;
  target: string;
  correlation?: number;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface KPIData {
  cpu: number;
  memory: number;
  incidents: number;
  alerts: number;
}

export interface MetricPoint {
  timestamp: number;
  value: number;
}
