import json
import csv

from simlab.dataset import audit_dataset, build_carla_dataset_manifest


def test_audit_dataset_counts_splits_and_curves(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  samples = [{"split": "train", "labels": {"reference_curvature_1pm": 0.0}},
             {"split": "validation", "labels": {"reference_curvature_1pm": 0.01}}]
  (run / "dataset_manifest.jsonl").write_text("\n".join(json.dumps(sample) for sample in samples))

  result = audit_dataset(tmp_path)

  assert result["sample_count"] == 2 and result["split_counts"] == {"train": 1, "validation": 1}
  assert result["curved_sample_count"] == 1 and result["reference_curvature_max_1pm"] == 0.01


def test_audit_dataset_reports_traffic_label_coverage(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  samples = [{"split": "train", "labels": {"traffic_nearest_distance_m": 12.0, "traffic_nearest_ttc_s": 6.0, "collision": False}},
             {"split": "train", "labels": {"traffic_nearest_distance_m": 4.5, "collision": True}}]
  (run / "dataset_manifest.jsonl").write_text("\n".join(json.dumps(sample) for sample in samples))

  result = audit_dataset(tmp_path)

  assert result["traffic_labeled_sample_count"] == 2
  assert result["traffic_nearest_distance_min_m"] == 4.5 and result["traffic_nearest_ttc_min_s"] == 6.0
  assert result["collision_labeled_sample_count"] == 1


def test_audit_dataset_reports_static_obstacle_bbox_coverage(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  sample = {"split": "train", "metadata": {"static_obstacle_bbox_xyxy_px": [1, 2, 4, 6]}, "labels": {}}
  (run / "dataset_manifest.jsonl").write_text(json.dumps(sample))

  result = audit_dataset(tmp_path)

  assert result["static_obstacle_bbox_labeled_sample_count"] == 1
  assert result["static_obstacle_bbox_area_min_px2"] == 12.0


def test_audit_dataset_counts_invalid_static_obstacle_bboxes(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  sample = {"split": "train", "metadata": {"static_obstacle_bbox_xyxy_px": [4, 2, 1, 6]}, "labels": {}}
  (run / "dataset_manifest.jsonl").write_text(json.dumps(sample))

  result = audit_dataset(tmp_path)

  assert result["static_obstacle_bbox_labeled_sample_count"] == 1
  assert result["static_obstacle_bbox_invalid_sample_count"] == 1


def test_build_carla_dataset_manifest_joins_measurement_only(tmp_path):
  captures = tmp_path / "captures"; captures.mkdir()
  (captures / "road-frame-000042.png").write_bytes(b"png")
  (captures / "road-frame-000042.json").write_text(json.dumps({"source_frame_id": 42, "capture_mono_ns": 7,
                                                                  "image": "captures/road-frame-000042.png"}))
  (captures / "capture_status.json").write_text(json.dumps({"dropped": 0}))
  with (tmp_path / "telemetry.csv").open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["simulation_frame", "measurement", "route_lateral_error_m",
                                                 "route_heading_error_deg", "route_reference_curvature_1pm"])
    writer.writeheader(); writer.writerow({"simulation_frame": 42, "measurement": True, "route_lateral_error_m": 0.2,
                                             "route_heading_error_deg": -1.0, "route_reference_curvature_1pm": 0.01})

  summary = build_carla_dataset_manifest(tmp_path)

  sample = json.loads((tmp_path / "dataset_manifest.jsonl").read_text())
  assert summary == {"schema_version": 1, "scope": "carla_analysis_only_not_control_training", "captured_frames": 1,
                     "joined_samples": 1, "dropped_frames": 0, "valid": True}
  assert sample["split"] == "analysis_only" and sample["labels"]["route_lateral_error_m"] == 0.2


def test_build_carla_dataset_manifest_marks_overflow_invalid(tmp_path):
  (tmp_path / "captures").mkdir()
  (tmp_path / "captures/capture_status.json").write_text(json.dumps({"dropped": 1}))
  (tmp_path / "telemetry.csv").write_text("simulation_frame\n")

  assert build_carla_dataset_manifest(tmp_path)["valid"] is False


def test_audit_dataset_reads_carla_route_curvature_label(tmp_path):
  run = tmp_path / "run"; run.mkdir()
  sample = {"split": "analysis_only", "labels": {"route_reference_curvature_1pm": -0.02}}
  (run / "dataset_manifest.jsonl").write_text(json.dumps(sample))

  result = audit_dataset(tmp_path)

  assert result["curved_sample_count"] == 1 and result["reference_curvature_min_1pm"] == -0.02
