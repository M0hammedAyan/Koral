def validate_anomaly(a):
    required = [
        "timestamp",
        "pod",
        "namespace",
        "metric",
        "value",
        "unit",
        "z_score",
        "is_anomaly",
        "window_size",
        "source"
    ]

    for key in required:
        if key not in a:
            raise ValueError(f"Missing field: {key}")

    if not isinstance(a["is_anomaly"], bool):
        raise ValueError("is_anomaly must be boolean")