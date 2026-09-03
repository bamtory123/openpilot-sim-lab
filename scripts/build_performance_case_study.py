#!/usr/bin/env python3
"""Build a public-safe SIL improvement case-study bundle from retained summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import fmean


FORBIDDEN = ("/home/", "/mnt/", "C:\\", "telemetry.csv", "camera.csv", "manager.log")


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(path: Path) -> dict:
  data = json.loads(path.read_text(encoding="utf-8"))
  metrics = data.get("metrics", {})
  return {"sha256": digest(path), "scenario_id": data.get("scenario_id"), "target_delay_ms": data.get("target_delay_ms"),
          "validity": data.get("validity"), "outcome": data.get("outcome"), "reasons": data.get("reasons", []),
          "lateral_rmse_m": metrics.get("lateral_rmse_m"), "camera_frames_published": metrics.get("camera_frames_published"),
          "lane_departure_occurred": metrics.get("lane_departure_occurred"), "collision_occurred": metrics.get("collision_occurred")}


def require_pass(records: list[dict], label: str) -> None:
  if not records or any(record["validity"] != "valid" or record["outcome"] != "pass" for record in records):
    raise ValueError(f"{label} must contain only valid/pass summaries")


def mean_rmse(records: list[dict]) -> float:
  values = [float(record["lateral_rmse_m"]) for record in records if record["lateral_rmse_m"] is not None]
  if not values:
    raise ValueError("missing lateral RMSE")
  return fmean(values)


def delay_matrix(root: Path) -> dict:
  summaries = [compact(path) for path in root.rglob("summary.json") if "warmup" not in path.parts]
  groups = {delay: [record for record in summaries if record["target_delay_ms"] == delay] for delay in (0, 50, 100, 150)}
  if any(len(records) != 3 for records in groups.values()):
    raise ValueError("delay root must contain exactly three retained summaries per delay")
  for delay, records in groups.items():
    require_pass(records, f"delay {delay}")
  return {str(delay): {"runs": groups[delay], "mean_lateral_rmse_m": mean_rmse(groups[delay])} for delay in groups}


def compact_pretrained_tuning(selection_path: Path, evaluation_path: Path) -> dict:
  selection = json.loads(selection_path.read_text(encoding="utf-8"))
  evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
  candidates = [{key: candidate.get(key) for key in ("run_id", "steer_ratio", "validity", "outcome", "reasons", "lateral_rmse_m", "eligible")}
                for candidate in selection.get("candidates", [])]
  return {"selection_sha256": digest(selection_path), "evaluation_sha256": digest(evaluation_path),
          "selection_status": selection.get("status"), "selected_steer_ratio": selection.get("selected_steer_ratio"),
          "changed_candidate_selected": selection.get("changed_candidate_selected"), "candidates": candidates,
          "candidate_success": evaluation.get("candidate_success"), "next_step": evaluation.get("next_step"),
          "reason": evaluation.get("reason")}


def render_summary(evidence: dict) -> str:
  gamma, tight = evidence["specialist_cases"]
  pretrained = evidence["pretrained_actuation_calibration"]
  return f"""# SIL performance-improvement case study

## Claim boundary

This bundle demonstrates a repeatable SIL improvement loop. The pretrained calibration result is a retained negative interface-calibration result; the positive cases are simulator-specialist only. Neither establishes real-road performance or changes v0.1 qualification.

## Pretrained actuator calibration

| Step | Result |
|---|---:|
| Tuning candidates | 8: `valid/fail`; 4/2/1: `invalid/not_evaluated` from coverage loss |
| Selected ratio | {pretrained['selected_steer_ratio']} (the unchanged baseline) |
| Calibration conclusion | `{pretrained['next_step']}` — no changed candidate was evaluated as an improvement |

## Case 1 — targeted gamma/curve data

| Step | Result |
|---|---:|
| Fixed gamma-0.8 baseline | `{gamma['baseline']['validity']}/{gamma['baseline']['outcome']}`, {gamma['baseline']['lateral_rmse_m']:.5f} m lateral RMSE |
| Targeted-data candidate | 3 × `valid/pass`, mean {gamma['candidate_mean_lateral_rmse_m']:.5f} m |
| Fault evidence | 0/50/100/150 ms: 3 × `valid/pass` per delay |

## Case 2 — tight-loop DAgger data

| Step | Result |
|---|---:|
| Fixed 45 m baseline | `{tight['baseline']['validity']}/{tight['baseline']['outcome']}`, {tight['baseline']['lateral_rmse_m']:.5f} m lateral RMSE |
| 45 m candidate | 3 × `valid/pass`, mean {tight['fixed_mean_lateral_rmse_m']:.5f} m |
| 52 m held-out geometry | 3 × `valid/pass`, mean {tight['heldout_mean_lateral_rmse_m']:.5f} m |

The source SHA-256 values in `evidence.json` bind these public aggregate values to retained local summaries. The bundle excludes local paths, raw frames, telemetry, process logs, and model artifacts.
"""


def render_svg(evidence: dict) -> str:
  gamma, tight = evidence["specialist_cases"]
  bars = [
    ("Gamma baseline", gamma["baseline"]["lateral_rmse_m"], "#b45309"),
    ("Gamma candidate", gamma["candidate_mean_lateral_rmse_m"], "#15803d"),
    ("Tight baseline", tight["baseline"]["lateral_rmse_m"], "#b45309"),
    ("Tight candidate", tight["fixed_mean_lateral_rmse_m"], "#15803d"),
    ("52m held-out", tight["heldout_mean_lateral_rmse_m"], "#2563eb"),
  ]
  maximum = max(float(value) for _, value, _ in bars)
  parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300">',
           '<rect width="100%" height="100%" fill="white"/>', '<text x="30" y="30" font-family="sans-serif" font-size="18">Lateral RMSE (lower is better; simulator-only contracts)</text>']
  for index, (label, value, color) in enumerate(bars):
    y = 55 + index * 45
    width = 460 * float(value) / maximum
    parts.extend((f'<text x="30" y="{y + 20}" font-family="sans-serif" font-size="14">{label}</text>',
                  f'<rect x="220" y="{y}" width="{width:.1f}" height="28" fill="{color}"/>',
                  f'<text x="{228 + width:.1f}" y="{y + 20}" font-family="sans-serif" font-size="14">{float(value):.3f} m</text>'))
  parts.append('</svg>')
  return "\n".join(parts) + "\n"


def build(args: argparse.Namespace) -> dict:
  gamma_baseline = compact(args.gamma_baseline)
  gamma_candidates = [compact(path) for path in args.gamma_candidate]
  tight_baseline = compact(args.tight_baseline)
  tight_fixed = [compact(path) for path in args.tight_fixed]
  tight_heldout = [compact(path) for path in args.tight_heldout]
  require_pass(gamma_candidates, "gamma candidate")
  require_pass(tight_fixed, "tight fixed candidate")
  require_pass(tight_heldout, "tight held-out candidate")
  evidence = {
    "schema_version": 1,
    "scope": "simulator_specialist_improvement_case_study_not_pretrained_or_road_performance",
    "pretrained_actuation_calibration": compact_pretrained_tuning(args.pretrained_tuning, args.pretrained_evaluation),
    "specialist_cases": [
      {"id": "targeted_gamma_curve_data", "baseline": gamma_baseline, "candidate_runs": gamma_candidates,
       "candidate_mean_lateral_rmse_m": mean_rmse(gamma_candidates), "delay_matrix": delay_matrix(args.gamma_delay_root)},
      {"id": "tight_dagger_geometry", "baseline": tight_baseline, "fixed_runs": tight_fixed,
       "fixed_mean_lateral_rmse_m": mean_rmse(tight_fixed), "heldout_runs": tight_heldout,
       "heldout_mean_lateral_rmse_m": mean_rmse(tight_heldout)},
    ],
  }
  serialized = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
  if any(token in serialized for token in FORBIDDEN):
    raise ValueError("public evidence contains a forbidden local token")
  args.output_dir.mkdir(parents=True, exist_ok=True)
  (args.output_dir / "evidence.json").write_text(serialized, encoding="utf-8")
  (args.output_dir / "SUMMARY.md").write_text(render_summary(evidence), encoding="utf-8")
  (args.output_dir / "comparison.svg").write_text(render_svg(evidence), encoding="utf-8")
  return evidence


def parser() -> argparse.ArgumentParser:
  result = argparse.ArgumentParser(description=__doc__)
  result.add_argument("--gamma-baseline", type=Path, required=True)
  result.add_argument("--pretrained-tuning", type=Path, required=True)
  result.add_argument("--pretrained-evaluation", type=Path, required=True)
  result.add_argument("--gamma-candidate", type=Path, required=True, nargs=3)
  result.add_argument("--gamma-delay-root", type=Path, required=True)
  result.add_argument("--tight-baseline", type=Path, required=True)
  result.add_argument("--tight-fixed", type=Path, required=True, nargs=3)
  result.add_argument("--tight-heldout", type=Path, required=True, nargs=3)
  result.add_argument("--output-dir", type=Path, required=True)
  return result


if __name__ == "__main__":
  build(parser().parse_args())
