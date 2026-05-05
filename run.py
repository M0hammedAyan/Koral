import json
from ai_core.main_engine import run_engine

with open("data/anomalies.json") as f:
    data = json.load(f)

incident, graph = run_engine(data)

print("Incident:", incident)
print("Graph:", graph)

with open("output/incidents.json", "w") as f:
    json.dump(incident, f, indent=4)

with open("output/graph.json", "w") as f:
    json.dump(graph, f, indent=4)

print("Done")