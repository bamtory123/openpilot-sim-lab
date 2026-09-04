from pathlib import Path

import numpy as np
from PIL import Image

from simlab.camera_domain import aggregate_statistics, color_affine, image_statistics


def _image(path: Path, values: tuple[int, int, int]) -> Path:
  Image.fromarray(np.full((8, 10, 3), values, dtype=np.uint8)).save(path)
  return path


def test_camera_domain_statistics_are_hash_bound_and_lower_region_based(tmp_path):
  stats = image_statistics(_image(tmp_path / "frame.png", (40, 80, 120)))

  assert len(stats["sha256"]) == 64
  assert stats["width_px"] == 10 and stats["height_px"] == 8
  assert stats["lower_rgb_mean"] == [40.0, 80.0, 120.0]
  assert stats["lower_edge_density"] == 0.0


def test_camera_domain_color_affine_is_bounded_moment_match(tmp_path):
  simulator = aggregate_statistics([_image(tmp_path / "sim.png", (40, 50, 60))])
  reference = aggregate_statistics([_image(tmp_path / "ref.png", (80, 90, 100))])
  affine = color_affine(simulator, reference)

  assert affine["gain_rgb"] == [0.5, 0.5, 0.5]
  assert affine["bias_rgb"] == [60.0, 64.0, 64.0]
