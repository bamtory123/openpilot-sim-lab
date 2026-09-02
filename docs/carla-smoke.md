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

| Check | Status | Evidence / constraint |
|---|---|---|
| Windows server start | Manual verification required | Shader compilation and GPU driver state can affect startup |
| WSL client connection | Manual verification required | Host address must be supplied through local environment configuration |
| Synchronous tick | Experimental | Record tick count in the smoke log |
| RGB camera/state/control mapping | Experimental | Adapter lifecycle is not a v0.1 acceptance criterion |
| Actor cleanup/restart | Known risk | Destroyed actor and route-spawn failures were observed during development |

Any later PASS result must include the CARLA version, host/port, server log, client log, and a second-run result.
