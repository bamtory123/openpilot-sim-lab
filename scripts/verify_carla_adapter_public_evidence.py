from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_carla_adapter_public_evidence import SCOPE, build_evidence, render_summary


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify generated public CARLA adapter-pilot evidence")
  parser.add_argument("summary", type=Path)
  parser.add_argument("--output-dir", type=Path, required=True)
  parser.add_argument("--departure-contract", required=True,
                      choices=("historical_lane_sensor_event_pre_route_ground_truth_threshold",
                               "route_lateral_error_threshold"))
  args = parser.parse_args()
  expected = build_evidence(args.summary, args.departure_contract)
  actual = json.loads((args.output_dir / "evidence.json").read_text(encoding="utf-8"))
  if actual != expected:
    raise SystemExit("public CARLA adapter evidence differs from retained source")
  if (args.output_dir / "README.md").read_text(encoding="utf-8") != render_summary(expected):
    raise SystemExit("public CARLA adapter summary differs from generated evidence")
  print(json.dumps({"schema_version": 1, "scope": SCOPE, "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
  main()
