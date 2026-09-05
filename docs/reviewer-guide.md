# Portfolio reviewer guide (5 minutes)

## One-sentence project

I built a reproducible ADAS SIL validation framework around OpenPilot: MetaDrive scenario orchestration, provenance, non-blocking camera-delay faults, ground-truth/KPI collection, verdicts, and qualification evidence.

OpenPilot is the **System Under Test (SUT)**; MetaDrive is the **SIL simulator**; this repository contains the validation framework rather than an autonomous-driving model.

## Read this first

| Time | Review | What it demonstrates |
|---:|---|---|
| 1 min | This page and the [portfolio summary](portfolio-summary.md) | Scope, contribution, and non-claims |
| 2 min | [Public v0.1 evidence summary](../examples/v0.1-portfolio-evidence/SUMMARY.md) | Formal matrix, baseline audit, candidate hard gate, host confirmation |
| 1 min | [v0.2 improvement case study](performance-improvement-case-study.md) | Separate pretrained calibration, specialist positive controls, and a source-bound rejected regression |
| 1 min | [Real-camera replay reference](../examples/v0.2-real-camera-model-replay/README.md) | Why pretrained perception and MetaDrive closed loop are evaluated on separate evidence paths |
| 1 min | [Architecture](architecture.md) and [OpenPilot patch boundary](openpilot-patch.md) | What was integrated and what was minimally instrumented |
| 1 min | [Qualification report](qualification-report.md) and [limitations](limitations.md) | Why the result is `not_qualified_yet`, without hiding failure evidence |

## What I implemented

```text
OpenPilot (SUT) ← delayed camera / simulated sensors → MetaDrive
       ↑                                               ↓
       └──── openpilot-sim-lab: scenario → telemetry → KPI/verdict/report
```

| Area | Implemented contribution | Evidence |
|---|---|---|
| Reproducibility | Pinned source/runtime provenance, dirty policy, scenario hash, preflight and patch reapplication | [architecture](architecture.md), [patch guide](openpilot-patch.md) |
| Ground truth | Fixed-reference-lane lateral/heading/progress telemetry; command and applied control recorded separately | [requirements](requirements.md), [test plan](test-plan.md) |
| Fault injection | One non-blocking queue path for 0/50/100/150 ms; capture/publish timing and drops retained | [public evidence](../examples/v0.1-portfolio-evidence/SUMMARY.md) |
| Verdicts | Data/infrastructure validity separated from SUT functional outcome; interruption recovery retained | [release process](release-process.md), [host stability](host-stability.md) |
| Regression evidence | Frozen baseline audit, phased hard/provenance gates, public-safe evidence and CI snapshot verification | [traceability](traceability.md), [portfolio snapshot](portfolio-snapshot.md) |
| Improvement loop | Bounded actuator-interface gate plus source-bound specialist positive and rejected-regression cases | [v0.2 case study](performance-improvement-case-study.md), [3.5 m/s rejection](../examples/v0.2-specialist-speed-boundary/SUMMARY.md) |
| Input-domain isolation | Official 60-frame OpenPilot road-camera replay; functional and host-timing verdicts separated | [real-camera replay](real-camera-model-replay.md) |
| Model-input diagnosis | Exact camera source-frame/model-frame overlay; rejected lane-width/dual-camera/marking/contrast candidates; source-hashed unmatched-scene structure audit prevents another unsupported pixel tweak | [source-aligned overlay](model-overlay-diagnostic.md), [camera-domain gap](camera-domain-gap.md) |

## Result scorecard

| Question | Result | Correct interpretation |
|---|---|---|
| Did the validation framework collect and classify the formal delay study? | Yes | The retained 12-run v0.1 matrix has complete timing/data evidence and repeatable `valid/fail: lane_departure` results. |
| Does the current host support the bounded integration path? | Yes, bounded | Two retained 200-frame probes passed their engagement/transport/artifact contract. This is not long-run clearance. |
| Did pretrained OpenPilot pass this MetaDrive driving contract? | No | The independent candidate set hit a Phase 1 coverage hard gate after known early departure. v0.1 remains `not_qualified_yet`. |
| Does the same pretrained model produce healthy outputs on a fixed real-camera replay? | Functionally yes | 60/60 model outputs, zero reported frame age/drop, high lane confidence, and long path horizon; this is offline input evidence, not a driving pass. |
| Is this real-road, HIL, CAN-actuation, or CARLA closed-loop validation? | No | Those are explicitly outside the v0.1 claim boundary. |

The negative SUT result is deliberate portfolio evidence: the framework preserves it as a valid functional failure or invalid coverage result instead of converting it into a passing claim.

## My code versus upstream components

| Component | Ownership / role |
|---|---|
| OpenPilot | Upstream SUT; only minimal telemetry and transport instrumentation is applied through documented patches. |
| MetaDrive | Upstream SIL simulator. |
| `openpilot-sim-lab` | This project's orchestration, scenarios, provenance, fault implementation, telemetry/KPI/verdict/report pipeline, tests, and evidence packaging. |
| CARLA material | Separate bounded v0.2 adapter-pilot/smoke evidence; never used to qualify v0.1. |

## Reproduce the review claim

Public-only verification needs no raw local runs and does not create a release:

```bash
scripts/verify_portfolio_snapshot.sh
```

For a bounded WSL integration check, follow the [reproducibility package](reproducibility.md). For source reconstruction, apply the pinned [OpenPilot patch bundles](../patches/README.md). Both paths preserve the boundary that a successful short probe is not a pretrained-driving pass.

## Good interview discussion points

- Why a delay injector must not block the camera producer, and why 0 ms follows the same queue path.
- Why fixed-reference-lane ground truth prevents a vehicle in an adjacent lane from appearing to have low lateral error.
- Why `valid/fail` and `invalid/not_evaluated` need separate evidence and retry handling.
- Why a framework can be technically complete while its SUT qualification is honestly `not_qualified_yet`.
- How provenance, immutable retained artifacts, and CI snapshot checks make a repeatability study reviewable.

For detailed experiments, use the [evaluation boundary](evaluation-boundary.md). It is intentionally not the first-stop document because it contains the full specialist and negative-result record.
