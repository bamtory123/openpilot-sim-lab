"""Analysis-only projection of OpenPilot model geometry onto road-camera images."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def nv12_to_rgb(frame: np.ndarray, width: int, height: int) -> np.ndarray:
  data = np.asarray(frame, dtype=np.uint8).reshape(-1)
  expected = width * height * 3 // 2
  if data.size != expected:
    raise ValueError(f"expected {expected} NV12 bytes, got {data.size}")
  y = data[:width * height].reshape(height, width).astype(np.int32)
  uv = data[width * height:].reshape(height // 2, width)
  u = np.repeat(np.repeat(uv[:, 0::2], 2, axis=0), 2, axis=1).astype(np.int32)
  v = np.repeat(np.repeat(uv[:, 1::2], 2, axis=0), 2, axis=1).astype(np.int32)
  c, d, e = y - 16, u - 128, v - 128
  rgb = np.stack(((298 * c + 409 * e + 128) >> 8,
                  (298 * c - 100 * d - 208 * e + 128) >> 8,
                  (298 * c + 516 * d + 128) >> 8), axis=2)
  return np.clip(rgb, 0, 255).astype(np.uint8)


def project_points(points: list[list[float]], intrinsic: list[list[float]], view_from_calib: list[list[float]],
                   z_offset_m: float = 0.0) -> list[tuple[float, float]]:
  xyz = np.asarray(points, dtype=np.float64)
  if xyz.ndim != 2 or xyz.shape[1] != 3:
    raise ValueError("points must be an N x 3 array")
  xyz = xyz.copy()
  xyz[:, 2] += z_offset_m
  view = np.asarray(view_from_calib, dtype=np.float64) @ xyz.T
  projected = np.asarray(intrinsic, dtype=np.float64) @ view
  depth = projected[2]
  valid = depth > 0.1
  pixels = (projected[:2, valid] / depth[valid]).T
  return [(float(x), float(y)) for x, y in pixels if np.isfinite(x) and np.isfinite(y)]


def render_overlay(image: Image.Image, snapshot: dict) -> Image.Image:
  base = image.convert("RGBA")
  overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
  draw = ImageDraw.Draw(overlay)
  projection = snapshot["projection"]
  intrinsic, view = projection["intrinsic"], projection["view_from_calib"]

  for lane, probability in zip(snapshot["lane_lines"], snapshot["lane_line_probabilities"], strict=True):
    points = project_points(lane, intrinsic, view)
    if len(points) > 1:
      draw.line(points, fill=(0, 255, 80, max(48, int(255 * probability))), width=max(2, int(7 * probability)))
  path = project_points(snapshot["path"], intrinsic, view, float(projection["camera_height_m"]))
  if len(path) > 1:
    draw.line(path, fill=(255, 60, 40, 230), width=6)

  left, right = snapshot["lane_line_probabilities"][1:3]
  horizon = snapshot["path"][-1][0] if snapshot["path"] else 0.0
  draw.rectangle((12, 12, 560, 54), fill=(0, 0, 0, 170))
  draw.text((22, 23), f"path red | lanes green | L/R confidence {left:.3f}/{right:.3f} | horizon {horizon:.1f} m",
            fill=(255, 255, 255, 255))
  return Image.alpha_composite(base, overlay).convert("RGB")


def save_overlay(image_path: Path, snapshot: dict, output_path: Path) -> dict:
  rendered = render_overlay(Image.open(image_path), snapshot)
  output_path.parent.mkdir(parents=True, exist_ok=True)
  rendered.save(output_path)
  return {"width_px": rendered.width, "height_px": rendered.height, "output": output_path.name}


def save_contact_sheet(images: list[Path], output_path: Path, columns: int = 2) -> None:
  if not images:
    raise ValueError("at least one overlay is required")
  opened = [Image.open(path).convert("RGB") for path in images]
  thumb_width = 960
  thumbs = [image.resize((thumb_width, round(image.height * thumb_width / image.width))) for image in opened]
  thumb_height = max(image.height for image in thumbs)
  rows = (len(thumbs) + columns - 1) // columns
  sheet = Image.new("RGB", (thumb_width * columns, thumb_height * rows), "black")
  for index, image in enumerate(thumbs):
    sheet.paste(image, ((index % columns) * thumb_width, (index // columns) * thumb_height))
  output_path.parent.mkdir(parents=True, exist_ok=True)
  sheet.save(output_path)
