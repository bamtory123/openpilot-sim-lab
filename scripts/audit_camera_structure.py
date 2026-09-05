#!/usr/bin/env python3
"""Compare non-semantic image structure across simulator and real-camera frame sets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simlab.camera_domain import aggregate_scene_structure


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--sim-frame", type=Path, required=True, nargs="+")
  parser.add_argument("--reference-frame", type=Path, required=True, nargs="+")
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()

  simulator = aggregate_scene_structure(args.sim_frame)
  reference = aggregate_scene_structure(args.reference_frame)
  result = {
    "schema_version": 1,
    "scope": "unmatched_scene_structure_diagnostic_not_segmentation_accuracy_or_driving_performance",
    "simulator": simulator,
    "reference": reference,
    "relative": {
      band: {
        metric: (simulator["bands"][band][metric] / value if value else None)
        for metric, value in reference["bands"][band].items()
      }
      for band in ("upper", "horizon", "lower")
    },
    "limitations": [
      "frame_sets_are_not_scene_matched",
      "fixed_vertical_bands_are_not_semantic_masks",
      "ratios_identify_domain_shift_but_not_model_causality",
    ],
  }
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
