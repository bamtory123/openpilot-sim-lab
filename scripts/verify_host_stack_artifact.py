from __future__ import annotations

import json
from pathlib import Path
import sys


def verify(path: Path) -> dict:
  artifact = json.loads(path.read_text(encoding="utf-8"))
  required = {"schema_version", "status", "exit_code", "failed_stage", "recorded_wsl_boot_id",
              "observed_wsl_boot_id", "wsl_boot_changed", "cuda", "renderer", "preflight"}
  missing = sorted(required - artifact.keys())
  if missing:
    raise ValueError(f"missing fields: {', '.join(missing)}")
  if artifact["schema_version"] not in {1, 2, 3} or artifact["status"] not in {"pass", "fail"}:
    raise ValueError("invalid schema or status")
  if artifact["schema_version"] == 2 and (not isinstance(artifact.get("provenance"), dict) or
                                           not {"sim_lab", "openpilot", "python_version", "gpu"} <= artifact["provenance"].keys()):
    raise ValueError("incomplete provenance")
  if artifact["schema_version"] == 3 and (not isinstance(artifact.get("provenance"), dict) or
                                           not {"sim_lab", "openpilot", "python_version", "wsl_kernel", "metadrive_version", "gpu"} <= artifact["provenance"].keys()):
    raise ValueError("incomplete runtime provenance")
  if artifact["status"] == "pass":
    if artifact["exit_code"] != 0 or artifact["failed_stage"] is not None or artifact["preflight"] != "pass":
      raise ValueError("inconsistent pass artifact")
    if artifact["wsl_boot_changed"] or artifact["recorded_wsl_boot_id"] != artifact["observed_wsl_boot_id"]:
      raise ValueError("pass artifact has a changed boot ID")
  elif artifact["exit_code"] == 0 or not artifact["failed_stage"]:
    raise ValueError("inconsistent failure artifact")
  return {"schema_version": 1, "status": "pass", "artifact_schema_version": artifact["schema_version"],
          "artifact_status": artifact["status"], "path": str(path)}


if __name__ == "__main__":
  print(json.dumps(verify(Path(sys.argv[1])), sort_keys=True))
