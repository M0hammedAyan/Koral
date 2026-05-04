export interface Anomaly {
  timestamp: number;
  pod: string;
  metric: string;
  value: number;
  z_score: number;
  is_anomaly: boolean;
}

export interface Correlation {
  pod_A: string;
  pod_B: string;
  correlation: number;
  lag: number;
}

export interface Incident {
  incident_id: string;
  root_cause: string;
  confidence: number;
  affected_pods: string[];
  timestamp?: number;
  severity?: 'Critical' | 'High' | 'Medium' | 'Low';
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
