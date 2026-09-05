import numpy as np
from PIL import Image

from simlab.model_overlay import nv12_to_rgb, project_points, render_overlay


def test_nv12_limited_range_black_converts_to_rgb_black():
  frame = np.concatenate((np.full(8, 16, dtype=np.uint8), np.full(4, 128, dtype=np.uint8)))
  assert np.array_equal(nv12_to_rgb(frame, 4, 2), np.zeros((2, 4, 3), dtype=np.uint8))


def test_projection_places_forward_point_at_optical_center():
  intrinsic = [[100.0, 0.0, 50.0], [0.0, 100.0, 30.0], [0.0, 0.0, 1.0]]
  view_from_calib = [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]
  assert project_points([[10.0, 0.0, 0.0]], intrinsic, view_from_calib) == [(50.0, 30.0)]


def test_overlay_is_analysis_only_image_operation():
  snapshot = {
    "projection": {"intrinsic": [[100.0, 0.0, 50.0], [0.0, 100.0, 30.0], [0.0, 0.0, 1.0]],
                   "view_from_calib": [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]],
                   "camera_height_m": 1.2},
    "path": [[5.0, 0.0, -1.2], [20.0, 0.0, -1.2]],
    "lane_lines": [[[5.0, -1.0, 0.0], [20.0, -1.0, 0.0]]] * 4,
    "lane_line_probabilities": [0.1, 0.8, 0.7, 0.1],
  }
  original = Image.new("RGB", (100, 60), "black")
  rendered = render_overlay(original, snapshot)

  assert rendered.size == original.size
  assert np.asarray(rendered).sum() > 0
  assert np.asarray(original).sum() == 0
