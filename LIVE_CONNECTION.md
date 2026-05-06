# How to Connect KORAL to a Real Server

## What the agents actually do (plain English)

Each agent runs in a loop every 10 seconds:
1. Asks Prometheus: "what is the current CPU/memory/storage of all pods?"
2. Computes a z-score (how abnormal is this value vs the last 30 readings?)
3. If z-score > 2.5 → marks it as an anomaly
4. Sends the result to the backend → backend calls correlation engine → incident appears on dashboard

So the ONLY thing you need to change to connect to a real server is:
  PROMETHEUS_URL = "http://<your-server-ip>:9090"

That's it. The agents do the rest automatically.

---

## What you need on your server

Your server needs Prometheus running and scraping your pods/containers.

### Option A — Your server already has Prometheus
Just find the IP and port. Usually: http://<server-ip>:9090
Test it: open http://<server-ip>:9090/graph in your browser
If you see the Prometheus UI → you're ready.

### Option B — Your server does NOT have Prometheus
Install it with Docker in 1 command:

  docker run -d \
    --name prometheus \
    -p 9090:9090 \
    -v /proc:/host/proc:ro \
    -v /sys:/host/sys:ro \
    prom/prometheus

Then install node_exporter to get CPU/memory metrics:

  docker run -d \
    --name node-exporter \
    --pid="host" \
    -p 9100:9100 \
    -v /proc:/host/proc:ro \
    -v /sys:/host/sys:ro \
    quay.io/prometheus/node-exporter

---

## How to run agents pointing at your real server

### Locally (for testing)

Open 4 PowerShell windows:

Window 1 - Correlation Engine:
  cd d:\KORAL\correlation-engine
  uvicorn main:app --host 0.0.0.0 --port 8005

Window 2 - Backend:
  cd d:\KORAL
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

Window 3 - CPU Agent pointing at YOUR server:
  cd d:\KORAL\agents
  set PROMETHEUS_URL=http://<your-server-ip>:9090
  set NAMESPACE=default
  set POD_NAME=my-cpu-agent
  set BACKEND_URL=http://localhost:8000
  python cpu-agent/main.py

Window 4 - Memory Agent:
  cd d:\KORAL\agents
  set PROMETHEUS_URL=http://<your-server-ip>:9090
  set NAMESPACE=default
  set POD_NAME=my-memory-agent
  set BACKEND_URL=http://localhost:8000
  python memory-agent/main.py

Window 5 - Frontend:
  cd d:\KORAL\frontend
  npm start

Replace <your-server-ip> with your actual server IP.
Replace default with your actual Kubernetes namespace.

---

## What happens then (the live flow)

  Your server runs pods
        |
        | Prometheus scrapes metrics every 15s
        v
  Prometheus at http://<your-server-ip>:9090
        |
        | Agent queries every 10s
        v
  cpu-agent / memory-agent / storage-agent / log-agent
        |
        | POST /anomalies (with z-score)
        v
  Backend at localhost:8000
        |
        | if anomaly → POST /correlate
        v
  Correlation Engine at localhost:8005
        |
        | runs RCA → returns incident
        v
  Backend broadcasts via WebSocket
        |
        v
  Dashboard at localhost:3000 updates in real time

---

## What the dashboard shows for real server data

- CPU chart: actual CPU usage of all pods in your namespace
- Memory chart: actual memory usage in MB
- Anomaly banner: fires when any metric spikes abnormally
- Incident cards: "CPU Saturation on pod-xyz" with confidence %
- Graph page: shows which pods are affected and how they relate

---

## Common Prometheus queries the agents use

CPU agent query:
  sum(rate(container_cpu_usage_seconds_total{namespace="<your-namespace>"}[1m])) by (pod)

Memory agent query:
  sum(container_memory_working_set_bytes{namespace="<your-namespace>"}) by (pod)

Storage agent query:
  sum(rate(container_fs_writes_bytes_total{namespace="<your-namespace>"}[1m])) by (pod)

You can test these directly in Prometheus UI at http://<your-server-ip>:9090/graph
If they return data → the agents will work.
If they return empty → your Prometheus is not scraping containers yet.

---

## Quick test: is my Prometheus returning data?

Run this in PowerShell (replace the IP):

  curl "http://<your-server-ip>:9090/api/v1/query?query=up"

If you get {"status":"success",...} → Prometheus is working.
If you get connection refused → Prometheus is not running or port is blocked.
