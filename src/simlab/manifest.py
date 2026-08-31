from __future__ import annotations

import json
import hashlib
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


def metadrive_source_metadata() -> dict[str, Any]:
  try:
    import metadrive
    root = Path(metadrive.__file__).resolve().parent.parent
  except (ImportError, AttributeError, TypeError):
    return {"path": None, "commit": None, "dirty": None, "submodules": ""}
  return {"path": str(root), **git_metadata(root)}


def metadrive_assets_metadata() -> dict[str, Any]:
  source = metadrive_source_metadata().get("path")
  assets = Path(source) / "metadrive" / "assets" if source else None
  version_file = assets / "version.txt" if assets else None
  vehicle_file = assets / "models" / "ferra" / "vehicle.gltf" if assets else None
  return {
    "path": str(assets) if assets else None,
    "version": version_file.read_text(encoding="utf-8").strip() if version_file and version_file.is_file() else None,
    "ferra_vehicle_available": bool(vehicle_file and vehicle_file.is_file()),
    "ferra_vehicle_sha256": hashlib.sha256(vehicle_file.read_bytes()).hexdigest() if vehicle_file and vehicle_file.is_file() else None,
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
    "metadrive_source": metadrive_source_metadata(),
    "metadrive_assets": metadrive_assets_metadata(),
    "python_version": sys.version, "metadrive_version": metadrive_version,
    "wsl_kernel": platform.release(), "gpu": _command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]),
    "driver": _command(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"]),
    "command": command, "environment": env,
  }


def write_json(path: Path, payload: dict[str, Any]) -> None:
  path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
