#!/usr/bin/env python3
"""Compare temporal-specialist output sensitivity to bounded pixel perturbations."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from simlab.specialist import image_features, load_specialist_samples


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def shift(image: np.ndarray, *, dx: int = 0, dy: int = 0) -> np.ndarray:
  result = np.roll(image, (dy, dx), axis=(0, 1))
  if dx > 0:
    result[:, :dx] = result[:, dx:dx + 1]
  elif dx < 0:
    result[:, dx:] = result[:, dx - 1:dx]
  if dy > 0:
    result[:dy] = result[dy:dy + 1]
  elif dy < 0:
    result[dy:] = result[dy - 1:dy]
  return result


def brighten(image: np.ndarray, delta: int) -> np.ndarray:
  return np.clip(image.astype(np.int16) + delta, 0, 255).astype(np.uint8)


TRANSFORMS = {
  "horizontal_minus_1px": lambda image: shift(image, dx=-1),
  "horizontal_plus_1px": lambda image: shift(image, dx=1),
  "vertical_minus_1px": lambda image: shift(image, dy=-1),
  "vertical_plus_1px": lambda image: shift(image, dy=1),
  "luma_minus_2": lambda image: brighten(image, -2),
  "luma_plus_2": lambda image: brighten(image, 2),
}


def temporal_features(previous: np.ndarray, current: np.ndarray) -> np.ndarray:
  previous_features = image_features(previous)
  current_features = image_features(current)
  return np.concatenate((current_features, current_features - previous_features))


def artifact_dict(path: Path) -> dict:
  with np.load(path, allow_pickle=False) as loaded:
    return {key: loaded[key].copy() for key in loaded.files}


def predict(artifact: dict, features: np.ndarray) -> np.ndarray:
  normalized = (features - artifact["mean"]) / artifact["scale"]
  return np.column_stack((normalized, np.ones(len(normalized)))) @ artifact["weights"]


def quantiles(values: np.ndarray) -> dict:
  return {"median_abs_delta": float(np.median(values)), "p95_abs_delta": float(np.quantile(values, 0.95)),
          "max_abs_delta": float(np.max(values))}


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--dataset-root", type=Path, required=True)
  parser.add_argument("--artifact", action="append", required=True, metavar="LABEL=PATH")
  parser.add_argument("--baseline-label", required=True)
  parser.add_argument("--candidate-label", required=True)
  parser.add_argument("--output", type=Path, required=True)
  args = parser.parse_args()
  artifact_paths = {}
  for item in args.artifact:
    label, separator, path = item.partition("=")
    if not separator or not label or label in artifact_paths:
      raise ValueError("each artifact must be a unique LABEL=PATH")
    artifact_paths[label] = Path(path)
  if args.baseline_label not in artifact_paths or args.candidate_label not in artifact_paths:
    raise ValueError("baseline and candidate labels must name supplied artifacts")

  samples = [sample for sample in load_specialist_samples(args.dataset_root) if sample.split == "validation"]
  pairs = []
  for run in {sample.run for sample in samples}:
    ordered = sorted((sample for sample in samples if sample.run == run), key=lambda sample: sample.simulation_frame)
    pairs.extend((previous, current) for previous, current in zip(ordered, ordered[1:])
                 if current.simulation_frame - previous.simulation_frame == 20)
  if not pairs:
    raise ValueError("no 20-frame temporal validation pairs")
  base_features, perturbed = [], {name: [] for name in TRANSFORMS}
  image_paths = set()
  for previous, current in pairs:
    previous_image = np.asarray(Image.open(previous.image).convert("RGB"))
    current_image = np.asarray(Image.open(current.image).convert("RGB"))
    image_paths.update((previous.image, current.image))
    base_features.append(temporal_features(previous_image, current_image))
    for name, transform in TRANSFORMS.items():
      perturbed[name].append(temporal_features(transform(previous_image), transform(current_image)))
  base_features = np.asarray(base_features)
  perturbed = {name: np.asarray(features) for name, features in perturbed.items()}

  models = {}
  for label, path in artifact_paths.items():
    artifact = artifact_dict(path)
    base_prediction = predict(artifact, base_features)
    transforms, all_deltas = {}, []
    for name, features in perturbed.items():
      delta = np.abs(predict(artifact, features) - base_prediction)
      transforms[name] = quantiles(delta)
      all_deltas.append(delta)
    models[label] = {"artifact_sha256": digest(path), "transforms": transforms,
                     "aggregate": quantiles(np.concatenate(all_deltas))}
  baseline_p95 = models[args.baseline_label]["aggregate"]["p95_abs_delta"]
  candidate_p95 = models[args.candidate_label]["aggregate"]["p95_abs_delta"]
  supported = candidate_p95 > baseline_p95 * 1.1
  result = {
    "schema_version": 1,
    "scope": "bounded_static_pixel_perturbation_diagnostic_not_pose_or_driving_performance_evidence",
    "classification": "candidate_pixel_sensitivity_increase_observed" if supported else
                      "candidate_pixel_sensitivity_increase_not_supported",
    "pair_count": len(pairs), "transform_count": len(TRANSFORMS),
    "baseline_label": args.baseline_label, "candidate_label": args.candidate_label,
    "candidate_to_baseline_p95_ratio": candidate_p95 / baseline_p95,
    "models": models,
    "dataset_manifest_sha256": [digest(path) for path in sorted(args.dataset_root.rglob("specialist_manifest.jsonl"))],
    "dataset_image_set_sha256": hashlib.sha256("".join(digest(path) for path in sorted(image_paths)).encode()).hexdigest(),
    "limitations": ["pixel_shifts_are_not_physical_camera_pose_perturbations",
                    "small_fixed_transform_set_does_not_establish_global_robustness",
                    "static_pair_response_does_not_measure_closed_loop_stability"],
  }
  args.output.parent.mkdir(parents=True, exist_ok=True)
  args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  print(json.dumps(result, indent=2, sort_keys=True))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
