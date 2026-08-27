from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

from .config import Scenario


def _command(args: list[str], cwd: Path | None = None) -> str | None:
  try:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip() or None
  except (OSError, subprocess.CalledProcessError):
    return None


def git_metadata(root: Path) -> dict[str, Any]:
  return {
    "commit": _command(["git", "rev-parse", "HEAD"], root),
    "dirty": bool(_command(["git", "status", "--porcelain"], root)),
    "submodules": _command(["git", "submodule", "status", "--recursive"], root) or "",
  }


def build_manifest(run_id: str, scenario: Scenario, simlab_root: Path, openpilot_root: Path, command: list[str]) -> dict[str, Any]:
  try:
    from importlib.metadata import version
    metadrive_version = version("metadrive-simulator")
  except Exception:
    metadrive_version = "not-installed"
  env = {key: os.environ[key] for key in ("SIMULATION", "SIM_TINYGRAD_DEVICE", "OPENPILOT_ROOT") if key in os.environ}
  return {
    "schema_version": 1, "run_id": run_id, "scenario_hash": scenario.hash,
    "sim_lab": git_metadata(simlab_root), "openpilot": git_metadata(openpilot_root),
    "python_version": sys.version, "metadrive_version": metadrive_version,
    "wsl_kernel": platform.release(), "gpu": _command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]),
    "driver": _command(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"]),
    "command": command, "environment": env,
  }


def write_json(path: Path, payload: dict[str, Any]) -> None:
  path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
