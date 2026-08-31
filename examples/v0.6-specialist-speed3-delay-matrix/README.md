# v0.6 simulator-specialist 3.0 m/s delay-matrix sample

This release-friendly subset contains one representative 150 ms `summary.json` and the aggregate result of the local `outputs/v0.2-speed3-delay-matrix-20260901` run. Raw telemetry, camera frames, logs, and generated reports remain local.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) | Median actual delay (ms) |
|---:|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.44359 | 22.07 |
| 50 | 3 | 3 / 3 / 0 | 0.59736 | 50.65 |
| 100 | 3 | 3 / 3 / 0 | 0.54405 | 100.57 |
| 150 | 3 | 3 / 3 / 0 | 0.43795 | 150.67 |

The excluded warm-up is not included in these counts. Every formal run met its 55-second active-time and 0.99 telemetry/road-camera coverage contracts with no lane departure, collision, or camera drop.

This applies only to the local v0.6 camera-only specialist artifact on the fixed default loop, fixed seed, gamma-0.8 rendering, and 3.0 m/s contract. It is not a pretrained-openpilot, real-vehicle, geometry-generalization, or broad speed-robustness result.
