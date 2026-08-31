#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"
: "${CUDA_SOAK_SECONDS:=20}"
: "${METADRIVE_RENDER_STEPS:=20}"

arguments=(preflight --scenario "${1:-configs/scenarios/md_default_loop_lane0_v1.yaml}")
if [[ "${SIMLAB_ALLOW_DIRTY:-0}" == "1" ]]; then
  arguments=(--allow-dirty "${arguments[@]}")
fi

SIM_TINYGRAD_DEVICE=CUDA "$OPENPILOT_PYTHON" scripts/check_cuda_runtime.py --duration-s "$CUDA_SOAK_SECONDS"
PYTHONPATH="$OPENPILOT_ROOT" "$OPENPILOT_PYTHON" scripts/check_metadrive_renderer.py --steps "$METADRIVE_RENDER_STEPS"
"$OPENPILOT_PYTHON" -m simlab.runner "${arguments[@]}"
