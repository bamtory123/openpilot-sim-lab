# Progress

## Completed

- MetaDrive reference-lane ground truth, scenario manifest, lifecycle events, and non-blocking camera-delay telemetry.
- Formal `md_default_loop_lane0_v1` delay matrix: warm-up excluded, then 0/50/100/150 ms in three interleaved repetitions each.
- World-frame geometry diagnostics and simulator-only controller experiments, kept separate from the formal model-driven result.
- Unit tests, report generation, and public instrumentation branches.

## Formal matrix: 2026-08-28

Output root: `outputs/v0.2-formal-delay-matrix-20260828` (local, reproducible run artifact).

| Delay (ms) | Runs | Result | Median lateral RMSE (m) |
|---:|---:|---|---:|
| 0 | 3 | all `valid/fail`: lane departure | 0.664 |
| 50 | 3 | all `valid/fail`: lane departure | 0.666 |
| 100 | 3 | all `valid/fail`: lane departure | 0.664 |
| 150 | 3 | all `valid/fail`: lane departure | 0.675 |

All 12 formal runs met the data-validity contract. This is a repeatable failure of the current model-driven simulator baseline, not evidence of a passing driving system or a real-road conclusion. The generated `report.md` and `report.svg` remain local artifacts; the release packaging step will select a small reproducible sample rather than commit the full run data.

Camera transport audit across the formal runs found monotonic unique source frame IDs, capture-before-publish timestamps, and zero dropped road frames. Actual delay ranges were 17.65–40.15 ms for the 0 ms scheduler path, 50.34–61.14 ms for 50 ms, 100.29–106.66 ms for 100 ms, and 150.31–159.97 ms for 150 ms. The nonzero 0 ms range is publisher scheduling overhead and must be reported as actual delay rather than treated as an exact zero-latency path.

On 2026-08-29, the workstation was revalidated after updating the Windows NVIDIA driver to 616.56. Windows and WSL both exposed an RTX 4080 with CUDA UMD 13.4; tinygrad CUDA arithmetic, MetaDrive reset/step/close, OpenPilot static checks, and the sim-lab test suite succeeded. A fresh manifest smoke check recorded driver 616.56, the WSL kernel, MetaDrive 0.4.2.3, and clean repository state.

The runner now applies `configs/thresholds.yaml` during classification. In addition to lane departure and collision, measured absolute lateral error above 1.25 m is recorded as `lateral_error_threshold` and produces `valid/fail`. Reclassifying the frozen formal matrix preserves its validity and adds this expected KPI failure reason to every run.

The runner also treats an `openpilot_state.engaged: false` event after `run_state: MEASURE` as `valid/fail: disengagement`. The frozen formal event logs contain no such measurement-period disengagements.

Generated reports now aggregate valid failure reasons per delay condition. Frozen summaries retain the classifier reasons produced at their original run time; newly collected runs include the later KPI and disengagement reasons where applicable.

A clean post-driver smoke run on 2026-08-29 verified the complete current contract at 0 ms: driver 616.56 in the manifest, `camera_timestamps_valid: true`, zero drops, and `valid/fail` with `lane_departure` plus `lateral_error_threshold`. Its lateral RMSE was 0.658 m; it is a diagnostic confirmation, not an additional formal replicate.

The same day, a frame-2500 camera/telemetry alignment capture showed a visible upcoming left curve in the 40-degree road image before the current reference segment changed from straight to +0.008658 1/m at frame 2600. Model/control target curvature at the capture was only about +3.5e-06 1/m with -0.978 m lateral error. This reinforces the camera/model domain-gap hypothesis and is kept separate from formal results.

The instrumentation now records the model-predicted path horizon/end geometry, and only records its 20 m offset/heading if the path really reaches 20 m. The first run exposed an approximately 4.3 m path horizon, so clamped interpolation is explicitly avoided. This isolates a perception-path failure from a downstream curvature/planner failure without introducing a simulator-only steering controller. A fresh diagnostic run is the next verification step.

The next diagnostic also records `modelV2` validity, consumed camera frame age/drop percentage, execution time, and predicted terminal speed. These fields distinguish a stale/invalid inference stream from a valid but simulator-domain-mismatched prediction.

The first inference-health attempt exposed a bridge schema mistake (`modelV2.valid` does not exist); it is preserved as an invalid crash artifact. The instrumentation was corrected to record the owning SubMaster's `valid['modelV2']` status before retrying, rather than treating a message field as valid.

## Next

1. Join model path geometry to the fixed-baseline curve segment; do not tune simulator-only controllers as an openpilot claim.
2. Add repeatable frame/ground-truth alignment fixtures before changing camera preprocessing or calibration.
3. Package sample results, reproducibility commands, limitations, and CI evidence for the portfolio release.
