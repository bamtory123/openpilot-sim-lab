from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
from PIL import Image


FEATURE_HEIGHT = 24
FEATURE_WIDTH = 32
ARTIFACT_VERSION = 1
TEMPORAL_ARTIFACT_VERSION = 2


@dataclass(frozen=True)
class SpecialistSample:
  image: Path
  split: str
  target_steer: float
  simulation_frame: int
  run: Path


def image_features(image: np.ndarray) -> np.ndarray:
  if image.ndim != 3 or image.shape[2] != 3:
    raise ValueError("expected an RGB image")
  y = np.linspace(0, image.shape[0] - 1, FEATURE_HEIGHT, dtype=np.intp)
  x = np.linspace(0, image.shape[1] - 1, FEATURE_WIDTH, dtype=np.intp)
  rgb = image[np.ix_(y, x)].astype(np.float64)
  return (rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114).reshape(-1) / 255.0


def load_specialist_samples(root: Path) -> list[SpecialistSample]:
  samples = []
  for manifest in sorted(root.rglob("specialist_manifest.jsonl")):
    for line in manifest.read_text(encoding="utf-8").splitlines():
      row = json.loads(line)
      target = row.get("target_normalized_steer")
      if row.get("split") in ("train", "validation") and isinstance(target, (int, float)):
        samples.append(SpecialistSample(manifest.parent / row["image"], row["split"], float(target), int(row.get("simulation_frame", -1)), manifest.parent))
  return samples


def _matrix(samples: list[SpecialistSample]) -> tuple[np.ndarray, np.ndarray]:
  if not samples:
    return np.empty((0, FEATURE_HEIGHT * FEATURE_WIDTH)), np.empty((0, ))
  return (np.stack([image_features(np.asarray(Image.open(sample.image).convert("RGB"))) for sample in samples]),
          np.asarray([sample.target_steer for sample in samples], dtype=np.float64))


def _temporal_matrix(samples: list[SpecialistSample], *, frame_gap: int) -> tuple[np.ndarray, np.ndarray]:
  features, targets = [], []
  for run in {sample.run for sample in samples}:
    ordered = sorted((sample for sample in samples if sample.run == run), key=lambda sample: sample.simulation_frame)
    for previous, current in zip(ordered, ordered[1:]):
      if previous.simulation_frame < 0 or current.simulation_frame - previous.simulation_frame != frame_gap:
        continue
      previous_features = image_features(np.asarray(Image.open(previous.image).convert("RGB")))
      current_features = image_features(np.asarray(Image.open(current.image).convert("RGB")))
      features.append(np.concatenate((current_features, current_features - previous_features)))
      targets.append(current.target_steer)
  return np.asarray(features), np.asarray(targets, dtype=np.float64)


def _dual_ridge_weights(features: np.ndarray, targets: np.ndarray, *, l2: float) -> np.ndarray:
  centered_targets = targets - targets.mean()
  coefficients = features.T @ np.linalg.solve(features @ features.T + np.eye(len(features)) * l2, centered_targets)
  return np.append(coefficients, targets.mean())


def train_specialist(dataset_root: Path, artifact_path: Path, *, l2: float = 1e-3) -> dict:
  samples = load_specialist_samples(dataset_root)
  train = [sample for sample in samples if sample.split == "train"]
  validation = [sample for sample in samples if sample.split == "validation"]
  if len(train) < 32 or not validation:
    raise ValueError("specialist training requires at least 32 train and one validation sample")
  x_train, y_train = _matrix(train)
  x_validation, y_validation = _matrix(validation)
  mean = x_train.mean(axis=0)
  scale = x_train.std(axis=0)
  scale[scale < 1e-6] = 1.0
  x_train = (x_train - mean) / scale
  x_validation = (x_validation - mean) / scale
  x_train = np.column_stack((x_train, np.ones(len(x_train))))
  x_validation = np.column_stack((x_validation, np.ones(len(x_validation))))
  regularizer = np.eye(x_train.shape[1]) * l2
  regularizer[-1, -1] = 0.0
  weights = np.linalg.solve(x_train.T @ x_train + regularizer, x_train.T @ y_train)
  prediction = x_validation @ weights
  metrics = {
    "train_samples": len(train), "validation_samples": len(validation),
    "validation_mae_normalized_steer": float(np.mean(np.abs(prediction - y_validation))),
    "validation_rmse_normalized_steer": float(np.sqrt(np.mean((prediction - y_validation) ** 2))),
    "feature_height": FEATURE_HEIGHT, "feature_width": FEATURE_WIDTH, "l2": l2,
  }
  artifact_path.parent.mkdir(parents=True, exist_ok=True)
  np.savez_compressed(artifact_path, version=np.array(ARTIFACT_VERSION), mean=mean, scale=scale, weights=weights)
  artifact_path.with_suffix(".json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  return metrics


def train_temporal_specialist(dataset_root: Path, artifact_path: Path, *, frame_gap: int = 20, l2: float = 1e-3) -> dict:
  samples = load_specialist_samples(dataset_root)
  train = [sample for sample in samples if sample.split == "train"]
  validation = [sample for sample in samples if sample.split == "validation"]
  x_train, y_train = _temporal_matrix(train, frame_gap=frame_gap)
  x_validation, y_validation = _temporal_matrix(validation, frame_gap=frame_gap)
  if len(x_train) < 32 or not len(x_validation):
    raise ValueError("temporal specialist training requires at least 32 train pairs and one validation pair")
  mean = x_train.mean(axis=0)
  scale = x_train.std(axis=0)
  scale[scale < 1e-6] = 1.0
  x_train = (x_train - mean) / scale
  x_validation = (x_validation - mean) / scale
  weights = _dual_ridge_weights(x_train, y_train, l2=l2)
  prediction = np.column_stack((x_validation, np.ones(len(x_validation)))) @ weights
  metrics = {
    "train_pairs": len(x_train), "validation_pairs": len(x_validation), "frame_gap": frame_gap,
    "validation_mae_normalized_steer": float(np.mean(np.abs(prediction - y_validation))),
    "validation_rmse_normalized_steer": float(np.sqrt(np.mean((prediction - y_validation) ** 2))),
    "feature_height": FEATURE_HEIGHT, "feature_width": FEATURE_WIDTH, "l2": l2,
  }
  artifact_path.parent.mkdir(parents=True, exist_ok=True)
  np.savez_compressed(artifact_path, version=np.array(TEMPORAL_ARTIFACT_VERSION), mean=mean, scale=scale, weights=weights, frame_gap=np.array(frame_gap))
  artifact_path.with_suffix(".json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  return metrics


def predict_specialist(artifact_path: Path, image: np.ndarray) -> float:
  with np.load(artifact_path, allow_pickle=False) as artifact:
    if int(artifact["version"]) != ARTIFACT_VERSION:
      raise ValueError("unsupported specialist artifact")
    features = (image_features(image) - artifact["mean"]) / artifact["scale"]
    return float(np.clip(np.append(features, 1.0) @ artifact["weights"], -0.2, 0.2))
