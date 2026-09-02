# CARLA client-smoke public sample

This is a public-safe extract from one retained CARLA client-smoke artifact. It is outside the v0.1 MetaDrive release gate and does not demonstrate an OpenPilot bridge, closed loop, route coverage, response quality, or driving capability.

## Retained observation

| Field | Value |
|---|---|
| Artifact schema | 2 |
| CARLA client / server | 0.9.16 / 0.9.16 |
| RGB camera | 320×180 |
| Applied command | throttle=0.0, steer=0.0, brake=1.0 |
| Reported speed (m/s) | 1.470000147819519 |
| Actor cleanup / world restore / server stop | True / True / True |

The source artifact SHA-256 is `0d768498fba4743feec0036a79a3c8afbcef07807b84d3f02c190147f1d6fdae`. It excludes local paths, server/client logs, and raw camera data. Verify the retained local artifact with `scripts/verify_carla_smoke_artifact.py` before regenerating this sample.
