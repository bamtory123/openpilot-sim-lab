"""Reference-bound image-domain diagnostics for simulator camera frames."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image


def _rgb(path: Path) -> np.ndarray:
  return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def _luma(rgb: np.ndarray) -> np.ndarray:
  return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _region_structure(rgb: np.ndarray) -> dict:
  luma = _luma(rgb)
  gradient_y = np.abs(np.diff(luma, axis=0))
  gradient_x = np.abs(np.diff(luma, axis=1))
  histogram = np.histogram(luma, bins=32, range=(0.0, 256.0))[0].astype(np.float64)
  probabilities = histogram[histogram > 0] / histogram.sum()
  saturation = rgb.max(axis=2) - rgb.min(axis=2)
  return {
    "luma_mean": float(luma.mean()),
    "luma_std": float(luma.std()),
    "luma_entropy_bits": float(-(probabilities * np.log2(probabilities)).sum()),
    "gradient_rms": float(np.sqrt(0.5 * (np.mean(gradient_x ** 2) + np.mean(gradient_y ** 2)))),
    "vertical_edge_density": float((gradient_x > 24.0).mean()),
    "horizontal_edge_density": float((gradient_y > 24.0).mean()),
    "bright_neutral_fraction": float(((luma > 160.0) & (saturation < 40.0)).mean()),
  }


def scene_structure_statistics(path: Path) -> dict:
  """Measure fixed image bands without claiming semantic segmentation or matched-scene accuracy."""
  rgb = _rgb(path)
  height = rgb.shape[0]
  bands = {
    "upper": rgb[:round(height * 0.4)],
    "horizon": rgb[round(height * 0.35):round(height * 0.65)],
    "lower": rgb[round(height * 0.5):],
  }
  return {
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "width_px": int(rgb.shape[1]),
    "height_px": int(height),
    "bands": {name: _region_structure(region) for name, region in bands.items()},
  }


def aggregate_scene_structure(paths: list[Path]) -> dict:
  if not paths:
    raise ValueError("at least one image is required")
  frames = [scene_structure_statistics(path) for path in paths]
  metrics = tuple(frames[0]["bands"]["upper"])
  bands = {
    band: {metric: float(np.mean([frame["bands"][band][metric] for frame in frames])) for metric in metrics}
    for band in ("upper", "horizon", "lower")
  }
  return {"frame_count": len(frames), "frames": frames, "bands": bands}


def image_statistics(path: Path) -> dict:
  """Return repeatable full-frame and lower-road-region appearance statistics."""
  rgb = _rgb(path)
  lower = rgb[rgb.shape[0] // 2:]
  luma = _luma(lower)
  saturation = lower.max(axis=2) - lower.min(axis=2)
  edge_density = 0.5 * ((np.abs(np.diff(luma, axis=0)) > 24.0).mean() +
                        (np.abs(np.diff(luma, axis=1)) > 24.0).mean())
  return {
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "width_px": int(rgb.shape[1]), "height_px": int(rgb.shape[0]),
    "lower_rgb_mean": [float(value) for value in lower.mean(axis=(0, 1))],
    "lower_rgb_std": [float(value) for value in lower.std(axis=(0, 1))],
    "lower_luma_mean": float(luma.mean()), "lower_luma_std": float(luma.std()),
    "lower_luma_quantiles": [float(value) for value in np.quantile(luma, (0.05, 0.5, 0.95))],
    "lower_saturation_mean": float(saturation.mean()), "lower_edge_density": float(edge_density),
  }


def aggregate_statistics(paths: list[Path]) -> dict:
  if not paths:
    raise ValueError("at least one image is required")
  frames = [image_statistics(path) for path in paths]
  numeric = ("lower_rgb_mean", "lower_rgb_std", "lower_luma_mean", "lower_luma_std", "lower_luma_quantiles",
             "lower_saturation_mean", "lower_edge_density")
  result = {"frame_count": len(frames), "frames": frames}
  for key in numeric:
    values = np.asarray([frame[key] for frame in frames], dtype=np.float64)
    result[key] = np.mean(values, axis=0).tolist() if values.ndim > 1 else float(values.mean())
  return result


def color_affine(simulator: dict, reference: dict) -> dict:
  """Moment-match lower-region RGB statistics; this is a diagnostic proposal, not a perception metric."""
  source_mean = np.asarray(simulator["lower_rgb_mean"], dtype=np.float64)
  source_std = np.asarray(simulator["lower_rgb_std"], dtype=np.float64)
  target_mean = np.asarray(reference["lower_rgb_mean"], dtype=np.float64)
  target_std = np.asarray(reference["lower_rgb_std"], dtype=np.float64)
  gain = np.clip(target_std / np.maximum(source_std, 1.0), 0.5, 2.0)
  bias = np.clip(target_mean - gain * source_mean, -64.0, 64.0)
  return {"gain_rgb": [float(value) for value in gain], "bias_rgb": [float(value) for value in bias]}
