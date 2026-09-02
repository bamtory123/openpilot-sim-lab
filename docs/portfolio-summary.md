# Portfolio summary

## What was built

This project treats OpenPilot as a System Under Test and MetaDrive as a deterministic SIL environment. The implemented contribution is the validation framework around the SUT:

- scenario/configuration validation, provenance manifest, and OpenPilot compatibility preflight
- fixed-reference-lane ground truth, separate telemetry/camera/event artifacts, and validity/outcome classification
- non-blocking camera transport-delay injection with actual delay, queue-depth, and drop evidence
- frozen baseline audit with complete-file SHA-256 evidence
- phased regression review: data/new-event hard gates, provenance compatibility, and KPI delta review
- bounded and full-run WSL/GPU host-stability evidence with boot-ID and Windows-event correlation

## Evidence retained

The frozen v0.1 historical delay matrix records 0/50/100/150 ms conditions with an excluded warm-up and three interleaved formal runs per condition. The host-confirmation probe establishes the current host's engagement, transport, and artifact path separately from driving performance. Requirements, test cases, artifacts, decisions, and qualification disposition are cross-linked in the project documentation.

## Deliberate non-claims

The pretrained OpenPilot model-driven candidate set cannot satisfy the current 55-second/1,200-frame formal coverage contract because its known lane departure occurs earlier. The resulting candidate comparison is a Phase 1 hard-gate failure. Therefore v0.1 is closed as `not_qualified_yet` for pretrained-driving qualification.

This project does not claim successful OpenPilot driving, real-road validation, HIL, vehicle-CAN actuation validation, CARLA closed-loop qualification, obstacle avoidance, or statistical/general driving generalization. Simulator-specialist experiments are separately scoped and never replace the pretrained OpenPilot baseline.

Start with the [public v0.1 evidence bundle](../examples/v0.1-portfolio-evidence/README.md): it is the small, public-safe entry point and preserves the distinction between the formal lane-departure failure and host compatibility probes. The retained local artifacts and final disposition are documented in the [qualification report](qualification-report.md), [decision log](decisions.md), and [limitations](limitations.md).
