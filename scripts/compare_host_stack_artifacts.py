from __future__ import annotations

import json
from pathlib import Path
import sys

from verify_host_stack_artifact import verify


def read(path: Path) -> dict:
  verify(path)
  return json.loads(path.read_text(encoding="utf-8"))


def value(artifact: dict, *keys: str):
  current = artifact
  for key in keys:
    current = current.get(key) if isinstance(current, dict) else None
  return current


def rate(artifact: dict) -> float | None:
  elapsed = value(artifact, "cuda", "elapsed_ms")
  iterations = value(artifact, "cuda", "iterations")
  if not isinstance(elapsed, (int, float)) or not isinstance(iterations, (int, float)) or elapsed <= 0:
    return None
  return iterations * 1000 / elapsed


def main(baseline_path: Path, candidate_path: Path) -> None:
  baseline, candidate = read(baseline_path), read(candidate_path)
  provenance_keys = ("gpu", "python_version", "wsl_kernel", "metadrive_version")
  changed = [key for key in provenance_keys
             if value(baseline, "provenance", key) != value(candidate, "provenance", key)]
  for source in ("sim_lab", "openpilot"):
    if value(baseline, "provenance", source) != value(candidate, "provenance", source):
      changed.append(source)
  result = {
    "schema_version": 1,
    "scope": "descriptive_host_runtime_comparison_only",
    "comparison_status": "comparable" if baseline["status"] == candidate["status"] == "pass" else "infrastructure_failure_present",
    "baseline": {"path": str(baseline_path), "artifact_schema_version": baseline["schema_version"],
                 "status": baseline["status"], "cuda_iterations_per_s": rate(baseline),
                 "renderer_elapsed_ms": value(baseline, "renderer", "elapsed_ms")},
    "candidate": {"path": str(candidate_path), "artifact_schema_version": candidate["schema_version"],
                  "status": candidate["status"], "cuda_iterations_per_s": rate(candidate),
                  "renderer_elapsed_ms": value(candidate, "renderer", "elapsed_ms")},
    "changed_provenance": changed,
  }
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main(Path(sys.argv[1]), Path(sys.argv[2]))
