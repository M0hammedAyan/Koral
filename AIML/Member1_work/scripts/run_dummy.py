"""Run the Project KORAL pipeline against bundled dummy events."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from ai_core import process_events

    events_path = repo_root / "data" / "dummy_events.json"
    events = json.loads(events_path.read_text(encoding="utf-8"))
    incidents = process_events(events, z_threshold=3.0, window_size=300)
    print(json.dumps(incidents, indent=2))


if __name__ == "__main__":
    main()