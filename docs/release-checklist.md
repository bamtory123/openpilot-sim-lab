# Portfolio release checklist

Target tag: `v0.1.0-portfolio`.

| Requirement | Evidence | Status |
|---|---|---|
| Preserved upstream work / isolated instrumentation | `openpilot` branch `project/sim-instrumentation`; sim-lab orchestration stays in this repository | complete |
| Fixed scenario and manifest provenance | `md_default_loop_lane0_v1`, `manifest.json`, `configs/compatibility.yaml` | complete |
| Reference-lane ground truth | 100 Hz `telemetry.csv` contract and instrumentation summary | complete |
| Non-blocking delay path | camera queue, timestamp/drop fields, camera transport audit | complete |
| Formal repeatability matrix | 12 formal runs, 0/50/100/150 ms × 3; warm-up excluded | complete |
| Result distinction | report shows valid runs, valid failures, and invalid runs separately | complete |
| Unit tests and CI | local test suite; GitHub CI required to be green at release commit | pending release commit |
| Sample/reproduction material | `examples/v0.2-formal-delay-matrix`, `docs/reproducibility.md` | complete |
| Scope limitations | README, instrumentation, progress, and CARLA smoke documents | complete |

## Release statement

The release may state that the deterministic MetaDrive harness, delay injector, telemetry, KPI report, and repeatability data collection are complete. It must state that the current model-driven baseline produces reproducible `valid/fail` lane departures. It must not claim successful closed-loop openpilot driving, real-vehicle validation, HIL, trained-model improvement, or CARLA closed-loop validation.

## Publish gate

Before creating the tag, run `uv run pytest -q`, confirm a clean worktree, wait for CI success on the release commit, and verify the sample JSON parses. The tag should point only to that green commit.
