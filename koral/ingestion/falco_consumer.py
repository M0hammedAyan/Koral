"""
Falco Event Consumer — receives events from Falcosidekick webhook.

Falco events are NOT primary detectors. They serve as gate_3 corroboration
for the 3-of-3 shutdown confirmation. A Falco event alone never triggers action.
"""
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from koral.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FalcoEvent:
    """Parsed Falco event from Falcosidekick webhook."""
    rule: str
    priority: str  # EMERGENCY, CRITICAL, WARNING, NOTICE, INFO
    output: str
    pod_name: str
    namespace: str
    process_name: Optional[str] = None
    parent_process: Optional[str] = None
    file_path: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_koral_tagged(self) -> bool:
        """Returns True if this event has KORAL-specific tags."""
        return "koral" in self.tags

    @property
    def attack_type(self) -> Optional[str]:
        """Infer attack type from Falco tags."""
        tag_set = set(self.tags)
        if "crypto_mining" in tag_set:
            return "CRYPTO_MINING"
        if "data_exfil" in tag_set:
            return "DATA_EXFILTRATION"
        if "container_escape" in tag_set:
            return "CONTAINER_ESCAPE"
        return None


class FalcoEventStore:
    """
    In-memory store for pending Falco events.

    Events are stored per pod with a TTL (default 10 minutes).
    When the classifier asks "has Falco fired for this pod?",
    we check this store.

    Events older than TTL are automatically pruned on access.
    """

    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._events: dict[str, list[FalcoEvent]] = defaultdict(list)

    def _pod_key(self, pod_name: str, namespace: str) -> str:
        return f"{namespace}/{pod_name}"

    def store(self, event: FalcoEvent) -> None:
        """Store a Falco event for later correlation."""
        key = self._pod_key(event.pod_name, event.namespace)
        self._events[key].append(event)
        logger.info(
            f"[falco] Stored event: rule={event.rule} pod={key} "
            f"priority={event.priority} attack_type={event.attack_type}"
        )

    def get_pending(
        self,
        pod_name: str,
        namespace: str,
        window_seconds: Optional[int] = None,
    ) -> list[FalcoEvent]:
        """
        Get Falco events for a pod within the TTL window.
        Prunes expired events before returning.
        """
        key = self._pod_key(pod_name, namespace)
        window = window_seconds or self.ttl_seconds
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window)

        # Prune expired
        self._events[key] = [
            e for e in self._events[key] if e.timestamp > cutoff
        ]

        return self._events[key]

    def has_attack_signal(self, pod_name: str, namespace: str) -> bool:
        """
        Quick check: does this pod have any Falco event that indicates an attack?
        Used by the 3-of-3 shutdown gate as gate_3.
        """
        events = self.get_pending(pod_name, namespace)
        return any(e.attack_type is not None for e in events)

    def clear_pod(self, pod_name: str, namespace: str) -> None:
        """Clear all events for a pod (after incident is resolved)."""
        key = self._pod_key(pod_name, namespace)
        self._events.pop(key, None)


def parse_falcosidekick_payload(payload: dict) -> Optional[FalcoEvent]:
    """
    Parse a Falcosidekick webhook JSON payload into a FalcoEvent.

    Falcosidekick sends payloads in this format:
    {
      "rule": "KORAL Crypto Mining - New Miner Process",
      "priority": "Critical",
      "output": "Crypto miner detected (pod=... namespace=... process=xmrig)",
      "output_fields": {
        "k8s.pod.name": "victim-pod-abc",
        "k8s.ns.name": "default",
        "proc.name": "xmrig",
        "proc.pname": "bash",
        "fd.name": "/dev/null"
      },
      "tags": ["koral", "crypto_mining", "attack"],
      "time": "2025-01-01T00:00:00.000000000Z"
    }
    """
    try:
        output_fields = payload.get("output_fields", {})

        pod_name = output_fields.get("k8s.pod.name", "")
        namespace = output_fields.get("k8s.ns.name", "")

        if not pod_name or not namespace:
            logger.warning("[falco] Event missing pod/namespace, skipping")
            return None

        return FalcoEvent(
            rule=payload.get("rule", "unknown"),
            priority=payload.get("priority", "WARNING").upper(),
            output=payload.get("output", ""),
            pod_name=pod_name,
            namespace=namespace,
            process_name=output_fields.get("proc.name"),
            parent_process=output_fields.get("proc.pname"),
            file_path=output_fields.get("fd.name"),
            destination_ip=output_fields.get("fd.rip"),
            destination_port=int(output_fields["fd.rport"]) if output_fields.get("fd.rport") else None,
            tags=payload.get("tags", []),
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"[falco] Failed to parse payload: {e}")
        return None


# Global instance
falco_store = FalcoEventStore()
