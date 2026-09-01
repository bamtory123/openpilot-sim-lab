# v0.1 qualification report (draft)

## Current framework verdict

`not_qualified_yet`

The historical baseline audit is approved, but the required current-host compatibility confirmation is not yet confirmed. This is a framework-release status, separate from the SUT driving outcome.

## Historical baseline

The frozen 0 ms formal reference has three complete, provenance-consistent run bundles. The checked run IDs and SHA-256 digests are in [historical-audit.json](../baselines/md_default_loop_lane0_v1/historical-audit.json). All three historical runs are `valid/fail: lane_departure`; this remains a known pretrained-SUT functional failure, not a SUT pass claim.

## Current-host confirmation attempt

On 2026-09-01, two consecutive 0 ms runs used the documented scenario and host-probe wrapper. Both wrappers exited zero without a WSL boot-ID change. Both runs recorded engagement, valid camera timestamps, 489 published camera frames, and zero dropped frames. Both nevertheless terminated at 24.44 s with lane departure, so formal telemetry and camera coverage were 0.4075, below the 0.99 requirement. Their runner verdict is therefore `invalid/not_evaluated` for coverage and insufficient active time, not an infrastructure crash.

The local evidence root is `outputs/v0.1-current-host-confirmation-20260901`. It is intentionally not committed as release data.

## Open item

The current contract requires a non-`invalid` host confirmation while also saying the known SUT lane departure does not block confirmation. On this formal scenario, the departure necessarily creates a coverage invalid. The policy needs a separate, explicitly scoped infrastructure-confirmation verdict before the two-run confirmation can be completed. It must not alter the frozen baseline or relabel the SUT outcome.

## Remaining release evidence

- Resolve the scoped current-host confirmation policy and collect its two-run evidence.
- Generate the baseline-relative regression-review artifact.
- Complete requirement-to-artifact traceability and the release package checklist.

See [limitations](limitations.md) for the SIL, domain-gap, synthetic-CAN, and real-vehicle boundaries.
