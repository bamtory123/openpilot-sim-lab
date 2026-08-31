from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def audit_dataset(root: Path) -> dict:
  samples = []
  for path in sorted(root.glob("*/dataset_manifest.jsonl")):
    samples.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
  curvature = [float(sample["labels"].get("reference_curvature_1pm") or 0.0) for sample in samples]
  traffic_distance = [float(sample["labels"]["traffic_nearest_distance_m"]) for sample in samples
                      if sample["labels"].get("traffic_nearest_distance_m") not in (None, "")]
  traffic_ttc = [float(sample["labels"]["traffic_nearest_ttc_s"]) for sample in samples
                 if sample["labels"].get("traffic_nearest_ttc_s") not in (None, "")]
  return {
    "sample_count": len(samples),
    "split_counts": dict(sorted(Counter(sample["split"] for sample in samples).items())),
    "curved_sample_count": sum(abs(value) > 0.005 for value in curvature),
    "reference_curvature_min_1pm": min(curvature, default=None),
    "reference_curvature_max_1pm": max(curvature, default=None),
    "traffic_labeled_sample_count": len(traffic_distance),
    "traffic_nearest_distance_min_m": min(traffic_distance, default=None),
    "traffic_nearest_ttc_min_s": min(traffic_ttc, default=None),
    "collision_labeled_sample_count": sum(bool(sample["labels"].get("collision")) for sample in samples),
  }
