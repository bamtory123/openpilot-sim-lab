# CARLA Windows–WSL smoke-test status

CARLA is outside the v0.1 MetaDrive release gate. The table is intentionally a smoke-test record, not a claim of complete closed-loop integration.

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

Summarize the retained local artifacts without starting CARLA or making a closed-loop claim:

```bash
uv run python scripts/summarize_carla_smoke_artifacts.py outputs/carla-smoke
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
