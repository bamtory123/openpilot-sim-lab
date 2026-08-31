#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"

output_root="${1:-outputs}"
find "$output_root" -type f -name manifest.json -printf '%h\n' | while IFS= read -r run_dir; do
  if [[ -f "$run_dir/scenario.yaml" && ! -f "$run_dir/summary.json" ]]; then
    "$OPENPILOT_PYTHON" -m simlab.runner recover --run-dir "$run_dir"
  fi
done
