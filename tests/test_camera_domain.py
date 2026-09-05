from pathlib import Path

import numpy as np
from PIL import Image

from simlab.camera_domain import (aggregate_scene_structure, aggregate_statistics, color_affine, image_statistics,
                                  scene_structure_statistics)
from simlab.config import load_scenario, scenario_with_camera_color_affine


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


def test_scene_structure_uses_fixed_bands_and_hashes_source(tmp_path):
  rgb = np.zeros((20, 20, 3), dtype=np.uint8)
  rgb[10:, ::2] = 255
  path = tmp_path / "structure.png"
  Image.fromarray(rgb).save(path)

  result = scene_structure_statistics(path)

  assert len(result["sha256"]) == 64
  assert result["bands"]["upper"]["gradient_rms"] == 0.0
  assert result["bands"]["lower"]["vertical_edge_density"] == 1.0
  assert result["bands"]["lower"]["luma_entropy_bits"] == 1.0


def test_scene_structure_aggregate_preserves_frames(tmp_path):
  first = _image(tmp_path / "first.png", (10, 20, 30))
  second = _image(tmp_path / "second.png", (30, 40, 50))

  result = aggregate_scene_structure([first, second])

  assert result["frame_count"] == 2 and len(result["frames"]) == 2
  assert abs(result["bands"]["lower"]["luma_mean"] - result["bands"]["upper"]["luma_mean"]) < 1e-4


def test_camera_color_affine_scenario_remains_openpilot_only():
  root = Path(__file__).resolve().parents[1]
  scenario = load_scenario(root / "configs/scenarios/md_default_loop_lane0_color_match_diagnostic_v2.yaml")
  candidate = scenario_with_camera_color_affine(scenario, {"gain_rgb": [1.1, 1.0, 0.9], "bias_rgb": [5.0, 0.0, -5.0]})

  assert candidate.data.get("simulator_control") is None and candidate.data.get("specialist_replay") is None
  assert candidate.data["environment"]["camera_color_affine"]["bias_rgb"] == [5.0, 0.0, -5.0]
