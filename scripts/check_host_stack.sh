#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
: "${CUDA_SOAK_SECONDS:=20}"
: "${METADRIVE_RENDER_STEPS:=20}"
simlab_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host_stack_output="${HOST_STACK_OUTPUT:-}"
boot_before="$(cat /proc/sys/kernel/random/boot_id)"
gpu_before="$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,pstate --format=csv,noheader,nounits 2>/dev/null || true)"
stage="cuda"
cuda_json=""
renderer_json=""

write_host_stack_result() {
  local status="$1"
  local exit_code="$2"
  local boot_after
  local gpu_after
  boot_after="$(cat /proc/sys/kernel/random/boot_id)"
  gpu_after="$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,pstate --format=csv,noheader,nounits 2>/dev/null || true)"
  [[ -n "$host_stack_output" ]] || return
  mkdir -p "$(dirname "$host_stack_output")"
  "$OPENPILOT_PYTHON" - "$host_stack_output" "$status" "$exit_code" "$stage" "$boot_before" "$boot_after" "$cuda_json" "$renderer_json" "$simlab_root" "$OPENPILOT_ROOT" "$gpu_before" "$gpu_after" <<'PY'
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

path, status, exit_code, stage, boot_before, boot_after, cuda, renderer, simlab_root, openpilot_root, gpu_before, gpu_after = sys.argv[1:]
sys.path.insert(0, str(Path(simlab_root) / "src"))
from simlab.manifest import metadrive_source_metadata


def git_source(root):
  commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
  dirty = subprocess.run(["git", "-C", root, "status", "--porcelain"], capture_output=True, text=True, check=True)
  return {"commit": commit.stdout.strip(), "dirty": bool(dirty.stdout.strip())}


def parse_gpu_snapshot(raw):
  fields = ("name", "driver_version", "temperature_c", "utilization_percent", "memory_used_mib", "memory_total_mib", "pstate")
  values = [value.strip() for value in raw.splitlines()[0].split(",")] if raw.strip() else []
  return dict(zip(fields, values, strict=True)) if len(values) == len(fields) else None


Path(path).write_text(json.dumps({
  "schema_version": 4,
  "created_at_utc": datetime.now(timezone.utc).isoformat(),
  "status": status,
  "exit_code": int(exit_code),
  "failed_stage": None if status == "pass" else stage,
  "recorded_wsl_boot_id": boot_before,
  "observed_wsl_boot_id": boot_after,
  "wsl_boot_changed": boot_before != boot_after,
  "cuda": json.loads(cuda) if cuda else None,
  "renderer": json.loads(renderer) if renderer else None,
  "gpu_before": parse_gpu_snapshot(gpu_before),
  "gpu_after": parse_gpu_snapshot(gpu_after),
  "preflight": "pass" if status == "pass" else None,
  "provenance": {"sim_lab": git_source(simlab_root), "openpilot": git_source(openpilot_root),
                 "metadrive_source": metadrive_source_metadata(), "python_version": sys.version, "wsl_kernel": platform.release(),
                 "metadrive_version": importlib.metadata.version("metadrive-simulator"),
                 "gpu": (parse_gpu_snapshot(gpu_after) or {}).get("name")},
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

on_error() {
  local exit_code=$?
  trap - ERR
  write_host_stack_result "fail" "$exit_code"
  exit "$exit_code"
}

trap on_error ERR

arguments=(preflight --scenario "${1:-$simlab_root/configs/scenarios/md_default_loop_lane0_v1.yaml}")
if [[ "${SIMLAB_ALLOW_DIRTY:-0}" == "1" ]]; then
  arguments=(--allow-dirty "${arguments[@]}")
fi

cuda_output="$(SIM_TINYGRAD_DEVICE=CUDA "$OPENPILOT_PYTHON" "$simlab_root/scripts/check_cuda_runtime.py" --duration-s "$CUDA_SOAK_SECONDS")"
printf '%s\n' "$cuda_output"
cuda_json="$(printf '%s\n' "$cuda_output" | tail -n 1)"
stage="renderer"
renderer_output="$(PYTHONPATH="$OPENPILOT_ROOT" "$OPENPILOT_PYTHON" "$simlab_root/scripts/check_metadrive_renderer.py" --steps "$METADRIVE_RENDER_STEPS")"
printf '%s\n' "$renderer_output"
renderer_json="$(printf '%s\n' "$renderer_output" | tail -n 1)"
stage="preflight"
preflight_output="$("$OPENPILOT_PYTHON" -m simlab.runner "${arguments[@]}")"
printf '%s\n' "$preflight_output"
boot_after="$(cat /proc/sys/kernel/random/boot_id)"
if [[ "$boot_before" != "$boot_after" ]]; then
  echo "WSL boot ID changed during host-stack check: $boot_before -> $boot_after" >&2
  stage="boot_id"
  write_host_stack_result "fail" 1
  exit 1
fi
stage="complete"
write_host_stack_result "pass" 0
echo "host-stack boot ID unchanged: $boot_after"
