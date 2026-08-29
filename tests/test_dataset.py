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
