"""Unit tests for the Cardinality Guard (Phase 0.2 validation gate)."""
import pytest
from koral.storage.cardinality_guard import CardinalityGuard, CardinalityViolation


@pytest.fixture
def guard():
    g = CardinalityGuard()
    g.MAX_CARDINALITY = 10  # Low limit for testing
    return g


class TestForbiddenLabels:
    def test_reject_request_id(self, guard):
        with pytest.raises(CardinalityViolation, match="Forbidden label"):
            guard.validate({"namespace": "default", "pod": "test", "request_id": "abc123"})

    def test_reject_trace_id(self, guard):
        with pytest.raises(CardinalityViolation, match="Forbidden label"):
            guard.validate({"namespace": "default", "pod": "test", "trace_id": "xyz"})

    def test_reject_user_id(self, guard):
        with pytest.raises(CardinalityViolation, match="Forbidden label"):
            guard.validate({"namespace": "default", "pod": "test", "user_id": "u-1"})

    def test_reject_session_id(self, guard):
        with pytest.raises(CardinalityViolation, match="Forbidden label"):
            guard.validate({"namespace": "default", "pod": "test", "session_id": "sess-1"})


class TestRequiredLabels:
    def test_reject_missing_namespace(self, guard):
        with pytest.raises(CardinalityViolation, match="Missing required"):
            guard.validate({"pod": "test", "metric": "cpu"})

    def test_reject_missing_pod(self, guard):
        with pytest.raises(CardinalityViolation, match="Missing required"):
            guard.validate({"namespace": "default", "metric": "cpu"})

    def test_accept_valid_labels(self, guard):
        # Should not raise
        guard.validate({"namespace": "default", "pod": "api-abc", "container": "main"})


class TestCardinalityLimit:
    def test_reject_exceeding_cardinality(self, guard):
        # Write 10 unique values (at the limit)
        for i in range(10):
            guard.validate({"namespace": "default", "pod": f"pod-{i}"})

        # 11th unique value should fail
        with pytest.raises(CardinalityViolation, match="exceeds cardinality"):
            guard.validate({"namespace": "default", "pod": "pod-overflow"})

    def test_same_value_does_not_increase_cardinality(self, guard):
        # Same value repeated should not count toward limit
        for _ in range(100):
            guard.validate({"namespace": "default", "pod": "same-pod"})
        # Should still pass — only 1 unique value

    def test_reset_clears_tracking(self, guard):
        for i in range(10):
            guard.validate({"namespace": "default", "pod": f"pod-{i}"})

        guard.reset()

        # After reset, should accept again
        guard.validate({"namespace": "default", "pod": "pod-new"})


class TestStats:
    def test_get_stats_returns_counts(self, guard):
        guard.validate({"namespace": "ns1", "pod": "pod-a"})
        guard.validate({"namespace": "ns2", "pod": "pod-b"})

        stats = guard.get_stats()
        assert stats["namespace"] == 2
        assert stats["pod"] == 2
