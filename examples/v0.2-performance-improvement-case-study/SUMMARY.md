# SIL performance-improvement case study

## Claim boundary

This bundle demonstrates a repeatable SIL improvement loop. The pretrained calibration result is a retained negative interface-calibration result; the positive cases are simulator-specialist only. Neither establishes real-road performance or changes v0.1 qualification.

## Pretrained actuator calibration

| Step | Result |
|---|---:|
| Tuning candidates | 8: `valid/fail`; 4/2/1: `invalid/not_evaluated` from coverage loss |
| Selected ratio | 8.0 (the unchanged baseline) |
| Calibration conclusion | `retain_negative_result_no_changed_candidate` — no changed candidate was evaluated as an improvement |

## Case 1 — targeted gamma/curve data

| Step | Result |
|---|---:|
| Fixed gamma-0.8 baseline | `valid/fail`, 1.34232 m lateral RMSE |
| Targeted-data candidate | 3 × `valid/pass`, mean 0.28765 m |
| Fault evidence | 0/50/100/150 ms: 3 × `valid/pass` per delay |

## Case 2 — tight-loop DAgger data

| Step | Result |
|---|---:|
| Fixed 45 m baseline | `valid/fail`, 0.51288 m lateral RMSE |
| 45 m candidate | 3 × `valid/pass`, mean 0.41224 m |
| 52 m held-out geometry | 3 × `valid/pass`, mean 0.49060 m |

The source SHA-256 values in `evidence.json` bind these public aggregate values to retained local summaries. The bundle excludes local paths, raw frames, telemetry, process logs, and model artifacts.
