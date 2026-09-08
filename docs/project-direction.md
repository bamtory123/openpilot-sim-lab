# Project direction review — 2026-09-08

## Decision

The portfolio's primary claim remains **ADAS SIL validation engineering**, not successful OpenPilot driving or model development. That direction is technically sound and now better supported than a continued attempt to make one simulator-specialist policy pass more cases.

The v0.1 qualification is frozen as `not_qualified_yet`. The v0.2 improvement case study is also feature-complete: it contains a negative pretrained actuator-calibration result, two simulator-only positive controls, a rejected targeted-data regression, and an anchored candidate that improved to two passes but failed the required 3/3 repeatability gate. Further alpha, dataset-window, renderer, or CARLA tuning is out of the submission scope unless a new version and fresh evaluation policy are approved first.

## Maturity assessment

| Area | Current maturity | Evidence | Remaining boundary |
|---|---|---|---|
| Configuration and provenance | High for a portfolio SIL | Pinned OpenPilot base, scenario/source hashes, dirty-state policy, runtime/GPU/WSL manifest | Not a controlled lab image or containerized GPU runtime |
| Lifecycle and recovery | High | Explicit state machine, watchdog, durable attempt, interrupted-run recovery | Long CUDA/WSL stability root cause remains open |
| Camera fault injection | High for the declared fault | One non-blocking queue path for 0/50/100/150 ms, actual delay/drop/queue telemetry and unit tests | Only camera transport delay/drop; no broader sensor/compute fault catalogue |
| Ground truth and verdicts | High for lane following | Fixed reference-lane telemetry and separate `validity`/`outcome` | Project-defined thresholds only; no OEM safety acceptance criteria |
| Regression and evidence | High | Frozen baseline audit, phase gates, source-bound public evidence, CI drift checks | Public bundles cannot independently recreate ignored raw runs/models |
| Execution repeatability | Medium | Repeated contracts and source-hashed divergence localization | Fixed seed is not bitwise or trajectory determinism; control/render scheduling remains unisolated |
| SUT/plant integration | Medium-low | OpenPilot camera/sensor/control bridge and command-versus-applied telemetry | Synthetic CAN/Panda and simplified MetaDrive plant; no ECU/EPS/HIL validation |
| Scenario and behavior coverage | Low by design | Fixed loop, serpentine, bounded traffic/obstacle probes | No meaningful traffic interaction, longitudinal policy, weather, ODD, or coverage model |
| Performance-improvement loop | Medium and honestly bounded | Positive specialist controls plus full-update and anchored rejection gates | Specialist artifacts do not improve pretrained OpenPilot or establish road generalization |
| Portfolio communication | High after curation | Five-minute guide, compact evidence, explicit non-claims | Detailed experimental archive remains large and should stay a secondary path |

## What the project now proves

- A candidate ADAS stack can be run under a frozen simulator contract with traceable source and runtime provenance.
- Camera transport faults can be injected without blocking capture, and actual delivery can be measured independently of configured delay.
- Data/infrastructure validity can be kept separate from a functional pass/fail verdict.
- Positive, negative, invalid, interrupted, and regressive candidates can all be retained without changing the acceptance rule after seeing results.
- The same framework can stop a superficially improved candidate when its repeated closed-loop margin is insufficient.

It does not prove deterministic simulator trajectories, production-grade SIL fidelity, pretrained OpenPilot performance in MetaDrive, real CAN/EPS behavior, HIL coverage, or road safety.

## Submission direction

For the current portfolio snapshot, stop adding experiments. Lead with four artifacts:

1. v0.1 non-blocking fault and verdict pipeline.
2. Frozen formal matrix plus honest `not_qualified_yet` disposition.
3. v0.2 source-bound improvement loop, including a positive control and rejected regression.
4. Architecture/patch boundary showing what belongs to this project versus OpenPilot and MetaDrive.

CARLA, real-camera replay, renderer probes, traffic probes, and the full specialist history remain optional deep dives. They support engineering judgment but should not occupy the first five minutes.

## Recommended next version

If development continues after the portfolio snapshot, v0.3 should be **execution-repeatability and interface-fidelity**, in this order:

1. Define a synchronous simulator-camera-inference-control tick contract and record capture-to-control age, control hold duration, and state checksums.
2. Repeat one fixed scenario enough times to separate bitwise input variation, scheduling variation, and nonlinear closed-loop amplification. Do not call the environment deterministic until that test passes.
3. Add a versioned actuator/vehicle-response model with delay, rate, saturation, and calibration provenance; validate command-to-applied response before adding scenarios.
4. Only then add a small requirements-driven scenario set and coverage dimensions such as curvature, speed, illumination, and lead-vehicle interaction.
5. Treat HIL, real CAN, EPS, or matched-scene perception as separate projects requiring hardware or permission-cleared data.

The next release should not be another specialist model revision. Its success criterion should be a measurable reduction in cross-run input/control/state divergence under an unchanged scenario, with no weakened functional gate.
