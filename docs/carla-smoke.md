# CARLA Windows–WSL smoke-test status

CARLA is outside the v0.1 MetaDrive release gate. The table is intentionally a smoke-test record, not a claim of complete closed-loop integration.

| Check | Status | Evidence / constraint |
|---|---|---|
| Windows server start | Manual verification required | Shader compilation and GPU driver state can affect startup |
| WSL client connection | Manual verification required | Host address must be supplied through local environment configuration |
| Synchronous tick | Experimental | Record tick count in the smoke log |
| RGB camera/state/control mapping | Experimental | Adapter lifecycle is not a v0.1 acceptance criterion |
| Actor cleanup/restart | Known risk | Destroyed actor and route-spawn failures were observed during development |

Any later PASS result must include the CARLA version, host/port, server log, client log, and a second-run result.
