from __future__ import annotations

import argparse
import json
from pathlib import Path


VALID_STATUSES = {"invalid", "integrated-but-not-stable", "bounded-pass"}
CARLA_LABEL_FIELDS = ("route_lateral_error_m", "route_heading_error_deg", "route_reference_curvature_1pm")


def verify_dataset(run_dir: Path, summary: dict, manifest: dict) -> dict | None:
  capture = manifest.get("capture", {})
  if not capture.get("enabled"):
    return None
  dataset = summary.get("dataset_summary")
  manifest_path, dataset_summary_path = run_dir / "dataset_manifest.jsonl", run_dir / "dataset_summary.json"
  if not isinstance(dataset, dict) or not manifest_path.is_file() or not dataset_summary_path.is_file():
    raise SystemExit("capture-enabled pilot requires dataset manifest and summary")
  persisted = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
  if persisted != dataset or dataset.get("scope") != "carla_analysis_only_not_control_training":
    raise SystemExit("CARLA dataset summary is inconsistent")
  captured = len(list((run_dir / "captures").glob("road-frame-*.png")))
  if captured != dataset.get("captured_frames"):
    raise SystemExit("CARLA dataset capture count is inconsistent")
  samples = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line]
  if len(samples) != dataset.get("joined_samples"):
    raise SystemExit("CARLA dataset sample count is inconsistent")
  for sample in samples:
    if sample.get("split") != "analysis_only" or not (run_dir / sample.get("image", "")).is_file():
      raise SystemExit("CARLA dataset sample is not analysis-only or image is missing")
    if any(label not in sample.get("labels", {}) for label in CARLA_LABEL_FIELDS):
      raise SystemExit("CARLA dataset sample is missing a route label")
  return {"valid": bool(dataset.get("valid")), "joined_samples": len(samples), "dropped_frames": dataset.get("dropped_frames")}


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify one CARLA adapter pilot artifact")
  parser.add_argument("run_dir", type=Path)
  args = parser.parse_args()
  summary_path = args.run_dir / "summary.json"
  manifest_path = args.run_dir / "manifest.json"
  if not summary_path.is_file() or not manifest_path.is_file():
    raise SystemExit("pilot artifact requires manifest.json and summary.json")
  summary = json.loads(summary_path.read_text(encoding="utf-8"))
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  if summary.get("schema_version") != 1 or summary.get("pilot_status") not in VALID_STATUSES:
    raise SystemExit("invalid CARLA adapter pilot summary")
  if manifest.get("scope") != "carla_v02_adapter_pilot_not_road_qualification":
    raise SystemExit("pilot manifest has an invalid scope")
  required = ("events.jsonl", "telemetry.csv", "camera.csv", "run.log")
  missing = [name for name in required if not (args.run_dir / name).is_file()]
  if missing:
    raise SystemExit(f"pilot artifact is missing: {', '.join(missing)}")
  dataset = verify_dataset(args.run_dir, summary, manifest)
  print(json.dumps({"status": "pass", "pilot_status": summary["pilot_status"], "run_dir": str(args.run_dir),
                    "dataset": dataset}, sort_keys=True))


if __name__ == "__main__":
  main()
