# v0.1 qualification report (draft)

## Current framework verdict

`not_qualified_yet`

The historical baseline audit and the required current-host compatibility confirmation are approved. The release remains unqualified until regression-review and remaining release-traceability artifacts are complete. This is a framework-release status, separate from the SUT driving outcome.

## Historical baseline

The frozen 0 ms formal reference has three complete, provenance-consistent run bundles. The checked run IDs and SHA-256 digests are in [historical-audit.json](../baselines/md_default_loop_lane0_v1/historical-audit.json). All three historical runs are `valid/fail: lane_departure`; this remains a known pretrained-SUT functional failure, not a SUT pass claim.

## Current-host confirmation

The initial two formal-scenario attempts were retained as `invalid/not_evaluated`: both had normal wrapper/WSL/transport behavior but the known lane departure at 24.44 s prevented their 55-second formal coverage requirement. They established that the formal-driving contract cannot also serve as a host-only check.

The resolved, separately versioned 200-frame probe then completed two consecutive `valid/pass` runs on 2026-09-01. Each recorded 9.99 s active time, 1.0 telemetry/camera coverage, 200 published camera frames, zero drops, valid timestamps, engagement, zero wrapper exit code and no WSL boot-ID change. Its local evidence root is `outputs/v0.1-host-confirmation-probe-20260901`; it is intentionally not committed as release data and is not a driving-performance result.

## Open item

The separate versioned nominal-10-second/200-frame `md_default_loop_lane0_host_confirmation_v1` probe retains the SUT, map, seed and 0 ms transport path but limits its verdict to engagement, transport and artifact integrity. It does not alter the frozen baseline or relabel the SUT outcome.

## Remaining release evidence

- The independent same-provenance 0 ms candidate comparison is complete but Phase 1 hard-gate failed: all three candidate runs were `invalid/not_evaluated` for coverage after known lane departure. Its scenario hash matches the frozen baseline; the local candidate root is `outputs/v0.1-current-host-confirmation-20260901`. This is an honest non-qualification result, not an infrastructure-crash conclusion.
- Define and approve the next baseline/candidate policy only if a future release needs a driving-performance comparison under the current active-time contract. Do not relabel the three invalid candidates as a passing or review-only result.
- Complete requirement-to-artifact traceability and the release package checklist.

See [limitations](limitations.md) for the SIL, domain-gap, synthetic-CAN, and real-vehicle boundaries.
