from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


CARLA_LABEL_FIELDS = ("route_lateral_error_m", "route_heading_error_deg", "route_reference_curvature_1pm")


def build_carla_dataset_manifest(run_dir: Path) -> dict:
  """Build an analysis-only CARLA RGB/route-label manifest from one pilot run.

  Ground truth is joined after collection and is never returned to the bridge;
  ``analysis_only`` samples cannot be mistaken for a control-training corpus.
  """
  capture_dir = run_dir / "captures"
  telemetry_path = run_dir / "telemetry.csv"
  if not telemetry_path.is_file():
    raise ValueError("telemetry.csv is required before building a CARLA dataset manifest")
  import csv
  with telemetry_path.open(encoding="utf-8", newline="") as handle:
    telemetry = {row.get("simulation_frame"): row for row in csv.DictReader(handle) if row.get("simulation_frame")}
  status_path = capture_dir / "capture_status.json"
  status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {"dropped": 0}
  samples = []
  for metadata_path in sorted(capture_dir.glob("road-frame-*.json")):
    capture = json.loads(metadata_path.read_text(encoding="utf-8"))
    image = run_dir / capture["image"]
    row = telemetry.get(str(capture["source_frame_id"]))
    if not image.is_file() or not row or row.get("measurement") != "True":
      continue
    labels = {field: row.get(field) for field in CARLA_LABEL_FIELDS}
    if any(value in (None, "") for value in labels.values()):
      continue
    samples.append({"schema_version": 1, "split": "analysis_only", "image": capture["image"],
                    "labels": {key: float(value) for key, value in labels.items()},
                    "metadata": {"source_frame_id": capture["source_frame_id"],
                                 "capture_mono_ns": capture["capture_mono_ns"],
                                 "simulator": "carla", "control_authority": "openpilot_only"}})
  manifest_path = run_dir / "dataset_manifest.jsonl"
  manifest_path.write_text("".join(json.dumps(sample, sort_keys=True) + "\n" for sample in samples), encoding="utf-8")
  summary = {"schema_version": 1, "scope": "carla_analysis_only_not_control_training",
             "captured_frames": len(list(capture_dir.glob("road-frame-*.png"))),
             "joined_samples": len(samples), "dropped_frames": int(status.get("dropped", 0)),
             "valid": int(status.get("dropped", 0)) == 0}
  (run_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  return summary


def audit_dataset(root: Path) -> dict:
  samples = []
  for path in sorted(root.glob("*/dataset_manifest.jsonl")):
    samples.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
  curvature = [float(sample["labels"].get("reference_curvature_1pm") or 0.0) for sample in samples]
  traffic_distance = [float(sample["labels"]["traffic_nearest_distance_m"]) for sample in samples
                      if sample["labels"].get("traffic_nearest_distance_m") not in (None, "")]
  traffic_ttc = [float(sample["labels"]["traffic_nearest_ttc_s"]) for sample in samples
                 if sample["labels"].get("traffic_nearest_ttc_s") not in (None, "")]
  bbox = [value for sample in samples if (value := sample.get("metadata", {}).get("static_obstacle_bbox_xyxy_px")) is not None]
  valid_bbox = [value for value in bbox if len(value) == 4 and 0 <= value[0] < value[2] <= 1928 and 0 <= value[1] < value[3] <= 1208]
  bbox_area = [float((value[2] - value[0]) * (value[3] - value[1])) for value in valid_bbox]
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
    "static_obstacle_bbox_labeled_sample_count": len(bbox),
    "static_obstacle_bbox_invalid_sample_count": len(bbox) - len(valid_bbox),
    "static_obstacle_bbox_area_min_px2": min(bbox_area, default=None),
    "static_obstacle_bbox_area_max_px2": max(bbox_area, default=None),
  }
