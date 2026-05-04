"""Memory Leak Simulation — continuously allocates memory to trigger memory-agent."""
import time

POD_NAME = "memory-leak-sim"

def run():
    print(f"[memory_leak] Starting memory leak on pod: {POD_NAME}")
    arr = []
    while True:
        arr.append("leak" * 10000)
        time.sleep(0.01)

if __name__ == "__main__":
    run()
