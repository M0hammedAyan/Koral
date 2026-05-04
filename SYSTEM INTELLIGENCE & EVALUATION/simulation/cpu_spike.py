"""CPU Spike Simulation — maxes out CPU to trigger cpu-agent anomaly detection."""
import time

BACKEND_URL = "http://backend.koral-system:8000"
POD_NAME = "cpu-spike-sim"

def run():
    print(f"[cpu_spike] Starting CPU spike on pod: {POD_NAME}")
    while True:
        [x * x for x in range(10 ** 6)]

if __name__ == "__main__":
    run()
