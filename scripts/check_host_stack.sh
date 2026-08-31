#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
: "${CUDA_SOAK_SECONDS:=20}"
: "${METADRIVE_RENDER_STEPS:=20}"
boot_before="$(cat /proc/sys/kernel/random/boot_id)"

arguments=(preflight --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}")
if [[ "${SIMLAB_ALLOW_DIRTY:-0}" == "1" ]]; then
  arguments=(--allow-dirty "${arguments[@]}")
fi

SIM_TINYGRAD_DEVICE=CUDA "$OPENPILOT_PYTHON" scripts/check_cuda_runtime.py --duration-s "$CUDA_SOAK_SECONDS"
PYTHONPATH="$OPENPILOT_ROOT" "$OPENPILOT_PYTHON" scripts/check_metadrive_renderer.py --steps "$METADRIVE_RENDER_STEPS"
"$OPENPILOT_PYTHON" -m simlab.runner "${arguments[@]}"
boot_after="$(cat /proc/sys/kernel/random/boot_id)"
if [[ "$boot_before" != "$boot_after" ]]; then
  echo "WSL boot ID changed during host-stack check: $boot_before -> $boot_after" >&2
  exit 1
fi
echo "host-stack boot ID unchanged: $boot_after"
