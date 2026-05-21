# API Reference

This repository exposes a FastAPI backend. The live OpenAPI docs are available at `/docs` when the backend is running.

Endpoints (high level):
- `POST /anomalies` — receive anomaly events
- `GET /incidents` — list incidents
- `POST /incidents/{id}/feedback` — submit analyst feedback

For full API schema, run the backend locally and visit `http://localhost:8000/docs`.
