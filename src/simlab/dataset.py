from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def audit_dataset(root: Path) -> dict:
  samples = []
  for path in sorted(root.glob("*/dataset_manifest.jsonl")):
    samples.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
  curvature = [float(sample["labels"].get("reference_curvature_1pm") or 0.0) for sample in samples]
  return {
    "sample_count": len(samples),
    "split_counts": dict(sorted(Counter(sample["split"] for sample in samples).items())),
    "curved_sample_count": sum(abs(value) > 0.005 for value in curvature),
    "reference_curvature_min_1pm": min(curvature, default=None),
    "reference_curvature_max_1pm": max(curvature, default=None),
  }
