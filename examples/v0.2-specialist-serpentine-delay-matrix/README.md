# v0.2 simulator-specialist serpentine delay-matrix sample

This release-friendly subset records the local `outputs/v0.2-temporal-gamma-tight-dagger-serpentine-delay-matrix-20260831` aggregate, excluding its warm-up. Raw telemetry, camera frames, logs, generated report SVG, and local artifact remain untracked.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) | Actual-delay median (ms) |
|---:|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.445708 | 24.48 |
| 50 | 3 | 3 / 3 / 0 | 0.445983 | 50.59 |
| 100 | 3 | 3 / 3 / 0 | 0.445983 | 100.70 |
| 150 | 3 | 3 / 3 / 0 | 0.445642 | 150.71 |

Every formal run completed 1,200 frames without lane departure, collision, or camera drop. This applies only to the local camera-only artifact and fixed versioned serpentine contract; it is not a pretrained-openpilot, arbitrary-route, vehicle, or real-road result.
