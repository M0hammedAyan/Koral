# KORAL Frontend

Clean, demo-winning React + TypeScript dashboard for KORAL observability system.

## Features

✅ **4 Pages**
- Dashboard (KPIs, charts, incident feed)
- Incident Details (root cause, timeline)
- Dependency Graph (D3.js force-directed)
- Settings (thresholds, auto-refresh)

✅ **Real-Time Updates**
- WebSocket integration
- Live incident feed
- Auto-refreshing charts

✅ **Dark Theme**
- Smooth animations
- Gradient effects
- Professional UX

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Start dev server
npm start

# Build for production
npm run build
```

### Docker Build

```bash
# Build image
docker build -t <dockerhub-username>/koral-frontend:latest .

# Push to registry
docker push <dockerhub-username>/koral-frontend:latest
```

### Deploy to Kubernetes

```bash
# Update Helm chart values with your image
helm upgrade frontend ../charts/frontend \
  -n koral-system \
  --set image.repository=<dockerhub-username>/koral-frontend \
  --set image.tag=latest
```

## Environment Variables

Create `.env` file:

```
REACT_APP_BACKEND_URL=http://backend.koral-system:8000
```

For local testing with port-forwarding:

```
REACT_APP_BACKEND_URL=http://localhost:8000
```

## Architecture

```
src/
├── components/       # Reusable UI components
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── KPICard.tsx
│   └── IncidentCard.tsx
├── pages/           # Route pages
│   ├── Dashboard.tsx
│   ├── Incidents.tsx
│   ├── IncidentDetails.tsx
│   ├── DependencyGraph.tsx
│   └── Settings.tsx
├── services/        # API & WebSocket
│   └── api.ts
├── types/           # TypeScript definitions
│   └── index.ts
└── styles/          # CSS modules
```

## API Integration

### REST Endpoints

- `GET /incidents` - Fetch all incidents
- `GET /graph` - Fetch dependency graph
- `GET /anomalies` - Fetch anomalies

### WebSocket

- `ws://backend:8000/ws/live` - Real-time updates

## Demo Flow

1. Open dashboard → see KPIs and charts
2. Trigger simulation (I/O storm)
3. Watch incident appear in feed (real-time)
4. Click "View Details" → see root cause
5. Click "View Graph" → see D3.js visualization
6. Hover nodes → highlight connections
7. Go to Settings → adjust thresholds

## Tech Stack

- React 18
- TypeScript
- React Router
- Recharts (time-series)
- D3.js (graph)
- Axios (HTTP)
- WebSocket (real-time)

## Port

Frontend runs on port **3000** (NodePort **30080** in Kubernetes)

Access via:
```bash
minikube service frontend -n koral-system
```

## Notes

- No business logic in frontend
- All data from backend APIs
- WebSocket for real-time feel
- Responsive design (desktop-first)
- Dark theme optimized for demos
