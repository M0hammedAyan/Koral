"""Log Error Burst Simulation — emits structured JSON errors to trigger log-agent."""
import time
import json
from datetime import datetime, timezone

POD_NAME = "log-error-gen-sim"

def run():
    print(f"[network_latency] Starting log error burst on pod: {POD_NAME}")
    while True:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR",
            "pod": POD_NAME,
            "message": "database connection failed",
            "latency_ms": 9999
        }
        print(json.dumps(entry), flush=True)
        time.sleep(0.5)

if __name__ == "__main__":
    run()
