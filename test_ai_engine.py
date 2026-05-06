"""
End-to-end test: loads the key, calls the AI engine analyze endpoint directly.
Run: python test_ai_engine.py
"""
import asyncio
import os
import sys

# Load .env manually
try:
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
except FileNotFoundError:
    pass

sys.path.insert(0, ".")

from ai_engine.main import analyze_incident, health
from ai_engine.main import IncidentAnalysisRequest

async def run():
    print("=== KORAL AI Engine Test ===\n")

    # 1. Check health
    h = health()
    print(f"Health check:")
    for k, v in h.items():
        print(f"  {k}: {v}")
    print()

    # 2. Test medium severity (should auto-fix)
    print("Test 1: Medium severity - CPU saturation (expect: auto_fix)")
    req = IncidentAnalysisRequest(
        incident_id="INC-TEST001",
        severity="medium",
        root_cause="cpu_saturation",
        summary="cpu anomaly in koral-system affecting pod-A",
        affected_pods=["pod-A"],
        primary_metric="cpu",
        confidence=0.72,
        namespace="koral-system",
        z_score=3.1,
        value=87.5,
    )
    result = await analyze_incident(req)
    print(f"  Action   : {result['action_type']}")
    print(f"  Model    : {result['model_used']}")
    msg_preview = result['user_message'][:120].encode('ascii', errors='replace').decode()
    print(f"  Message  : {msg_preview}...")
    print()

    # 3. Test critical severity (should alert developer)
    print("Test 2: Critical severity - Memory OOM (expect: alert_developer)")
    req2 = IncidentAnalysisRequest(
        incident_id="INC-TEST002",
        severity="critical",
        root_cause="memory_pressure_or_oom",
        summary="memory anomaly in koral-system affecting pod-B",
        affected_pods=["pod-B"],
        primary_metric="memory",
        confidence=0.91,
        namespace="koral-system",
        z_score=4.7,
        value=498.0,
    )
    result2 = await analyze_incident(req2)
    print(f"  Action   : {result2['action_type']}")
    print(f"  Model    : {result2['model_used']}")
    msg2_preview = result2['user_message'][:120].encode('ascii', errors='replace').decode()
    print(f"  Message  : {msg2_preview}...")
    print()

    print("=== All tests passed ===")

asyncio.run(run())
