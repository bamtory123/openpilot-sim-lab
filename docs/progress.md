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

## Next

1. Inspect camera/model domain gap with the formal baseline fixed; do not tune simulator-only controllers as an openpilot claim.
2. Add repeatable frame/ground-truth alignment fixtures before changing camera preprocessing or calibration.
3. Package sample results, reproducibility commands, limitations, and CI evidence for the portfolio release.
