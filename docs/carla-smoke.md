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

| Check | Status | Evidence / constraint |
|---|---|---|
| Windows server start | Manual verification required | Shader compilation and GPU driver state can affect startup |
| WSL client import | Pass: v0.2 preparation | OpenPilot runtime imports `carla==0.9.16` |
| Windows–WSL client connection | Pass: one connectivity smoke | CARLA 0.9.16 handshake at `172.28.112.1:2000`; server stopped immediately after the check |
| Synchronous tick | Pass: one smoke | Two fixed-step ticks advanced frames `39941 → 39942`; prior world settings restored |
| RGB camera/state/control mapping | Experimental | Adapter lifecycle is not a v0.1 acceptance criterion |
| Actor cleanup/restart | Known risk | Destroyed actor and route-spawn failures were observed during development |

Any later PASS result must include the CARLA version, host/port, server log, client log, and a second-run result.

The retained connection/tick result does not include an actor, camera, OpenPilot bridge, control mapping, cleanup, or second run. It must not be described as CARLA closed-loop integration.
