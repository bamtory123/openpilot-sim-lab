from __future__ import annotations

from pathlib import Path
import json


def select_actuation_candidate(summary_paths: list[Path]) -> dict:
  """Select the lowest-error non-invalid, non-collision tuning candidate."""
  candidates = []
  for path in summary_paths:
    summary = json.loads(path.read_text(encoding="utf-8"))
    manifest = json.loads(path.with_name("manifest.json").read_text(encoding="utf-8"))
    ratio = manifest.get("actuation", {}).get("steer_ratio")
    reasons = set(summary.get("reasons", []))
    eligible = (summary.get("validity") != "invalid" and "collision" not in reasons and
                isinstance(ratio, (int, float)) and summary.get("metrics", {}).get("lateral_rmse_m") is not None)
    candidates.append({"summary": str(path), "run_id": summary.get("run_id"), "steer_ratio": ratio,
                       "validity": summary.get("validity"), "outcome": summary.get("outcome"),
                       "reasons": sorted(reasons), "lateral_rmse_m": summary.get("metrics", {}).get("lateral_rmse_m"),
                       "eligible": eligible})
  eligible = [candidate for candidate in candidates if candidate["eligible"]]
  selected = min(eligible, key=lambda candidate: (float(candidate["lateral_rmse_m"]), -float(candidate["steer_ratio"]))) if eligible else None
  return {"schema_version": 1, "scope": "pretrained_actuation_tuning_selection_only",
          "selection_rule": "lowest_lateral_rmse_then_higher_steer_ratio",
          "candidates": candidates, "selected_run_id": selected["run_id"] if selected else None,
          "selected_steer_ratio": selected["steer_ratio"] if selected else None,
          "changed_candidate_selected": bool(selected and float(selected["steer_ratio"]) != 8.0),
          "status": "selected" if selected else "no_eligible_candidate"}
