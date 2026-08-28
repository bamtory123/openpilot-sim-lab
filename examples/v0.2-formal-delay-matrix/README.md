# v0.2 formal delay-matrix sample

This small package is a release-friendly subset of the local formal run at `outputs/v0.2-formal-delay-matrix-20260828`. It contains one representative 0 ms `summary.json` and the aggregate table below; it intentionally excludes full telemetry, camera frames, and raw process logs.

| Target delay (ms) | Formal runs | Valid / fail / invalid | Median lateral RMSE (m) |
|---:|---:|---:|---:|
| 0 | 3 | 3 / 3 / 0 | 0.663898 |
| 50 | 3 | 3 / 3 / 0 | 0.665897 |
| 100 | 3 | 3 / 3 / 0 | 0.663629 |
| 150 | 3 | 3 / 3 / 0 | 0.675149 |

Every formal run was a measured `valid/fail` due to lane departure. This is a repeatability result for a model-driven simulator baseline, not evidence of passing automated driving performance.

The frozen run used `openpilot@a93db2186`, `openpilot-sim-lab@e07b9c7`, MetaDrive 0.4.2.3, Python 3.12.13, WSL kernel 6.18.33.2, and an RTX 4080. Reproduce the current project state with [the formal procedure](../../docs/reproducibility.md); the current runtime/commit will be recorded in each new manifest.
