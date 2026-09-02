# Portfolio snapshot

This document is the submission entry point for the current repository commit. It is a portfolio snapshot, not a new GitHub release, tag, or pretrained-driving qualification.

## What the snapshot demonstrates

- A deterministic MetaDrive SIL validation framework around OpenPilot: provenance preflight, reference-lane telemetry, non-blocking camera transport delay, validity/outcome separation, reports, and recovery.
- Honest retention of the fixed model-driven baseline as `valid/fail: lane_departure`, and of an independent current candidate set as a Phase 1 coverage hard-gate failure.
- Bounded GPU/WSL compatibility evidence that preserves runtime provenance, normal returned failures, host interruption recovery, and Windows-event correlation boundaries.

## What it does not demonstrate

- Successful pretrained OpenPilot driving, real-road performance, HIL, real CAN actuation, obstacle avoidance, or CARLA closed-loop qualification.
- A root cause or long-duration clearance for the CUDA-backed bridge interruption boundary.
- General driving performance from the separately scoped simulator-specialist experiments.

## Reviewer path

1. Read the [portfolio summary](portfolio-summary.md) and [qualification report](qualification-report.md). The v0.1 pretrained-driving disposition is final: `not_qualified_yet`.
2. Start with the [public v0.1 evidence summary](../examples/v0.1-portfolio-evidence/SUMMARY.md), then inspect the [public v0.1 evidence bundle](../examples/v0.1-portfolio-evidence/README.md). Its source hashes bind the small public extract to retained local evidence without publishing raw frames, telemetry, or process logs.
3. Reproduce the bounded host/transport path with the [reproducibility package](reproducibility.md). Its `valid/pass` result is compatibility evidence, not a driving-performance result.
4. Review [evaluation boundaries](evaluation-boundary.md), [host stability](host-stability.md), and the [release checklist](release-checklist.md) before interpreting any simulator-specialist or host result.

## Submission rule

Use the Git commit containing this file as the snapshot identifier. Do not create a new release tag while the qualification state remains `not_qualified_yet`; the earlier historical tags are archived harness snapshots only and do not override this disposition.

Before submission, run the snapshot-only verifier from a clean sim-lab checkout:

```bash
scripts/verify_portfolio_snapshot.sh
```

For the complete local readiness check, include the freshly retained bounded artifacts explicitly. This validates their stored contracts without changing the v0.1 qualification disposition:

```bash
uv run python scripts/verify_portfolio_readiness.py \
  --repro-root outputs/reproducibility-package-20260903-portfolio \
  --host-stack outputs/host-stack-20260903-portfolio/host-stack.json \
  --carla-result outputs/carla-smoke/20260902T103857Z/result.json
```
