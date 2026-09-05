#!/usr/bin/env python3
"""Select and build a trust-region blend of two temporal specialist artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from simlab.specialist import _temporal_matrix, load_specialist_samples


ALPHAS = tuple(index / 10 for index in range(11))


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_linear(artifact: dict) -> tuple[np.ndarray, float]:
  weights = artifact["weights"]
  coefficient = weights[:-1] / artifact["scale"]
  intercept = float(weights[-1] - (artifact["mean"] / artifact["scale"]) @ weights[:-1])
  return coefficient, intercept


def blend_artifacts(base: dict, update: dict, alpha: float) -> dict:
  if not 0.0 <= alpha <= 1.0:
    raise ValueError("alpha must be in [0, 1]")
  base_coefficient, base_intercept = raw_linear(base)
  update_coefficient, update_intercept = raw_linear(update)
  coefficient = (1.0 - alpha) * base_coefficient + alpha * update_coefficient
  intercept = (1.0 - alpha) * base_intercept + alpha * update_intercept
  mean, scale = base["mean"], base["scale"]
  weights = np.append(coefficient * scale, intercept + mean @ coefficient)
  return {"version": base["version"], "mean": mean, "scale": scale, "weights": weights,
          "frame_gap": base["frame_gap"]}


def predict(artifact: dict, features: np.ndarray) -> np.ndarray:
  normalized = (features - artifact["mean"]) / artifact["scale"]
  return np.column_stack((normalized, np.ones(len(normalized)))) @ artifact["weights"]


def rmse(prediction: np.ndarray, target: np.ndarray) -> float:
  return float(np.sqrt(np.mean((prediction - target) ** 2)))


def validation_matrix(root: Path, frame_gap: int) -> tuple[np.ndarray, np.ndarray, list[Path]]:
  samples = [sample for sample in load_specialist_samples(root) if sample.split == "validation"]
  features, targets = _temporal_matrix(samples, frame_gap=frame_gap)
  if not len(targets):
    raise ValueError(f"no temporal validation pairs: {root}")
  manifests = sorted(root.rglob("specialist_manifest.jsonl"))
  return features, targets, manifests


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--base-artifact", type=Path, required=True)
  parser.add_argument("--update-artifact", type=Path, required=True)
  parser.add_argument("--original-validation-root", type=Path, required=True)
  parser.add_argument("--targeted-validation-root", type=Path, required=True)
  parser.add_argument("--output-artifact", type=Path, required=True)
  parser.add_argument("--max-original-rmse-increase", type=float, default=0.02)
  parser.add_argument("--min-targeted-rmse-improvement", type=float, default=0.40)
  args = parser.parse_args()

  with np.load(args.base_artifact, allow_pickle=False) as loaded:
    base = {key: loaded[key].copy() for key in loaded.files}
  with np.load(args.update_artifact, allow_pickle=False) as loaded:
    update = {key: loaded[key].copy() for key in loaded.files}
  if int(base["version"]) != 2 or int(update["version"]) != 2 or int(base["frame_gap"]) != int(update["frame_gap"]):
    raise ValueError("artifacts must use the same temporal-specialist contract")

  frame_gap = int(base["frame_gap"])
  original_x, original_y, original_manifests = validation_matrix(args.original_validation_root, frame_gap)
  targeted_x, targeted_y, targeted_manifests = validation_matrix(args.targeted_validation_root, frame_gap)
  original_base = rmse(predict(base, original_x), original_y)
  targeted_base = rmse(predict(base, targeted_x), targeted_y)
  sweep = []
  for alpha in ALPHAS:
    candidate = blend_artifacts(base, update, alpha)
    original = rmse(predict(candidate, original_x), original_y)
    targeted = rmse(predict(candidate, targeted_x), targeted_y)
    sweep.append({"alpha": alpha, "original_validation_rmse": original, "targeted_validation_rmse": targeted,
                  "original_relative_change": (original - original_base) / original_base,
                  "targeted_relative_improvement": (targeted_base - targeted) / targeted_base})
  eligible = [row for row in sweep if row["original_relative_change"] <= args.max_original_rmse_increase and
              row["targeted_relative_improvement"] >= args.min_targeted_rmse_improvement]
  if not eligible:
    raise SystemExit("no blend satisfies the offline trust-region gate")
  selected = min(eligible, key=lambda row: row["alpha"])
  artifact = blend_artifacts(base, update, selected["alpha"])
  args.output_artifact.parent.mkdir(parents=True, exist_ok=True)
  np.savez_compressed(args.output_artifact, **artifact)
  result = {
    "schema_version": 1, "scope": "offline_specialist_blend_selection_not_driving_performance",
    "selection_rule": "minimum_alpha_meeting_both_thresholds", "selected": selected,
    "thresholds": {"max_original_rmse_increase": args.max_original_rmse_increase,
                   "min_targeted_rmse_improvement": args.min_targeted_rmse_improvement},
    "base_artifact_sha256": digest(args.base_artifact), "update_artifact_sha256": digest(args.update_artifact),
    "output_artifact_sha256": digest(args.output_artifact),
    "original_manifest_sha256": [digest(path) for path in original_manifests],
    "targeted_manifest_sha256": [digest(path) for path in targeted_manifests], "sweep": sweep,
  }
  output_json = args.output_artifact.with_suffix(".json")
  output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
