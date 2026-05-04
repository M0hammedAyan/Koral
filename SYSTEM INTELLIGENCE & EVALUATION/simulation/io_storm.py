"""PVC I/O Storm Simulation — writes continuously to /data to trigger storage-agent."""
import time
import os

POD_NAME = "io-storm-sim"
DATA_PATH = "/data/test.txt"

def run():
    print(f"[io_storm] Starting I/O storm on pod: {POD_NAME}")
    os.makedirs("/data", exist_ok=True)
    with open(DATA_PATH, "w") as f:
        while True:
            f.write("X" * 10000)
            f.flush()

if __name__ == "__main__":
    run()
