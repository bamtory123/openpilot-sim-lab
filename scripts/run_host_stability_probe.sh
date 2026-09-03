#!/usr/bin/env bash
set -euo pipefail

: "${OPENPILOT_ROOT:?Set OPENPILOT_ROOT to the instrumented openpilot checkout}"
: "${OPENPILOT_PYTHON:=$OPENPILOT_ROOT/.venv/bin/python}"

scenario="${1:?Pass a scenario path}"
output_root="${2:?Pass an output root}"
attempt_dir="$output_root/host-probe-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$attempt_dir"
cp "$scenario" "$attempt_dir/scenario.yaml"
boot_before="$(cat /proc/sys/kernel/random/boot_id)"
kernel_before="$(uname -r)"
uptime_before="$(cut -d' ' -f1 /proc/uptime)"
gpu_before="$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,pstate --format=csv,noheader,nounits 2>/dev/null || true)"

PYTHONPATH=src "$OPENPILOT_PYTHON" - "$attempt_dir/attempt.json" "$scenario" "$attempt_dir/scenario.yaml" "$boot_before" "$kernel_before" "$uptime_before" "$gpu_before" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from simlab.config import load_scenario

path, scenario, snapshot, boot_id, kernel, uptime, gpu = map(str, sys.argv[1:])
Path(path).write_text(json.dumps({
  "schema_version": 2,
  "created_at_utc": datetime.now(timezone.utc).isoformat(),
  "scenario_path": str(Path(scenario).resolve()),
  "scenario_snapshot": str(Path(snapshot).resolve()),
  "scenario_hash": load_scenario(Path(snapshot)).hash,
  "recorded_wsl_boot_id": boot_id,
  "host_start": {"wsl_kernel": kernel, "uptime_s": float(uptime), "gpu": gpu or None},
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

set +e
PYTHONPATH=src "$OPENPILOT_PYTHON" -m simlab.runner --allow-dirty run --scenario "$scenario" --outputs "$attempt_dir/runs"
exit_code=$?
set -e
boot_after="$(cat /proc/sys/kernel/random/boot_id)"
kernel_after="$(uname -r)"
uptime_after="$(cut -d' ' -f1 /proc/uptime)"
gpu_after="$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,pstate --format=csv,noheader,nounits 2>/dev/null || true)"

"$OPENPILOT_PYTHON" - "$attempt_dir/attempt.json" "$exit_code" "$boot_after" "$kernel_after" "$uptime_after" "$gpu_after" <<'PY'
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

path, exit_code, boot_id, kernel, uptime, gpu = sys.argv[1:]
payload = json.loads(Path(path).read_text(encoding="utf-8"))
payload.update({
  "completed_at_utc": datetime.now(timezone.utc).isoformat(),
  "runner_exit_code": int(exit_code),
  "observed_wsl_boot_id": boot_id,
  "wsl_boot_changed": payload["recorded_wsl_boot_id"] != boot_id,
  "host_end": {"wsl_kernel": kernel, "uptime_s": float(uptime), "gpu": gpu or None},
})
Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

exit "$exit_code"
