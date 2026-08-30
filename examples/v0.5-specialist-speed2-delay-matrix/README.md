# v0.5 simulator-specialist 2 m/s delay-matrix sample

This small package is a release-friendly subset of the local matrix at `outputs/v0.5-temporal-dagger-speed2-delay-matrix-20260830`. It contains one representative 150 ms `summary.json` and the aggregate table below. Full telemetry, camera frames, process logs, and the locally generated specialist artifact are intentionally excluded.

| Target delay (ms) | Formal runs | Valid / pass / invalid | Median lateral RMSE (m) | Actual-delay median (ms) |
|---:|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.333038 | 23.48 |
| 50 | 3 | 3 / 3 / 0 | 0.332900 | 50.57 |
| 100 | 3 | 3 / 3 / 0 | 0.333164 | 100.66 |
| 150 | 3 | 3 / 3 / 0 | 0.332763 | 150.63 |

Every formal run completed the 1,200-frame measurement budget without lane departure, collision, or camera drop. This result applies only to the opt-in camera-only simulator-specialist artifact at 2.0 m/s on the fixed MetaDrive loop. It does not describe the pretrained openpilot baseline, the 3.0/4.0 m/s specialist conditions, real vehicles, or real-road performance.

Reproduce with `configs/scenarios/md_default_loop_lane0_temporal_dagger_speed2_heldout_v1.yaml` and the `batch` command documented in [simulator-specialist](../../docs/simulator-specialist.md).
