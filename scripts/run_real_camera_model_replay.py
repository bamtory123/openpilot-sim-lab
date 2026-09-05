#!/usr/bin/env python3
"""Run the pinned OpenPilot 60-frame real-camera model replay and retain aggregate evidence."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

import numpy as np
from PIL import Image

from simlab.model_overlay import nv12_to_rgb, render_overlay, save_contact_sheet
from simlab.model_replay import summarize_replay


def _git(path: Path) -> dict:
  commit = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
  dirty = bool(subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip())
  return {"commit": commit, "dirty": dirty}


def _program_version(name: str) -> dict:
  path = subprocess.check_output(["sh", "-c", f"command -v {name}"], text=True).strip()
  first_line = subprocess.check_output([path, "-version"], text=True, stderr=subprocess.STDOUT).splitlines()[0]
  match = re.search(r"version\s+(?:n)?(\d+)", first_line)
  return {"path": path, "version": first_line, "major": int(match.group(1)) if match else None}


def _remote_metadata(url: str) -> dict:
  request = urllib.request.Request(url, method="HEAD")
  with urllib.request.urlopen(request, timeout=30) as response:
    return {
      "url": url,
      "content_length": int(response.headers["Content-Length"]),
      "content_md5": response.headers.get("Content-MD5"),
      "etag": response.headers.get("ETag"),
      "last_modified": response.headers.get("Last-Modified"),
    }


def _model_record(message) -> dict:
  model = message.modelV2
  path_x = list(model.position.x)
  lane_probs = list(model.laneLineProbs)
  return {
    "frame_id": int(model.frameId),
    "frame_age": int(model.frameAge),
    "frame_drop_pct": float(model.frameDropPerc),
    "model_execution_time_s": float(model.modelExecutionTime),
    "path_horizon_m": float(path_x[-1]) if path_x else 0.0,
    "left_lane_probability": float(lane_probs[1]) if len(lane_probs) > 1 else 0.0,
    "right_lane_probability": float(lane_probs[2]) if len(lane_probs) > 2 else 0.0,
    "desired_curvature_1pm": float(model.action.desiredCurvature),
  }


def _driver_record(message) -> dict:
  return {"model_execution_time_s": float(message.driverStateV2.modelExecutionTime)}


def _model_snapshot(message, projection: dict, source_frame_index: int) -> dict:
  model = message.modelV2

  def points(value) -> list[list[float]]:
    return [[float(x), float(y), float(z)] for x, y, z in zip(value.x, value.y, value.z, strict=True)]

  return {
    "schema_version": 1,
    "scope": "analysis_only_model_projection_not_control_or_accuracy",
    "source_frame_index": source_frame_index,
    "model_frame_id": int(model.frameId),
    "projection": projection,
    "path": points(model.position),
    "lane_lines": [points(lane) for lane in model.laneLines],
    "lane_line_probabilities": [float(value) for value in model.laneLineProbs],
  }


def _write_json(path: Path, value: dict) -> None:
  path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--openpilot-root", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  parser.add_argument("--allow-dirty", action="store_true")
  args = parser.parse_args()

  openpilot_root = args.openpilot_root.resolve()
  simlab_root = Path(__file__).resolve().parents[1]
  source = {"openpilot": _git(openpilot_root), "sim_lab": _git(simlab_root)}
  if not args.allow_dirty and any(repository["dirty"] for repository in source.values()):
    raise SystemExit("dirty source tree rejected; commit changes or pass --allow-dirty for a diagnostic run")

  ffmpeg, ffprobe = _program_version("ffmpeg"), _program_version("ffprobe")
  if ffmpeg["major"] is None or ffmpeg["major"] > 7:
    raise SystemExit("OpenPilot's pinned FrameReader requires FFmpeg <= 7 because it passes the removed -vsync option")

  sys.path.insert(0, str(openpilot_root))
  from openpilot.selfdrive.test.process_replay.model_replay import END_FRAME, SEGMENT, START_FRAME, TEST_ROUTE, get_frames, model_replay
  from openpilot.common.transformations.camera import DEVICE_CAMERAS, get_view_frame_from_calib_frame
  from openpilot.tools.lib.logreader import LogReader
  from openpilot.tools.lib.openpilotci import get_url

  names = ("fcamera.hevc", "ecamera.hevc", "dcamera.hevc", "rlog.zst")
  remote_inputs = [_remote_metadata(get_url(TEST_ROUTE, SEGMENT, name)) for name in names]
  manifest = {
    "schema_version": 1,
    "scope": "pretrained_real_camera_model_replay_reference_not_closed_loop_or_road_performance",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "source": source,
    "route": {"route_id": TEST_ROUTE, "segment": SEGMENT, "start_frame": START_FRAME,
              "end_frame_exclusive": END_FRAME, "remote_inputs": remote_inputs},
    "runtime": {"python": sys.version.split()[0], "ffmpeg": ffmpeg, "ffprobe": ffprobe},
  }
  args.output.mkdir(parents=True, exist_ok=False)
  _write_json(args.output / "manifest.json", manifest)

  try:
    log_messages = list(LogReader(get_url(TEST_ROUTE, SEGMENT, "rlog.zst")))
    frames = get_frames()
    messages = model_replay(log_messages, frames)
    model_messages = [message for message in messages if message.which() == "modelV2"]
    model_records = [_model_record(message) for message in model_messages]
    driver_records = [_driver_record(message) for message in messages if message.which() == "driverStateV2"]
    summary = summarize_replay(model_records, driver_records, END_FRAME - START_FRAME)
    summary["source"] = source
    summary["route"] = manifest["route"] | {"remote_inputs": [
      {key: value for key, value in item.items() if key != "url"} for item in remote_inputs
    ]}
    with (args.output / "model_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
      writer = csv.DictWriter(stream, fieldnames=list(model_records[0]))
      writer.writeheader()
      writer.writerows(model_records)

    calibration = next(message.extrinsicsCalibration for message in log_messages if message.which() == "extrinsicsCalibration")
    rpy = list(calibration.rpyCalib)
    camera = DEVICE_CAMERAS[("tici", "unknown")].narrow_road
    projection = {"intrinsic": camera.intrinsics.tolist(),
                  "view_from_calib": get_view_frame_from_calib_frame(*rpy, 0.0)[:, :3].tolist(),
                  "camera_height_m": float(calibration.height[0]), "calibration_rpy_rad": [float(value) for value in rpy]}
    diagnostic_dir = args.output / "diagnostics"
    diagnostic_dir.mkdir()
    overlay_paths = []
    for index in (0, 20, 40, 59):
      snapshot = _model_snapshot(model_messages[index], projection, index)
      snapshot_path = diagnostic_dir / f"model-frame-{index:03d}.json"
      overlay_path = diagnostic_dir / f"overlay-frame-{index:03d}.png"
      _write_json(snapshot_path, snapshot)
      rgb = nv12_to_rgb(np.asarray(frames["narrowRoadCameraState"].get(index)), camera.width, camera.height)
      render_overlay(Image.fromarray(rgb), snapshot).save(overlay_path)
      overlay_paths.append(overlay_path)
    save_contact_sheet(overlay_paths, diagnostic_dir / "contact-sheet.png")
    summary["diagnostic_overlays"] = {"scope": "local_analysis_only_not_public_evidence",
                                      "frames": [path.name for path in overlay_paths], "contact_sheet": "contact-sheet.png"}
    _write_json(args.output / "summary.json", summary)
  except Exception as error:
    _write_json(args.output / "summary.json", {
      "schema_version": 1,
      "scope": manifest["scope"],
      "classification": "replay_failed",
      "functional_status": "fail",
      "timing_status": "not_evaluated",
      "error": {"type": type(error).__name__, "message": str(error)},
    })
    raise

  print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
