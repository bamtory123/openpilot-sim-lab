# Reproducing the formal MetaDrive matrix

## Bounded reproducibility package (recommended today)

This package is the fast, host-safe reproduction path. It runs the repository tests, dirty-aware preflight, one versioned 200-frame host probe, report generation, and an artifact verifier. It is **not** a formal driving-performance matrix.

```bash
cd /home/hyunsung/src/openpilot-sim-lab
export OPENPILOT_ROOT=/home/hyunsung/src/openpilot
export OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python"
scripts/run_reproducibility_package.sh outputs/reproducibility-package
```

Success requires `verification.json` with `status: pass`, one `summary.json` marked `valid/pass`, a frozen scenario snapshot/hash, 200 published camera frames, and zero drops. Preserve the complete output directory. A failure remains evidence; do not rerun in place or replace its artifacts.

## New PC / WSL bootstrap

On Ubuntu WSL with an NVIDIA-enabled WSL GPU runtime, install `git` and [uv](https://docs.astral.sh/uv/), clone this repository into a workspace directory, then run:

```bash
cd /path/to/openpilot-sim-lab
scripts/bootstrap_new_wsl.sh --install
export OPENPILOT_ROOT="$(cd .. && pwd)/openpilot"
export OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python"
scripts/run_reproducibility_package.sh outputs/reproducibility-package
```

The bootstrap fixes OpenPilot at `d7ee3435737d7e0bd88f14ffedd45999b6d2e957` and MetaDrive at `2716f55a9c7b928ce957a497a15c2c19840c08bc`, creates the OpenPilot environment, installs MetaDrive and sim-lab editable into that runtime, and syncs sim-lab test dependencies. Run `scripts/bootstrap_new_wsl.sh --check` before the package to verify those exact commits and the runtime import without changing state.

These commands run the fixed model-driven baseline, not a simulator-only controller diagnostic.

```bash
cd /home/hyunsung/src/openpilot-sim-lab
export OPENPILOT_ROOT=/home/hyunsung/src/openpilot
export OPENPILOT_PYTHON="$OPENPILOT_ROOT/.venv/bin/python"

$OPENPILOT_PYTHON -m simlab.runner preflight --allow-dirty \
  --scenario configs/scenarios/md_default_loop_lane0_v1.yaml
$OPENPILOT_PYTHON -m simlab.runner batch --allow-dirty \
  --scenario configs/scenarios/md_default_loop_lane0_v1.yaml \
  --outputs outputs/formal-delay-matrix
$OPENPILOT_PYTHON -m simlab.runner report --outputs outputs/formal-delay-matrix
```

The batch performs one excluded warm-up followed by three interleaved runs for each of 0, 50, 100, and 150 ms. It refuses dirty repositories by default. Each output directory records the actual commits, dirty state, Python/runtime details, scenario hash, command, and environment in `manifest.json`.

Coverage and infrastructure integrity take precedence over driving outcome: insufficient telemetry coverage, insufficient measured road-camera coverage, timestamp faults, frame loss, watchdog expiry, or host interruption produce `invalid/not_evaluated` even if a lane departure or collision was observed. Only a coverage-complete run can be classified as `valid/fail` for those driving events.

New summaries record `telemetry_coverage_ratio` and `road_camera_coverage_ratio` alongside the verdict, using only measurement-period rows.

Every scenario requires `validity.min_active_time_s`; the measured simulation-time span is enforced and recorded as `active_time_s`. This keeps short diagnostic smoke contracts explicit rather than allowing their camera-frame count to imply a longer active window.

## Acceptance checks

1. Exclude `outputs/formal-delay-matrix/warmup` from formal counts.
2. Confirm exactly three `summary.json` files for each target delay.
3. Preserve every result, including `invalid/not_evaluated` runs and retries.
4. Read `validity` separately from `outcome`: lane departure is `valid/fail`, while startup, logging, timestamp, overflow, and watchdog faults are invalid infrastructure data.
5. Use `camera.csv` actual timestamps and delays, never only the configured delay, when discussing the fault.

The current baseline is expected to produce repeatable lane-departure failures. Do not use this procedure to claim real-vehicle performance, HIL validation, or successful openpilot driving.

## Opt-in tight-loop specialist matrix

This separate procedure requires the local generated `models/v0.6-temporal-gamma-tight-dagger-ridge.npz` artifact; it does not modify the pretrained openpilot path or the formal model-driven matrix.

```bash
$OPENPILOT_PYTHON -m simlab.runner preflight --allow-dirty \
  --scenario configs/scenarios/md_tight_loop_lane0_temporal_v06_gamma_tight_dagger_speed2_heldout_v1.yaml
$OPENPILOT_PYTHON -m simlab.runner batch --allow-dirty \
  --scenario configs/scenarios/md_tight_loop_lane0_temporal_v06_gamma_tight_dagger_speed2_heldout_v1.yaml \
  --outputs outputs/tight-specialist-delay-matrix
$OPENPILOT_PYTHON -m simlab.runner report --outputs outputs/tight-specialist-delay-matrix
```

Apply the same acceptance checks above. The checked-in sample documents a fixed 45 m loop, seed, direction, default rendering, and 2.0 m/s target only. A missing local artifact is a preflight failure, not a reason to substitute ground truth or alter the scenario.

## Opt-in v0.2 serpentine matrix

`openpilot_serpentine_v1` is a versioned alternating-turn MetaDrive profile. It requires the same local tight-DAgger artifact and does not alter the v0.1 formal scenario.

```bash
$OPENPILOT_PYTHON -m simlab.runner preflight --allow-dirty \
  --scenario configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_heldout_v1.yaml
$OPENPILOT_PYTHON -m simlab.runner batch --allow-dirty \
  --scenario configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_heldout_v1.yaml \
  --outputs outputs/serpentine-specialist-delay-matrix
$OPENPILOT_PYTHON -m simlab.runner report --outputs outputs/serpentine-specialist-delay-matrix
```

This is v0.2 experimental evidence only. Do not combine it with the v0.1 default-loop release result or interpret it as arbitrary route/road validation.

## Opt-in v0.2 low-traffic probe

This is a single 0 ms fixed-seed lane-following probe, not an actor-interaction or avoidance test. It requires the locally recorded MetaDrive 0.4.2.3 traffic-config correction described in [openpilot-patch](openpilot-patch.md); its dirty dependency state is retained in the manifest.

```bash
cd /home/hyunsung/src/metadrive
git apply /home/hyunsung/src/openpilot-sim-lab/patches/metadrive-0.4.2.3-traffic-render-vehicle.patch
git apply /home/hyunsung/src/openpilot-sim-lab/patches/metadrive-0.4.2.3-road-marking-profile.patch
```

```bash
$OPENPILOT_PYTHON -m simlab.runner --allow-dirty run \
  --scenario configs/scenarios/md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_traffic03_heldout_v1.yaml \
  --outputs outputs/serpentine-low-traffic-probe
```

Confirm `traffic_vehicle_count_mean` and `traffic_vehicle_count_max` in `summary.json` before describing this as a traffic-present run. The actor count alone does not demonstrate detection, prediction, yielding, braking, or collision avoidance.

The tracked traffic scenario sets `validity.min_traffic_vehicle_count: 1`. If no measured telemetry row reaches that count, the runner returns `invalid/not_evaluated` with `traffic_actor_coverage`, even if lane-following KPIs would otherwise pass.

## Camera alignment diagnostic

```bash
$OPENPILOT_PYTHON -m simlab.runner run --allow-dirty \
  --scenario configs/scenarios/md_default_loop_lane0_frame_alignment_diagnostic_v1.yaml \
  --outputs outputs/frame-alignment-diagnostic
```

This opt-in diagnostic writes PNG captures and `camera_alignment.json` inside its individual run directory. It does not alter the formal scenario or its results.
