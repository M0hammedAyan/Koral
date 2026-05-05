def apply_rules(anomalies):

    metrics = [a["metric"] for a in anomalies]

    if "pvc_io" in metrics and "cpu" in metrics:
        return "Storage I/O spike caused CPU overload"

    if "pvc_io" in metrics and "restart" in metrics:
        return "Storage pressure caused pod restart"

    if "cpu" in metrics and "log_error" in metrics:
        return "Application failure under load"

    if "memory" in metrics and "oom_kill" in metrics:
        return "Memory leak detected"

    if "network" in metrics and "latency" in metrics:
        return "Network congestion issue"

    if "disk" in metrics and "restart" in metrics:
        return "Disk exhaustion caused crash"

    return "Root cause unclear"