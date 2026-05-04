import axios from 'axios';
import { Incident, Graph, Anomaly } from '../types';

// Relative URLs — React dev proxy forwards to http://localhost:8000
const client = axios.create({ baseURL: '' });

export const api = {
  getIncidents: async (): Promise<Incident[]> => {
    try {
      const { data } = await client.get('/incidents');
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error('[KORAL] /incidents failed:', e);
      return [];
    }
  },

  getGraph: async (): Promise<Graph> => {
    try {
      const { data } = await client.get('/graph');
      return data?.nodes ? data : { nodes: [], edges: [] };
    } catch (e) {
      console.error('[KORAL] /graph failed:', e);
      return { nodes: [], edges: [] };
    }
  },

  getAnomalies: async (): Promise<Anomaly[]> => {
    try {
      const { data } = await client.get('/anomalies');
      console.log('[KORAL] /anomalies count:', Array.isArray(data) ? data.length : data);
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error('[KORAL] /anomalies failed:', e);
      return [];
    }
  },

  getIncidentById: async (id: string): Promise<Incident | null> => {
    const incidents = await api.getIncidents();
    return incidents.find(i => i.incident_id === id) ?? null;
  }
};

export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: ((data: any) => void)[] = [];

  connect() {
    try {
      const wsUrl = `ws://localhost:8000/ws/live`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => console.log('[KORAL] WebSocket connected');
      this.ws.onclose = () => console.log('[KORAL] WebSocket closed');

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach(l => l(data));
        } catch {
          // ignore malformed
        }
      };

      this.ws.onerror = (e) => {
        console.warn('[KORAL] WebSocket error, retrying in 5s', e);
        setTimeout(() => this.connect(), 5000);
      };
    } catch (e) {
      console.warn('[KORAL] WebSocket init failed:', e);
    }
  }

  subscribe(callback: (data: any) => void) {
    this.listeners.push(callback);
  }

  disconnect() {
    this.ws?.close();
  }
}

export const wsService = new WebSocketService();
