# CARLA Windows–WSL smoke-test status

CARLA is outside the v0.1 MetaDrive release gate. The table is intentionally a smoke-test record, not a claim of complete closed-loop integration.

## v0.2 bounded adapter pilot

The separate `project/carla-adapter-pilot` branch now contains a minimal CARLA `World` adapter. It supplies CARLA RGB/state/vehicle-response data to the existing bridge and applies **OpenPilot commands only**. Route curvature, lane state, ground truth, specialist models, and safety overrides are not controller inputs.

The pilot is a bounded, city-route integration experiment, not an ADAS qualification. Its result is one of `invalid`, `integrated-but-not-stable`, or `bounded-pass`; the last means only that the declared 60-second simulator contract completed without the pilot's collision/lane/disengagement conditions. It never changes the v0.1 `not_qualified_yet` disposition.

Run ten isolated attempts from Windows. The wrapper starts and stops a new offscreen CARLA server per attempt, prepares Town04, creates a route asset before the bridge starts, preserves every attempt, and keeps dynamic traffic at zero:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\wsl.localhost\Ubuntu-24.04\home\hyunsung\src\openpilot-sim-lab\scripts\run_carla_adapter_pilot.ps1 -Attempts 10 -MeasurementSeconds 60
```

The route builder rejects the historical all-straight route asset. A failed route build or server/bridge startup is retained as infrastructure evidence and must not be retried silently into a selected-success matrix. Validate each completed pilot output without starting CARLA:

```bash
uv run python scripts/verify_carla_adapter_pilot.py outputs/carla-adapter-pilot/<run-id>
```

### Analysis-only RGB/route-label collection

The pilot can additionally retain sparse CARLA RGB frames for later **analysis-only** work. This remains outside the OpenPilot control path: the callback places an immutable RGB copy on a bounded writer queue, and a separate thread writes PNGs. Route ground truth is joined from already-recorded telemetry only after the run finishes; it is never returned to the bridge or used as a controller input.

Use `--capture-every-n-frames 20` for a 1 Hz capture at the adapter's 20 Hz camera rate:

```bash
uv run python scripts/run_carla_adapter_pilot.py ... --capture-every-n-frames 20
```

The run directory then contains `captures/`, `dataset_manifest.jsonl`, and `dataset_summary.json`. The manifest includes only measurement-period frames with matching route labels and sets every sample split to `analysis_only`. Any capture-writer overflow sets `dataset_summary.valid` to false; the run must not be used as a dataset. This is a provenance/label contract, not a trained model, an OpenPilot change, or a CARLA-driving result.

## Current v0.2 preparation

The current WSL OpenPilot runtime has the matching `carla==0.9.16` Python client installed. The Windows workstation has a CARLA 0.9.16 server executable at the local user path, but no server is started or implied by this preparation step.

Check the local client and an optional server executable path without starting CARLA:

```bash
/home/hyunsung/src/openpilot/.venv/bin/python scripts/carla_smoke_preflight.py \
  --server-exe /mnt/c/Users/Hyunsung\ Kim/CARLA_0.9.16/CarlaUE4.exe
```

Only after manually starting the server, request a WSL-to-Windows connection check explicitly:

```bash
/home/hyunsung/src/openpilot/.venv/bin/python scripts/carla_smoke_preflight.py \
  --connect --host <Windows-WSL-host-IP> --port 2000
```

Both commands are client/connectivity smoke checks only; neither starts an OpenPilot bridge nor qualifies CARLA closed-loop behavior.

To exercise only the CARLA synchronous world tick after the connection succeeds, add an explicit small tick budget. The script restores the prior world settings before it exits:

```bash
/home/hyunsung/src/openpilot/.venv/bin/python scripts/carla_smoke_preflight.py \
  --connect --host <Windows-WSL-host-IP> --port 2000 --sync-ticks 2
```

The CARLA-only smoke creates one brake-commanded vehicle and one 320×180 RGB camera, checks one image/state/control result, then destroys both actors and restores the world settings. It does not start OpenPilot:

```bash
/home/hyunsung/src/openpilot/.venv/bin/python scripts/carla_smoke_preflight.py \
  --connect --host <Windows-WSL-host-IP> --port 2000 --camera-state-control-smoke
```

For repeatable Windows–WSL evidence, use the PowerShell wrapper with a process-local execution-policy bypass. This avoids the Windows policy that otherwise blocks an unsigned script reached through the WSL UNC path; it does not change the machine policy. The wrapper starts one temporary offscreen server, waits for the WSL client handshake, writes server/connect/client logs plus `result.json` below `outputs/carla-smoke`, and stops that exact server in `finally` on either pass or failure:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File \\wsl.localhost\Ubuntu-24.04\home\hyunsung\src\openpilot-sim-lab\scripts\run_carla_camera_smoke.ps1
```

The wrapper discovers the current WSL default-route gateway; pass `-HostIp <gateway>` to override discovery. Its result remains CARLA-client smoke evidence only.

Verify a retained wrapper result without starting CARLA. The current wrapper writes schema 2, which also summarizes the client/server versions, camera dimensions, control, speed, and cleanup observation. The verifier remains compatible with earlier schema-1 retained results:

```bash
uv run python scripts/verify_carla_smoke_artifact.py outputs/carla-smoke/<run-id>/result.json
```

Summarize the retained local artifacts without starting CARLA or making a closed-loop claim. A malformed result stays visible as a failed artifact instead of aborting the whole summary:

```bash
uv run python scripts/summarize_carla_smoke_artifacts.py outputs/carla-smoke
```

A public-safe extract of the latest retained schema-2 observation is in [the CARLA client-smoke sample](../examples/v0.2-carla-client-smoke/README.md). It excludes local paths, raw camera data, and logs.

Regenerate and verify that sample only when the retained local source artifact is available:

```bash
uv run python scripts/build_carla_smoke_public_evidence.py outputs/carla-smoke/<run-id>/result.json --output-dir examples/v0.2-carla-client-smoke
uv run python scripts/verify_carla_smoke_public_evidence.py outputs/carla-smoke/<run-id>/result.json --output-dir examples/v0.2-carla-client-smoke
```

| Check | Status | Evidence / constraint |
|---|---|---|
| Windows server start | Manual verification required | Shader compilation and GPU driver state can affect startup |
| WSL client import | Pass: v0.2 preparation | OpenPilot runtime imports `carla==0.9.16` |
| Windows–WSL client connection | Pass: one connectivity smoke | CARLA 0.9.16 handshake at `172.28.112.1:2000`; server stopped immediately after the check |
| Synchronous tick | Pass: one smoke | Two fixed-step ticks advanced frames `39941 → 39942`; prior world settings restored |
| RGB camera/state/control mapping | 3 retained wrapper artifacts; 2 earlier manual observations | The three retained artifacts verify 320×180 RGB, brake command, and vehicle state; latest is schema 2 at `outputs/carla-smoke/20260902T103857Z/client.log`. The two earlier terminal-only observations are not equivalent retained evidence. No OpenPilot adapter or response-quality conclusion. |
| Actor cleanup/restart | 3 retained wrapper artifacts; 2 earlier manual observations | Each retained artifact verifies actor cleanup and world-setting restoration; latest schema-2 `result.json` records `server_stopped: true` with server/connect/client logs and client observations. Historical actor/route failures remain open. |

New CARLA smoke evidence must use the wrapper and include the CARLA version, host/port, server log, client log, and a second-run result. Earlier manual observations remain historical context only.

The retained connection/tick/camera result does not include an OpenPilot bridge, vehicle-response quality evaluation, route coverage, or closed-loop run. It must not be described as CARLA closed-loop integration.
