# v0.6 simulator-specialist gamma-0.8 delay-matrix sample

This release-friendly subset contains one representative 150 ms `summary.json` and the aggregate result of the local `outputs/v0.6-temporal-gamma-curve-speed2-gamma08-delay-matrix-20260830` run. Raw telemetry, camera frames, logs, and the generated artifact remain local.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) |
|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.286913 |
| 50 | 3 | 3 / 3 / 0 | 0.287740 |
| 100 | 3 | 3 / 3 / 0 | 0.286968 |
| 150 | 3 | 3 / 3 / 0 | 0.287576 |

Every formal run completed 1,200 frames without lane departure, collision, or camera drop. This applies only to the v0.6 local camera-only artifact on the fixed 60 m loop, 2.0 m/s, gamma-0.8 contract. It is not an openpilot pretrained-model, vehicle, road, or geometry-generalization result.
