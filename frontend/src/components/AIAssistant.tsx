import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { api } from '../services/api';
import './AIAssistant.css';

// In dev (port 3000), call AI engine directly on 8006
// In production (nginx), go through /ai/ proxy
const AI_BASE = window.location.port === '3000'
  ? 'http://localhost:8006'
  : '';

const aiClient = axios.create({ baseURL: AI_BASE });

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  model?: string;
  timestamp: string;
}

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  auto_fix:        { label: 'Auto-Fixed',        color: '#51cf66' },
  report:          { label: 'Reported to You',   color: '#ffa500' },
  alert_developer: { label: 'Developer Alerted', color: '#ff6b6b' },
};

export const AIAssistant: React.FC = () => {
  const [chat, setChat]       = useState<ChatMessage[]>([]);
  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const [tab, setTab]         = useState<'activity' | 'chat'>('activity');
  const [aiIncidents, setAiIncidents] = useState<any[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load incidents that already have AI explanations
  const loadAIData = useCallback(async () => {
    const incidents = await api.getIncidents();
    const withAI = incidents
      .filter((i: any) => i.ai_explanation || i.ai_message)
      .reverse();
    setAiIncidents(withAI);
  }, []);

  useEffect(() => {
    loadAIData();

    // WebSocket — direct to backend port 8000 in dev
    const isDev = window.location.port === '3000';
    const host  = isDev ? 'localhost:8000' : window.location.host;
    const ws    = new WebSocket(`ws://${host}/ws/live`);

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'incident_ai' && msg.payload?.ai_message) {
          // New AI analysis arrived — add to activity and show in chat
          setAiIncidents(prev => [msg.payload, ...prev]);
          setChat(prev => [...prev, {
            role: 'ai',
            text: msg.payload.ai_message,
            model: msg.payload.ai_model,
            timestamp: new Date().toISOString(),
          }]);
          setTab('chat');
        }
      } catch {}
    };

    return () => ws.close();
  }, [loadAIData]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setChat(prev => [...prev, {
      role: 'user', text: userMsg,
      timestamp: new Date().toISOString(),
    }]);
    setLoading(true);

    try {
      // Build context from latest incidents for better AI answers
      const context = {
        recent_incidents: aiIncidents.slice(0, 3).map(i => ({
          id: i.incident_id,
          severity: i.severity,
          root_cause: i.root_cause,
          summary: i.summary,
          pods: i.affected_pods,
        })),
      };

      const { data } = await aiClient.post('/chat', { message: userMsg, context });
      setChat(prev => [...prev, {
        role: 'ai',
        text: data.response,
        model: data.model,
        timestamp: data.timestamp,
      }]);
    } catch (e) {
      setChat(prev => [...prev, {
        role: 'ai',
        text: 'Could not reach AI engine. Make sure it is running on port 8006.',
        timestamp: new Date().toISOString(),
      }]);
    }
    setLoading(false);
  };

  const fmt = (ts: string | number) => {
    try {
      const d = typeof ts === 'number' ? new Date(ts * 1000) : new Date(ts);
      return d.toLocaleTimeString();
    } catch { return ''; }
  };

  return (
    <div className="ai-assistant">
      <div className="ai-header">
        <div className="ai-title">
          <span className="ai-icon">&#129302;</span>
          <span>KORAL AI</span>
        </div>
        <div className="ai-tabs">
          <button className={tab === 'activity' ? 'active' : ''} onClick={() => setTab('activity')}>
            Activity
            {aiIncidents.length > 0 && <span className="badge">{aiIncidents.length}</span>}
          </button>
          <button className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>
            Chat
          </button>
        </div>
      </div>

      {/* ── ACTIVITY TAB ── */}
      {tab === 'activity' && (
        <div className="ai-activity-list">
          {aiIncidents.length === 0 ? (
            <div className="ai-empty">
              <div style={{ fontSize: '2rem' }}>&#128269;</div>
              <div>No AI activity yet</div>
              <div className="ai-empty-sub">AI analyses incidents automatically when they occur</div>
            </div>
          ) : (
            aiIncidents.map((inc, i) => {
              const action = ACTION_LABELS[inc.ai_action] ?? { label: inc.ai_action, color: '#888' };
              return (
                <div key={inc.incident_id ?? i} className={`ai-activity-card ${inc.severity}`}>
                  <div className="ai-activity-header">
                    <span className="ai-action-label" style={{ color: action.color }}>
                      {action.label}
                    </span>
                    <span className="ai-activity-time">{fmt(inc.created_at ?? inc.timestamp)}</span>
                  </div>
                  <div className="ai-activity-incident">{inc.incident_id}</div>
                  <div className="ai-activity-message">
                    {inc.ai_message || inc.ai_explanation}
                  </div>
                  <div className="ai-activity-footer">
                    <span className="ai-model-badge">{inc.ai_model ?? 'GPT-4o'}</span>
                    <span className="ai-pods">
                      {Array.isArray(inc.affected_pods)
                        ? inc.affected_pods.join(', ')
                        : inc.affected_pods}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ── CHAT TAB ── */}
      {tab === 'chat' && (
        <div className="ai-chat">
          <div className="ai-chat-messages">
            {chat.length === 0 && (
              <div className="ai-chat-welcome">
                <div className="ai-welcome-icon">&#129302;</div>
                <div>Hi! I am KORAL AI powered by GPT-4o.</div>
                <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '0.25rem' }}>
                  Ask me about your incidents, pods, or cluster health.
                </div>
                <div className="ai-suggestions">
                  {[
                    "What happened to web-server-pod?",
                    "Why is CPU critical?",
                    "How do I fix CPU saturation?",
                    "What should the developer do now?",
                  ].map(s => (
                    <button key={s} className="ai-suggestion" onClick={() => setInput(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chat.map((msg, i) => (
              <div key={i} className={`ai-message ${msg.role}`}>
                <div className="ai-message-bubble">
                  {msg.text.split('\n').map((line, j) => (
                    <p key={j}>{line}</p>
                  ))}
                </div>
                <div className="ai-message-meta">
                  {msg.role === 'ai' && msg.model && (
                    <span className="ai-model-badge">{msg.model}</span>
                  )}
                  <span className="ai-message-time">{fmt(msg.timestamp)}</span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="ai-message ai">
                <div className="ai-message-bubble ai-typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="ai-chat-input">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Ask KORAL AI anything..."
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()}>
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
