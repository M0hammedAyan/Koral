def calculate_confidence(corr, anomalies):

    metric_count = len(set([a["metric"] for a in anomalies]))
    anomaly_count = len(anomalies)
    # weighted scoring
    score = (corr * 0.5) + (metric_count * 0.2) + (anomaly_count * 0.1)

    return float(round(min(score, 1.0), 2))


def build_incident(root, pods, corr, anomalies):

    confidence = calculate_confidence(corr, anomalies)

    return {
        "incident_id": "INC-001",
        "root_cause": root,
        "confidence": float(round(confidence, 2)),
        "affected_pods": pods
    }