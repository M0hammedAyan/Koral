# KORAL Frontend — Complete Implementation Guide

## 🎯 What Was Built

A **production-ready React + TypeScript dashboard** with:

✅ 4 complete pages (Dashboard, Incidents, Graph, Settings)
✅ Real-time WebSocket integration
✅ D3.js force-directed dependency graph
✅ Recharts time-series visualization
✅ Dark theme with smooth animations
✅ Responsive design
✅ Docker + Kubernetes ready

---

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html              # HTML entry point
├── src/
│   ├── components/             # Reusable components
│   │   ├── Header.tsx          # Top bar with status
│   │   ├── Sidebar.tsx         # Navigation menu
│   │   ├── KPICard.tsx         # Metric cards
│   │   └── IncidentCard.tsx    # Incident feed item
│   ├── pages/                  # Route pages
│   │   ├── Dashboard.tsx       # Main page (KPIs + charts + feed)
│   │   ├── Incidents.tsx       # All incidents list
│   │   ├── IncidentDetails.tsx # Single incident view
│   │   ├── DependencyGraph.tsx # D3.js graph
│   │   └── Settings.tsx        # Threshold controls
│   ├── services/
│   │   └── api.ts              # REST + WebSocket service
│   ├── types/
│   │   └── index.ts            # TypeScript interfaces
│   ├── styles/                 # CSS files (dark theme)
│   │   ├── Header.css
│   │   ├── Sidebar.css
│   │   ├── Dashboard.css
│   │   ├── KPICard.css
│   │   ├── IncidentCard.css
│   │   ├── IncidentDetails.css
│   │   ├── DependencyGraph.css
│   │   ├── Settings.css
│   │   └── Incidents.css
│   ├── App.tsx                 # Main app with routing
│   ├── App.css                 # Global styles
│   └── index.tsx               # React entry point
├── Dockerfile                  # Multi-stage build
├── nginx.conf                  # Nginx config for SPA
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── .env                        # Environment variables
└── README.md                   # Documentation
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Local Development

```bash
# Start dev server (port 3000)
npm start
```

### 3. Build for Production

```bash
npm run build
```

### 4. Docker Build & Push

```bash
# Build image
docker build -t <your-dockerhub>/koral-frontend:latest .

# Push to registry
docker push <your-dockerhub>/koral-frontend:latest
```

### 5. Deploy to Kubernetes

```bash
# Update Helm chart
helm upgrade frontend ../charts/frontend \
  -n koral-system \
  --set image.repository=<your-dockerhub>/koral-frontend \
  --set image.tag=latest

# Access dashboard
minikube service frontend -n koral-system
```

---

## 🎨 Pages Overview

### 1. Dashboard (`/`)

**Components:**
- 4 KPI cards (CPU, Memory, Incidents, Alerts)
- 3 real-time charts (CPU, Memory, Storage)
- Incident feed (right panel)

**Features:**
- Auto-refresh every 10s
- WebSocket live updates
- Color-coded severity
- Click incident → details page

### 2. Incidents (`/incidents`)

**Components:**
- Filter buttons (All, Critical, High)
- Grid of incident cards

**Features:**
- Filter by severity
- Click card → details page

### 3. Incident Details (`/incident/:id`)

**Components:**
- Root cause (big text box)
- Confidence badge
- Affected pods list
- Timeline visualization

**Features:**
- Back to dashboard button
- View graph button

### 4. Dependency Graph (`/graph`)

**Components:**
- D3.js force-directed graph
- Legend (normal/problem)
- Node details panel

**Features:**
- Drag nodes
- Click node → show details
- Hover → enlarge
- Color-coded status (green/red)

### 5. Settings (`/settings`)

**Components:**
- Auto-refresh toggle
- Threshold inputs (CPU, Memory, Storage)

**Features:**
- Save to localStorage
- Reset to defaults

---

## 🔌 API Integration

### REST Endpoints

```typescript
// Get all incidents
GET /incidents
Response: Incident[]

// Get dependency graph
GET /graph
Response: { nodes: GraphNode[], edges: GraphEdge[] }

// Get anomalies
GET /anomalies
Response: Anomaly[]
```

### WebSocket

```typescript
// Connect to live feed
ws://backend:8000/ws/live

// Message format
{
  type: 'incident' | 'anomaly',
  payload: Incident | Anomaly
}
```

---

## 🎨 Design System

### Colors

```css
Background: #0a0a0a, #1a1a1a
Primary: #00d4ff (cyan)
Success: #51cf66 (green)
Error: #ff6b6b (red)
Warning: #ffa500 (orange)
Text: #e0e0e0
```

### Animations

- Fade in: 0.5s ease
- Slide in: 0.3s ease
- Hover lift: translateY(-5px)
- Pulse: 2s infinite

---

## 📊 Data Flow

```
Backend API → api.ts → React State → Components → UI
                ↓
          WebSocket → Live Updates → State Update → Re-render
```

---

## 🧪 Demo Scenario

1. **Open Dashboard**
   - See 4 KPI cards
   - Charts show baseline metrics

2. **Trigger Simulation**
   ```bash
   kubectl apply -f infra/k8s/simulation/io-storm.yaml
   ```

3. **Watch Real-Time Updates**
   - Incident appears in feed (WebSocket)
   - KPI cards update
   - Charts show spike

4. **Click "View Details"**
   - See root cause: "PVC I/O spike caused CPU surge"
   - Confidence: 92%
   - Timeline visualization

5. **Click "View Dependency Graph"**
   - D3.js graph loads
   - Red nodes = problem pods
   - Green nodes = healthy
   - Drag and interact

6. **Go to Settings**
   - Adjust CPU threshold: 2.5 → 3.0
   - Save settings

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to backend"

**Solution:**
```bash
# Check backend is running
kubectl get pods -n koral-system | grep backend

# Port-forward for local testing
kubectl port-forward svc/backend 8000:8000 -n koral-system

# Update .env
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Issue: "WebSocket connection failed"

**Solution:**
- Ensure backend WebSocket endpoint is `/ws/live`
- Check nginx.conf has WebSocket proxy config
- Verify backend supports WebSocket upgrade

### Issue: "Graph not rendering"

**Solution:**
- Check browser console for D3 errors
- Verify `/graph` endpoint returns valid data
- Ensure nodes have `id`, `label`, `status`
- Ensure edges have `source`, `target`

### Issue: "Charts empty"

**Solution:**
- Verify `/anomalies` endpoint returns data
- Check anomalies have `metric`, `value`, `timestamp`
- Ensure at least one agent is sending data

---

## 🔧 Customization

### Change Theme Colors

Edit `src/App.css`:
```css
/* Change primary color */
--primary: #00d4ff;  /* Change to your color */
```

### Add New Page

1. Create `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`:
   ```tsx
   <Route path="/new" element={<NewPage />} />
   ```
3. Add menu item in `src/components/Sidebar.tsx`

### Modify Chart Colors

Edit chart components:
```tsx
<Line stroke="#00d4ff" />  // Change color
```

---

## 📦 Dependencies

```json
{
  "react": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "recharts": "^2.10.0",
  "d3": "^7.8.5",
  "axios": "^1.6.0",
  "typescript": "^5.3.0"
}
```

---

## 🚢 Deployment Checklist

- [ ] Update `.env` with correct backend URL
- [ ] Build Docker image
- [ ] Push to DockerHub
- [ ] Update Helm chart values
- [ ] Deploy to Kubernetes
- [ ] Verify service is running
- [ ] Test WebSocket connection
- [ ] Trigger simulation
- [ ] Verify real-time updates

---

## 🎯 Demo Tips

1. **Start with clean state** - No incidents initially
2. **Trigger I/O storm** - Most impressive demo
3. **Show real-time feed** - Incident appears within 30s
4. **Explain root cause** - Plain English explanation
5. **Show graph** - Visual dependency mapping
6. **Adjust thresholds** - Show configurability

---

## 📝 Notes

- Frontend is **read-only** - no write operations
- All logic in backend/correlation engine
- WebSocket for real-time feel
- D3.js graph is interactive
- Dark theme optimized for presentations
- Responsive (desktop-first)

---

## ✅ Completion Status

✅ All 4 pages implemented
✅ REST API integration
✅ WebSocket real-time updates
✅ D3.js dependency graph
✅ Recharts time-series
✅ Dark theme with animations
✅ Docker + Kubernetes ready
✅ TypeScript type safety
✅ Production build optimized

**Status: READY FOR DEMO** 🚀
