"""Feedback Loop — adjusts thresholds when backend reports false positives."""
import json
import os

THRESHOLD_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "threshold", "thresholds.json"
)
FEEDBACK_LOG = os.path.join(os.path.dirname(__file__), "feedback_log.json")
STEP_UP = 0.2      # increase k when false positive
STEP_DOWN = 0.1    # decrease k when confirmed true positive
MAX_K = 4.0
MIN_K = 1.5


def _load(path: str) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def process_feedback(incident_id: str, metric: str, is_correct: bool) -> dict:
    """
    Call this when backend sends feedback on an incident.
    is_correct=False → false positive → raise threshold
    is_correct=True  → confirmed → slightly lower threshold
    """
    cfg = _load(THRESHOLD_CONFIG)
    key = f"{metric}_threshold"
    old = cfg.get(key, 2.5)

    if not is_correct:
        new = min(round(old + STEP_UP, 2), MAX_K)
    else:
        new = max(round(old - STEP_DOWN, 2), MIN_K)

    cfg[key] = new
    _save(THRESHOLD_CONFIG, cfg)

    record = {
        "incident_id": incident_id,
        "metric": metric,
        "is_correct": is_correct,
        "old_threshold": old,
        "new_threshold": new
    }

    log = _load(FEEDBACK_LOG) if os.path.exists(FEEDBACK_LOG) else []
    if not isinstance(log, list):
        log = []
    log.append(record)
    _save(FEEDBACK_LOG, log)

    return record
