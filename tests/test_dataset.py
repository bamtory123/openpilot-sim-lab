import json

from simlab.dataset import audit_dataset


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
