# v0.6 simulator-specialist tight-DAgger delay-matrix sample

This release-friendly subset records the aggregate result of the local `outputs/v0.6-temporal-gamma-tight-dagger-tight-loop-delay-matrix-20260831` batch. It excludes the warm-up. Raw telemetry, camera frames, logs, report SVG, and generated artifact remain local.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) | Actual-delay median (ms) |
|---:|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.420300 | 24.57 |
| 50 | 3 | 3 / 3 / 0 | 0.421229 | 50.63 |
| 100 | 3 | 3 / 3 / 0 | 0.421403 | 100.69 |
| 150 | 3 | 3 / 3 / 0 | 0.421229 | 150.76 |

Every formal run completed 1,200 frames without lane departure, collision, or camera drop. It applies only to the local camera-only artifact on the fixed 45 m loop, seed, direction, rendering, and 2.0 m/s contract. It is not an openpilot pretrained-model, vehicle, road, or general geometry result.
