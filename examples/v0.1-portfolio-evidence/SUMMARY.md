# v0.1 public evidence summary

## Qualification boundary

The final v0.1 pretrained-driving disposition is `not_qualified_yet`. This bundle demonstrates validation-framework evidence, not successful pretrained OpenPilot driving.

## Selected evidence

- **Formal model-driven matrix:** representative `valid/fail` with `lane_departure`. All retained formal results are lane-departure failures; delay-group median lateral RMSE: 0 ms: 0.663898 m | 50 ms: 0.665897 m | 100 ms: 0.663629 m | 150 ms: 0.675149 m.
- **Baseline audit:** `approved` `md-default-loop-v1-approved` with 3 retained runs.
- **Current candidate review:** Phase 1 `hard_gate_fail`. KPI deltas are `diagnostic_only_after_phase_1_failure`.
- **Host confirmation:** 2 `valid/pass` 200-frame compatibility probes. Scope: `compatibility_only_not_driving_performance`.

## Evidence integrity

`evidence.json` records the full local source paths and SHA-256 digests. This public bundle excludes raw telemetry, camera data, frames, and process logs. Regenerate with `uv run python scripts/build_v01_public_evidence.py` and verify retained local sources with `uv run python scripts/verify_v01_public_evidence.py`.
