from collections import deque
from base_agent import compute_z_score, HISTORY_SIZE


def test_z_score_normal():
    history = deque([10, 11, 9, 10, 11, 9, 10, 11, 9, 10], maxlen=HISTORY_SIZE)
    z = compute_z_score(history, 10)
    assert abs(z) < 1.0


def test_z_score_spike():
    history = deque([10, 11, 9, 10, 11, 9, 10, 11, 9, 10], maxlen=HISTORY_SIZE)
    z = compute_z_score(history, 100)
    assert z > 2.5


def test_z_score_insufficient_history():
    history = deque([5], maxlen=HISTORY_SIZE)
    assert compute_z_score(history, 100) == 0.0


def test_z_score_negative_spike():
    history = deque([100, 101, 99, 100, 101, 99, 100, 101, 99, 100], maxlen=HISTORY_SIZE)
    z = compute_z_score(history, 1)
    assert z < -2.5


def test_anomaly_flag():
    history = deque([10, 11, 9, 10, 11, 9, 10, 11, 9, 10], maxlen=HISTORY_SIZE)
    z = compute_z_score(history, 100)
    assert abs(z) > 2.5
