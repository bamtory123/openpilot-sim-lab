#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"

output_root="${1:-outputs}"
find "$output_root" -type f -name manifest.json -printf '%h\n' | while IFS= read -r run_dir; do
  if [[ -f "$run_dir/scenario.yaml" && ! -f "$run_dir/summary.json" ]]; then
    PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner recover --run-dir "$run_dir"
  fi
done
find "$output_root" -type f -name attempt.json -printf '%h\n' | while IFS= read -r attempt_dir; do
  if [[ ! -f "$attempt_dir/summary.json" ]] && ! find "$attempt_dir/runs" -name summary.json -print -quit 2>/dev/null | grep -q .; then
    PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner recover-attempt --attempt-dir "$attempt_dir"
  fi
done
