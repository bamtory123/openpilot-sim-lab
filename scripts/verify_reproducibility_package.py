from __future__ import annotations

import json
from pathlib import Path
import sys


def main(root: Path) -> None:
  summaries = list(root.rglob("summary.json"))
  if len(summaries) != 1:
    raise SystemExit(f"expected one probe summary, found {len(summaries)}")
  summary = json.loads(summaries[0].read_text(encoding="utf-8"))
  attempt = json.loads(next(root.rglob("attempt.json")).read_text(encoding="utf-8"))
  required = {"validity": "valid", "outcome": "pass"}
  if any(summary.get(key) != value for key, value in required.items()):
    raise SystemExit("probe did not complete valid/pass")
  metrics = summary.get("metrics", {})
  if metrics.get("camera_frames_published") != 200 or metrics.get("camera_frames_dropped") != 0:
    raise SystemExit("camera transport contract was not met")
  if not attempt.get("scenario_hash") or not Path(attempt["scenario_snapshot"]).is_file():
    raise SystemExit("attempt provenance is incomplete")
  result = {"schema_version": 1, "status": "pass", "summary": str(summaries[0]),
            "scenario_hash": attempt["scenario_hash"], "wsl_boot_changed": attempt.get("wsl_boot_changed")}
  (root / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
  main(Path(sys.argv[1]))
