#!/usr/bin/env python3
"""Evaluate a reference-derived MetaDrive color candidate without changing pretrained OpenPilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from simlab.config import load_scenario, scenario_with_camera_color_affine
from simlab.manifest import write_json
from simlab.runner import run_once


def passed(summary_path: Path) -> bool:
  summary = json.loads(summary_path.read_text(encoding="utf-8"))
  return summary.get("validity") == "valid" and summary.get("outcome") == "pass"


def candidate_from_audit(path: Path) -> dict[str, list[float]]:
  audit = json.loads(path.read_text(encoding="utf-8"))
  if audit.get("scope") != "camera_domain_moment_match_diagnostic_not_perception_or_road_performance":
    raise RuntimeError("camera audit has an unsupported scope")
  affine = audit.get("recommended_environment_overlay", {}).get("camera_color_affine")
  if not isinstance(affine, dict):
    raise RuntimeError("camera audit does not contain a color-affine proposal")
  return affine


def is_identity(affine: dict[str, list[float]]) -> bool:
  return affine.get("gain_rgb") == [1.0, 1.0, 1.0] and affine.get("bias_rgb") == [0.0, 0.0, 0.0]


def run_repetitions(scenario, repetitions: int, output_root: Path, allow_dirty: bool) -> list[Path]:
  return [run_once(scenario, output_root=output_root, allow_dirty=allow_dirty) for _ in range(repetitions)]


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--audit", type=Path, required=True)
  parser.add_argument("--fixed-scenario", type=Path, required=True)
  parser.add_argument("--heldout-scenario", type=Path, required=True)
  parser.add_argument("--output-root", type=Path, required=True)
  parser.add_argument("--allow-dirty", action="store_true")
  args = parser.parse_args()
  affine = candidate_from_audit(args.audit)
  audit_sha256 = hashlib.sha256(args.audit.read_bytes()).hexdigest()
  if is_identity(affine):
    result = {"schema_version": 1, "scope": "pretrained_camera_color_evaluation_not_road_performance",
              "audit_sha256": audit_sha256, "camera_color_affine": affine, "runs": {}, "candidate_success": False,
              "next_step": "retain_no_change_audit", "reason": "identity_color_affine"}
    args.output_root.mkdir(parents=True, exist_ok=True)
    write_json(args.output_root / "evaluation.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return
  fixed, heldout = load_scenario(args.fixed_scenario), load_scenario(args.heldout_scenario)
  candidate_fixed = scenario_with_camera_color_affine(fixed, affine)
  candidate_heldout = scenario_with_camera_color_affine(heldout, affine)
  runs = {
    "fixed_baseline": run_repetitions(fixed, 3, args.output_root / "fixed-baseline", args.allow_dirty),
    "fixed_candidate": run_repetitions(candidate_fixed, 3, args.output_root / "fixed-candidate", args.allow_dirty),
    "heldout_baseline": run_repetitions(heldout, 3, args.output_root / "heldout-baseline", args.allow_dirty),
    "heldout_candidate": run_repetitions(candidate_heldout, 3, args.output_root / "heldout-candidate", args.allow_dirty),
  }
  candidate_paths = runs["fixed_candidate"] + runs["heldout_candidate"]
  candidate_success = all(passed(path / "summary.json") for path in candidate_paths)
  result = {"schema_version": 1, "scope": "pretrained_camera_color_evaluation_not_road_performance",
            "audit_sha256": audit_sha256, "camera_color_affine": affine,
            "runs": {key: [str(path / "summary.json") for path in value] for key, value in runs.items()},
            "candidate_success": candidate_success,
            "next_step": "run_delay_matrix" if candidate_success else "retain_negative_result_no_delay_matrix"}
  write_json(args.output_root / "evaluation.json", result)
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()
