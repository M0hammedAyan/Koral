from .correlation import lag_correlation 
from .rules import apply_rules 
from .incident_builder import build_incident 
from .dependency_graph import build_graph
from .schemas import validate_anomaly


def run_engine(data):

    # Step 0: validate schema
    for a in data:
        validate_anomaly(a)

    # helper for unique pod identification
    def get_pod_key(a):
        return f"{a.get('namespace','default')}/{a['pod']}"

    # Step 1: filter anomalies (from agents)
    anomalies = [a for a in data if a["is_anomaly"]]

    print("Anomalies:", anomalies)

    # Step 2: correlation (use FULL data, not anomalies)
    edges = []
    best_corr = 0.0

    pods_list = sorted({get_pod_key(a) for a in data})

    for i in range(len(pods_list)):
        for j in range(i + 1, len(pods_list)):

            podA = pods_list[i]
            podB = pods_list[j]

            a_data = [item for item in data if get_pod_key(item) == podA]
            b_data = [item for item in data if get_pod_key(item) == podB]

            # need enough points
            if len(a_data) < 2 or len(b_data) < 2:
                continue

            corr, lag = lag_correlation(a_data, b_data)

            # threshold aligned with your project spec
            if corr > 0.85:

                if lag > 0:
                    source = podA
                    target = podB
                else:
                    source = podB
                    target = podA

                edges.append({
                    "source": source,
                    "target": target,
                    "correlation": float(corr),
                    "lag": int(lag)
                })

                best_corr = max(best_corr, float(corr))

    print("Edges:", edges)
    print("Best correlation:", best_corr)

    # Step 3: rule engine (ONLY anomalies)
    root = apply_rules(anomalies)

    # Step 4: affected pods (consistent with namespace)
    if anomalies:
        affected_pods = list({get_pod_key(a) for a in anomalies})
    else:
        affected_pods = list({get_pod_key(a) for a in data})

    # Step 5: build incident
    incident = build_incident(root, affected_pods, best_corr, anomalies)

    # Step 6: build graph
    graph = build_graph(edges)

    return incident, graph