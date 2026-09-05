# 3.5 m/s targeted-DAgger boundary case

## Decision

The targeted candidate was rejected after one held-out diagnostic. It departed at 49.48 m, earlier than the v0.6 repeatable 87.86–91.42 m boundary, and its observed partial-run lateral RMSE increased from 0.62414 to 0.98317 m.

| Stage | Result |
|---|---|
| v0.6 boundary | 3 × `invalid/not_evaluated`; common-curve departure |
| Failure localization | `repeatable_common_curve_departure`; capture frames 4960–5600 |
| Targeted data | 33 train + 33 validation samples |
| v0.7 held-out diagnostic | `invalid/not_evaluated`; lane departure, no collision/drop/host restart |
| Gate action | `reject_candidate_stop_before_repeat_and_delay_matrix` |

Both RMSE values are incomplete-run diagnostics and are performance-ineligible. No repeated candidate evaluation or delay matrix was run. This simulator-only negative case demonstrates rejection by the SIL improvement gate; it is not road-performance evidence.

## Anchored follow-up

An offline trust-region gate selected the minimum blend alpha `0.5` that improved targeted validation by 41.77% while limiting original-validation RMSE increase to 1.08%. Three fresh-seed closed-loop repeats produced `2 pass / 1 fail`; lateral RMSE was 0.49987, 0.53219, 0.70821 m. The failed repeat departed at 49.85 m despite unchanged source and host contracts. The candidate is therefore rejected for insufficient repeatability margin, and no regression or delay matrix follows.
