#!/usr/bin/env python3
"""Build public-safe evidence for the 3.5 m/s targeted-DAgger rejection."""

import argparse
import hashlib
import json
from pathlib import Path


FORBIDDEN = ("/home/", "/mnt/", "C:\\", "telemetry.csv", "manager.log", "specialist_manifest.jsonl")


def digest(path: Path) -> str:
  return hashlib.sha256(path.read_bytes()).hexdigest()


def render_summary(evidence: dict) -> str:
  baseline, candidate = evidence["baseline"], evidence["candidate"]
  anchored = evidence["anchored_followup"]
  return f"""# 3.5 m/s targeted-DAgger boundary case

## Decision

The targeted candidate was rejected after one held-out diagnostic. It departed at {candidate['departure_progress_m']:.2f} m, earlier than the v0.6 repeatable {baseline['departure_progress_m_range'][0]:.2f}–{baseline['departure_progress_m_range'][1]:.2f} m boundary, and its observed partial-run lateral RMSE increased from {baseline['observed_mean_lateral_rmse_m']:.5f} to {candidate['observed_lateral_rmse_m']:.5f} m.

| Stage | Result |
|---|---|
| v0.6 boundary | 3 × `invalid/not_evaluated`; common-curve departure |
| Failure localization | `{evidence['localization']['classification']}`; capture frames {evidence['localization']['capture_start_frame']}–{evidence['localization']['capture_end_frame']} |
| Targeted data | {evidence['training']['train_samples']} train + {evidence['training']['validation_samples']} validation samples |
| v0.7 held-out diagnostic | `{candidate['validity']}/{candidate['outcome']}`; lane departure, no collision/drop/host restart |
| Gate action | `{evidence['decision']}` |

Both RMSE values are incomplete-run diagnostics and are performance-ineligible. No repeated candidate evaluation or delay matrix was run. This simulator-only negative case demonstrates rejection by the SIL improvement gate; it is not road-performance evidence.

## Anchored follow-up

An offline trust-region gate selected the minimum blend alpha `{anchored['selected_alpha']}` that improved targeted validation by {anchored['targeted_relative_improvement']:.2%} while limiting original-validation RMSE increase to {anchored['original_relative_change']:.2%}. Three fresh-seed closed-loop repeats produced `{anchored['pass_count']} pass / {anchored['fail_count']} fail`; lateral RMSE was {', '.join(f'{value:.5f}' for value in anchored['lateral_rmse_m'])} m. The failed repeat departed at 49.85 m despite unchanged source and host contracts. The candidate is therefore rejected for insufficient repeatability margin, and no regression or delay matrix follows.
"""


def render_svg(evidence: dict) -> str:
  baseline = evidence["baseline"]["observed_mean_lateral_rmse_m"]
  candidate = evidence["candidate"]["observed_lateral_rmse_m"]
  maximum = max(baseline, candidate)
  bars = (("v0.6 boundary (3-run observed mean)", baseline, "#64748b"),
          ("v0.7 targeted candidate (single run)", candidate, "#b91c1c"))
  parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="190" viewBox="0 0 800 190">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="25" y="28" font-family="sans-serif" font-size="17">Observed partial-run lateral RMSE — diagnostic only</text>']
  for index, (label, value, color) in enumerate(bars):
    y = 55 + index * 55
    width = 390 * value / maximum
    parts.extend((f'<text x="25" y="{y + 20}" font-family="sans-serif" font-size="13">{label}</text>',
                  f'<rect x="320" y="{y}" width="{width:.1f}" height="28" fill="{color}"/>',
                  f'<text x="{328 + width:.1f}" y="{y + 20}" font-family="sans-serif" font-size="13">{value:.3f} m</text>'))
  parts.append('<text x="25" y="178" font-family="sans-serif" font-size="12" fill="#475569">Both runs are invalid/not_evaluated; lower is better, but neither value is qualification evidence.</text>')
  parts.append('</svg>')
  return "\n".join(parts) + "\n"


def build(args: argparse.Namespace) -> dict:
  gate = json.loads(args.baseline_gate.read_text(encoding="utf-8"))
  localization = json.loads(args.departure_analysis.read_text(encoding="utf-8"))
  candidate_summary = json.loads(args.candidate_summary.read_text(encoding="utf-8"))
  candidate_analysis = json.loads(args.candidate_analysis.read_text(encoding="utf-8"))
  attempt = json.loads(args.candidate_attempt.read_text(encoding="utf-8"))
  training = json.loads(args.training_metrics.read_text(encoding="utf-8"))
  anchored_selection = json.loads(args.anchored_selection.read_text(encoding="utf-8"))
  anchored_gate = json.loads(args.anchored_gate.read_text(encoding="utf-8"))
  manifests = [path.read_text(encoding="utf-8").splitlines() for path in args.targeted_manifest]
  candidate_departure = candidate_analysis["runs"][0]["first_lane_departure"]
  metrics = candidate_summary["metrics"]
  window = localization["recommended_capture_window"]
  evidence = {
    "schema_version": 1,
    "scope": "simulator_specialist_speed_boundary_negative_case_not_road_performance",
    "baseline": {
      "gate_sha256": digest(args.baseline_gate),
      "performance_eligible": gate["aggregate"]["performance_eligible"],
      "observed_mean_lateral_rmse_m": gate["aggregate"]["observed_mean_lateral_rmse_m"],
      "departure_progress_m_range": localization["departure_progress_m_range"],
    },
    "localization": {
      "analysis_sha256": digest(args.departure_analysis),
      "classification": localization["classification"],
      "common_reference_curvature_1pm": localization["common_reference_curvature_1pm"],
      "capture_start_frame": window["start_frame"], "capture_end_frame": window["end_frame"],
    },
    "training": {
      "manifest_sha256": [digest(path) for path in args.targeted_manifest],
      "train_samples": len(manifests[0]), "validation_samples": len(manifests[1]),
      "metrics_sha256": digest(args.training_metrics), "artifact_sha256": digest(args.artifact),
      "train_pairs": training["train_pairs"], "validation_pairs": training["validation_pairs"],
      "validation_rmse_normalized_steer": training["validation_rmse_normalized_steer"],
    },
    "candidate": {
      "summary_sha256": digest(args.candidate_summary), "analysis_sha256": digest(args.candidate_analysis),
      "attempt_sha256": digest(args.candidate_attempt), "validity": candidate_summary["validity"],
      "outcome": candidate_summary["outcome"], "reasons": candidate_summary["reasons"],
      "observed_lateral_rmse_m": metrics["lateral_rmse_m"],
      "departure_frame": candidate_departure["simulation_frame"],
      "departure_progress_m": candidate_departure["route_progress_m"],
      "collision_occurred": metrics["collision_occurred"],
      "camera_frames_dropped": metrics["camera_frames_dropped"],
      "wsl_boot_changed": attempt["wsl_boot_changed"],
    },
    "anchored_followup": {
      "selection_sha256": digest(args.anchored_selection), "gate_sha256": digest(args.anchored_gate),
      "selected_alpha": anchored_selection["selected"]["alpha"],
      "original_relative_change": anchored_selection["selected"]["original_relative_change"],
      "targeted_relative_improvement": anchored_selection["selected"]["targeted_relative_improvement"],
      "gate_status": anchored_gate["status"],
      "performance_eligible": anchored_gate["aggregate"]["performance_eligible"],
      "pass_count": sum(run["validity"] == "valid" and run["outcome"] == "pass" for run in anchored_gate["runs"]),
      "fail_count": sum(run["validity"] == "valid" and run["outcome"] == "fail" for run in anchored_gate["runs"]),
      "lateral_rmse_m": [run["lateral_rmse_m"] for run in anchored_gate["runs"]],
      "decision": "reject_for_insufficient_repeatability_margin",
    },
    "decision": "reject_candidate_stop_before_repeat_and_delay_matrix",
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
  result.add_argument("--baseline-gate", type=Path, required=True)
  result.add_argument("--departure-analysis", type=Path, required=True)
  result.add_argument("--targeted-manifest", type=Path, nargs=2, required=True)
  result.add_argument("--training-metrics", type=Path, required=True)
  result.add_argument("--artifact", type=Path, required=True)
  result.add_argument("--candidate-summary", type=Path, required=True)
  result.add_argument("--candidate-analysis", type=Path, required=True)
  result.add_argument("--candidate-attempt", type=Path, required=True)
  result.add_argument("--anchored-selection", type=Path, required=True)
  result.add_argument("--anchored-gate", type=Path, required=True)
  result.add_argument("--output-dir", type=Path, required=True)
  return result


if __name__ == "__main__":
  build(parser().parse_args())
