#!/usr/bin/env python3
"""Build a public-safe real-camera versus MetaDrive model-output contrast."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import fmean


FORBIDDEN = ("/home/", "/mnt/", "C:\\", "telemetry.csv", "model_metrics.csv", "fcamera.hevc")


def _digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(rows: list[dict], key: str) -> float:
  return fmean(float(row[key]) for row in rows)


def _metadrive(run: Path) -> dict:
  summary_path, telemetry_path = run / "summary.json", run / "telemetry.csv"
  summary = json.loads(summary_path.read_text(encoding="utf-8"))
  with telemetry_path.open(encoding="utf-8") as stream:
    rows = [row for row in csv.DictReader(stream) if row["measurement"].lower() in ("1", "true")]
  if not rows:
    raise ValueError("MetaDrive evidence has no measurement rows")
  straight = [row for row in rows if abs(float(row["reference_curvature_1pm"])) < 0.001]
  curve = [row for row in rows if abs(float(row["reference_curvature_1pm"])) >= 0.001]

  def segment(records: list[dict]) -> dict:
    return {"samples": len(records), "left_lane_probability_mean": _mean(records, "model_left_lane_prob"),
            "right_lane_probability_mean": _mean(records, "model_right_lane_prob"),
            "path_horizon_m_mean": _mean(records, "model_path_end_x_m")}

  return {
    "summary_sha256": _digest(summary_path), "telemetry_sha256": _digest(telemetry_path),
    "scenario_id": summary["scenario_id"], "validity": summary["validity"], "outcome": summary["outcome"],
    "all": segment(rows), "straight": segment(straight), "curve": segment(curve),
  }


def render_readme(evidence: dict) -> str:
  real = evidence["real_camera_reference"]
  meta = evidence["metadrive_closed_loop"]
  return f"""# Real-camera model replay reference

This public-safe bundle adds an official OpenPilot real-camera replay reference beside the MetaDrive closed-loop evidence. It isolates model input health; it is not a driving test, matched-scene accuracy study, or real-road performance claim.

| Observation | Official real-camera replay | MetaDrive 40° closed loop |
|---|---:|---:|
| Model outputs | {real['model_v2_count']} / {real['expected_frames']} | {meta['all']['samples']} telemetry samples |
| Left lane probability mean | {real['model']['left_lane_probability']['mean']:.4f} | {meta['all']['left_lane_probability_mean']:.4f} |
| Right lane probability mean | {real['model']['right_lane_probability']['mean']:.4f} | {meta['all']['right_lane_probability_mean']:.4f} |
| Path horizon mean | {real['model']['path_horizon_m']['mean']:.2f} m | {meta['all']['path_horizon_m_mean']:.2f} m |
| Functional status | `{real['functional_status']}` | `{meta['validity']}/{meta['outcome']}` |
| Host timing | `{real['timing_status']}` | not compared across runtimes |

The pretrained model produced full-count, fresh outputs on the upstream real-camera route, with roughly 0.9 lane probabilities and a 244 m mean path horizon. Under the retained MetaDrive camera contract, mean lane probabilities were roughly 0.01–0.02 and the path horizon was below 5 m. Because the scenes are not matched, this is a strong input-domain diagnostic contrast—not an accuracy ratio. It supports stopping ungrounded simulator camera tuning and keeping MetaDrive focused on integration, timing/fault injection, and actuator regression.

`evidence.json` binds the aggregate values to the retained real-camera summary and MetaDrive summary/telemetry with SHA-256. Raw video, decoded frames, per-frame telemetry, models, and local paths are excluded.
"""


def render_svg(evidence: dict) -> str:
  real, meta = evidence["real_camera_reference"], evidence["metadrive_closed_loop"]["all"]
  lane = [("Real left", real["model"]["left_lane_probability"]["mean"], "#2563eb"),
          ("Real right", real["model"]["right_lane_probability"]["mean"], "#2563eb"),
          ("MetaDrive left", meta["left_lane_probability_mean"], "#b45309"),
          ("MetaDrive right", meta["right_lane_probability_mean"], "#b45309")]
  parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="310" viewBox="0 0 760 310">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="25" y="28" font-family="sans-serif" font-size="18">Pretrained model output contrast (not matched-scene accuracy)</text>']
  for index, (label, value, color) in enumerate(lane):
    y = 48 + index * 38
    parts.extend((f'<text x="25" y="{y + 19}" font-family="sans-serif" font-size="13">{label}</text>',
                  f'<rect x="150" y="{y}" width="{500 * value:.1f}" height="24" fill="{color}"/>',
                  f'<text x="{158 + 500 * value:.1f}" y="{y + 18}" font-family="sans-serif" font-size="13">{value:.3f}</text>'))
  real_horizon = real["model"]["path_horizon_m"]["mean"]
  meta_horizon = meta["path_horizon_m_mean"]
  parts.extend(('<text x="25" y="220" font-family="sans-serif" font-size="14">Mean path horizon</text>',
                f'<rect x="150" y="204" width="{500 * real_horizon / 260:.1f}" height="24" fill="#2563eb"/>',
                f'<text x="655" y="222" font-family="sans-serif" font-size="13">real {real_horizon:.1f} m</text>',
                f'<rect x="150" y="242" width="{500 * meta_horizon / 260:.1f}" height="24" fill="#b45309"/>',
                f'<text x="{160 + 500 * meta_horizon / 260:.1f}" y="260" font-family="sans-serif" font-size="13">MetaDrive {meta_horizon:.1f} m</text>',
                '<text x="25" y="295" font-family="sans-serif" font-size="12">Different scenes; descriptive input-domain evidence only.</text>',
                '</svg>'))
  return "\n".join(parts) + "\n"


def build(real_summary_path: Path, metadrive_run: Path, output_dir: Path) -> dict:
  real = json.loads(real_summary_path.read_text(encoding="utf-8"))
  if real.get("functional_status") != "pass":
    raise ValueError("real-camera replay must be functionally complete")
  real_public = {key: real[key] for key in (
    "classification", "functional_status", "timing_status", "expected_frames", "model_v2_count",
    "driver_state_v2_count", "model_frame_coverage", "model", "timing_contract_s", "route", "source", "limitations")}
  real_public["summary_sha256"] = _digest(real_summary_path)
  evidence = {
    "schema_version": 1,
    "scope": "real_camera_replay_vs_metadrive_model_output_contrast_not_accuracy_or_road_performance",
    "real_camera_reference": real_public,
    "metadrive_closed_loop": _metadrive(metadrive_run),
    "interpretation": "consistent_with_simulator_input_domain_mismatch_requires_matched_scene_for_causal_attribution",
  }
  serialized = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
  if any(token in serialized for token in FORBIDDEN):
    raise ValueError("public evidence contains a forbidden local token")
  output_dir.mkdir(parents=True, exist_ok=True)
  (output_dir / "evidence.json").write_text(serialized, encoding="utf-8")
  (output_dir / "README.md").write_text(render_readme(evidence), encoding="utf-8")
  (output_dir / "comparison.svg").write_text(render_svg(evidence), encoding="utf-8")
  return evidence


def parser() -> argparse.ArgumentParser:
  result = argparse.ArgumentParser(description=__doc__)
  result.add_argument("--real-summary", type=Path, required=True)
  result.add_argument("--metadrive-run", type=Path, required=True)
  result.add_argument("--output-dir", type=Path, required=True)
  return result


if __name__ == "__main__":
  args = parser().parse_args()
  build(args.real_summary, args.metadrive_run, args.output_dir)
