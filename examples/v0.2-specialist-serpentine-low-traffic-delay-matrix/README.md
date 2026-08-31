# v0.2 simulator-specialist serpentine low-traffic delay-matrix sample

This release-friendly subset records the local `outputs/v0.2-temporal-gamma-tight-dagger-serpentine-traffic03-delay-matrix-20260831` aggregate, excluding its warm-up. The scenario uses fixed seed `20260831`, `traffic_density: 0.03`, and the local v0.6 temporal specialist artifact. Raw telemetry, camera frames, logs, generated SVG, and the local artifact remain untracked.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) | Actual-delay median (ms) | Mean traffic actors | Maximum traffic actors |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.446965 | 24.18 | 3.34 | 4 |
| 50 | 3 | 3 / 3 / 0 | 0.447341 | 50.58 | 3.34 | 4 |
| 100 | 3 | 3 / 3 / 0 | 0.446280 | 100.65 | 3.34 | 4 |
| 150 | 3 | 3 / 3 / 0 | 0.447100 | 150.66 | 3.34 | 4 |

Every formal run completed 1,200 frames without ego lane departure, ego collision, or camera drop. The traffic count comes from MetaDrive's traffic manager and establishes actor presence only. This sample does not evaluate actor detection, prediction, yielding, braking, obstacle avoidance, arbitrary traffic density, pretrained openpilot, vehicles, or real roads. Its MetaDrive source provenance is deliberately dirty and is recorded in each local run manifest.
