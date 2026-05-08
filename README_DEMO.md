KORAL Hackathon Demo — Recording Runbook

Overview
- Purpose: Start a visually-clean demo environment and trigger synthetic incidents.

Quick start (one-liners)
- Build + Start demo stack:
  docker compose -f docker-compose-prod.yml -f docker-compose.demo.yml up -d --build
- Trigger synthetic incidents:
  scripts/generate_incidents.sh

Key URLs
- Frontend dashboard: http://localhost:3000
- Prometheus targets / graph: http://localhost:9090

Recommended recording sequence
1. In a single terminal: `docker ps` (use `--format` to keep output short).
2. Open browser: frontend URL (show landing, incident feed, graphs).
3. Show Prometheus `Targets` page (open http://localhost:9090/targets). Ensure UP.
4. Run `scripts/generate_incidents.sh` to start sim containers.
5. In terminal show `docker stats --no-stream` for 2–3 seconds to capture spike.
6. Switch to frontend — incident cards should appear and update.
7. Show correlation engine logs or AI summary (curl backend `/incidents/latest` if available).

Clean terminal commands for recording
- Show running containers (compact):
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
- Show pods (Kubernetes):
  kubectl get pods --all-namespaces --no-headers -o wide
- Tail single service logs (clean):
  docker compose logs --no-color --tail=200 backend
- Check Prometheus targets:
  open http://localhost:9090/targets

Stopping demo sims
- Stop simulators:
  docker rm -f koral-sim-cpu koral-sim-memory koral-sim-storage || true

Notes & Tips
- Use a single terminal window for each visual: one `docker ps`, one `docker compose logs --tail=200 backend`, one `docker compose logs --tail=200 koral-prometheus`.
- Use browser full-screen mode and hide bookmarks/toolbars for clean recording.
