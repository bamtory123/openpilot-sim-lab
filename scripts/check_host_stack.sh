#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
: "${CUDA_SOAK_SECONDS:=20}"
: "${METADRIVE_RENDER_STEPS:=20}"
host_stack_output="${HOST_STACK_OUTPUT:-}"
boot_before="$(cat /proc/sys/kernel/random/boot_id)"

arguments=(preflight --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}")
if [[ "${SIMLAB_ALLOW_DIRTY:-0}" == "1" ]]; then
  arguments=(--allow-dirty "${arguments[@]}")
fi

cuda_output="$(SIM_TINYGRAD_DEVICE=CUDA "$OPENPILOT_PYTHON" scripts/check_cuda_runtime.py --duration-s "$CUDA_SOAK_SECONDS")"
printf '%s\n' "$cuda_output"
cuda_json="$(printf '%s\n' "$cuda_output" | tail -n 1)"
renderer_output="$(PYTHONPATH="$OPENPILOT_ROOT" "$OPENPILOT_PYTHON" scripts/check_metadrive_renderer.py --steps "$METADRIVE_RENDER_STEPS")"
printf '%s\n' "$renderer_output"
renderer_json="$(printf '%s\n' "$renderer_output" | tail -n 1)"
preflight_output="$("$OPENPILOT_PYTHON" -m simlab.runner "${arguments[@]}")"
printf '%s\n' "$preflight_output"
boot_after="$(cat /proc/sys/kernel/random/boot_id)"
if [[ "$boot_before" != "$boot_after" ]]; then
  echo "WSL boot ID changed during host-stack check: $boot_before -> $boot_after" >&2
  exit 1
fi
if [[ -n "$host_stack_output" ]]; then
  mkdir -p "$(dirname "$host_stack_output")"
  "$OPENPILOT_PYTHON" - "$host_stack_output" "$boot_before" "$boot_after" "$cuda_json" "$renderer_json" <<'PY'
import json
from pathlib import Path
import sys

path, boot_before, boot_after, cuda, renderer = sys.argv[1:]
Path(path).write_text(json.dumps({
  "schema_version": 1,
  "status": "pass",
  "recorded_wsl_boot_id": boot_before,
  "observed_wsl_boot_id": boot_after,
  "wsl_boot_changed": boot_before != boot_after,
  "cuda": json.loads(cuda),
  "renderer": json.loads(renderer),
  "preflight": "pass",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
fi
echo "host-stack boot ID unchanged: $boot_after"
