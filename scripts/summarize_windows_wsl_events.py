from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys


LEVELS = {"1": "Critical", "2": "Error", "3": "Warning", "4": "Information", "5": "Verbose"}


def severity(event: dict) -> str:
  return LEVELS.get(str(event.get("LevelDisplayName")), str(event.get("LevelDisplayName") or "Unknown"))


def main(path: Path) -> None:
  payload = json.loads(path.read_text(encoding="utf-8-sig"))
  events = payload.get("events", [])
  severity_counts = Counter(severity(event) for event in events)
  high = [event for event in events if severity(event) in {"Error", "Warning", "Critical"}]
  groups = Counter(f"{event.get('LogName')} | {event.get('ProviderName')} | {event.get('Id')}" for event in events)
  result = {
    "schema_version": 1,
    "scope": "descriptive_windows_wsl_gpu_event_summary_only",
    "since": payload.get("since"),
    "until": payload.get("until"),
    "event_count": len(events),
    "severity_counts": dict(sorted(severity_counts.items())),
    "high_severity_event_count": len(high),
    "top_event_groups": [{"count": count, "event": event} for event, count in groups.most_common(10)],
  }
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main(Path(sys.argv[1]))
