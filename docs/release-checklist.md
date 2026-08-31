# Portfolio release checklist

Released tags: `v0.1.0-portfolio`, `v0.1.1-portfolio`, and `v0.1.2-portfolio`.

The latest v0.1 release is `v0.1.2-portfolio` at `d27c0920af16f6d54928ec382d8d057674caa50a`. It adds measurement-period disengagement classification while retaining the frozen formal matrix's reproducible `valid/fail` baseline status.

| Requirement | Evidence | Status |
|---|---|---|
| Preserved upstream work / isolated instrumentation | `openpilot` branch `project/sim-instrumentation`; sim-lab orchestration stays in this repository | complete |
| Fixed scenario and manifest provenance | `md_default_loop_lane0_v1`, `manifest.json`, `configs/compatibility.yaml` | complete |
| Reference-lane ground truth | 100 Hz `telemetry.csv` contract and instrumentation summary | complete |
| Non-blocking delay path | camera queue, timestamp/drop fields, camera transport audit | complete |
| Formal repeatability matrix | 12 formal runs, 0/50/100/150 ms × 3; warm-up excluded | complete |
| Result distinction | report shows valid runs, valid failures, and invalid runs separately | complete |
| Unit tests and CI | local test suite; GitHub CI green for the release commit and current documentation commit | complete |
| Sample/reproduction material | `examples/v0.2-formal-delay-matrix`, `docs/reproducibility.md` | complete |
| Scope limitations | README, instrumentation, progress, and CARLA smoke documents | complete |

## Release statement

The release may state that the deterministic MetaDrive harness, delay injector, telemetry, KPI report, and repeatability data collection are complete. It must state that the current model-driven baseline produces reproducible `valid/fail` lane departures. It must not claim successful closed-loop openpilot driving, real-vehicle validation, HIL, trained-model improvement, or CARLA closed-loop validation.

## Future publish gate

Before creating any additional tag, run `uv run pytest -q`, confirm a clean worktree, wait for CI success on the release commit, and verify the sample JSON parses. The tag should point only to that green commit. The v0.2 experimental branch additionally requires a documented disposition of the Windows/WSL CUDA stability boundary; it must not promote rendered-lead smoke results to a perception, avoidance, or real-driving claim.

## Post-v0.1 experimental extensions

The opt-in simulator-specialist and `openpilot_serpentine_v1` evidence added after the v0.1 tag remains on `main` as v0.2 experimental material. It must not move `v0.1.0-portfolio` or change the v0.1 release statement. Any later tag must separately identify its generated local artifact, exact scenario, output sample, CI revision, and simulator-only limitations.

## v0.2 host-stability disposition

| Item | Evidence | Status |
|---|---|---|
| Interrupted-run integrity | manifest UTC timestamp and WSL boot ID; `recover` preserves both in `host_recovery` | complete |
| Windows-side correlation | `collect_windows_wsl_events.ps1` writes a bounded System-log JSON beside an artifact | complete |
| Bounded component check | CUDA soak, offscreen renderer, preflight, and boot-ID comparison in `check_host_stack.sh` | complete |
| Long CUDA-backed bridge stability | two 59.99 s/1,200-frame foreground probes retained boot ID with no selected Windows event; no independent root-cause isolation or long-run clearance | open |

The completed rows make infrastructure interruptions auditable and non-misleading. They do not clear the last row or authorize a long formal matrix solely to obtain more samples.
