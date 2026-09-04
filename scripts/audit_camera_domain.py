#!/usr/bin/env python3
"""Derive a bounded simulator RGB affine diagnostic from road-camera reference frames."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simlab.camera_domain import aggregate_statistics, color_affine


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--sim-frame", type=Path, required=True, nargs="+")
  parser.add_argument("--reference-frame", type=Path, required=True, nargs="+")
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  simulator, reference = aggregate_statistics(args.sim_frame), aggregate_statistics(args.reference_frame)
  result = {"schema_version": 1, "scope": "camera_domain_moment_match_diagnostic_not_perception_or_road_performance",
            "simulator": simulator, "reference": reference, "recommended_environment_overlay": {
              "camera_color_affine": color_affine(simulator, reference)},
            "limitations": ["matches lower-region RGB moments only", "does_not_measure_lane_semantics_or_model_accuracy",
                            "requires_closed_loop_evaluation_before_any_candidate_claim"]}
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
