# Simulator dataset collection

The dataset collector is an opt-in diagnostic, separate from the formal delay study. Each sample records a run-relative road-camera PNG plus its capture metadata and route/model labels in `dataset_manifest.jsonl`.

Run one fixed collection:

```bash
cd /home/hyunsung/src/openpilot-sim-lab
OPENPILOT_ROOT=/home/hyunsung/src/openpilot \
  /home/hyunsung/src/openpilot/.venv/bin/python3 -m simlab.runner run \
  --scenario configs/scenarios/md_default_loop_lane0_dataset_collection_v1.yaml \
  --outputs outputs/dataset-collection
```

Current labels are route-relative diagnostic targets: lateral/heading error, reference curvature, and model output state. They are not pixel-space lane labels and are therefore suitable for dataset audit and path-target experimentation, not for claiming production lane-detection training.

The first single-seed collection has 18 images and is a smoke set only. The first three-seed matrix (`20260827`, `20260828`, `20260829`) produced 54 images with 15 curved-segment samples; every run remains a valid driving-system failure and is retained as data provenance. This is still too small for training. A training dataset requires expanded coverage, a predeclared train/validation split, and a pixel or vehicle-frame path-label definition.

Run the declared matrix with `simlab.runner collect` instead of `run`:

```bash
$OPENPILOT_PYTHON -m simlab.runner collect \
  --scenario configs/scenarios/md_default_loop_lane0_dataset_collection_v1.yaml \
  --outputs outputs/dataset-collection-matrix
```

The verified split matrix contains 36 train and 18 validation samples; curved segments are split 10 and 5 respectively. These counts are provenance checks, not training-sufficiency claims.

The dataset audit reports only `0 … +0.008658 1/m` reference curvature for the initial matrix. It has no negative-curvature coverage, so it must not be used to train a general path model. The directional smoke run verified direction `1` produces `−0.008032 … 0 1/m` reference curvature with 370 negative-curve telemetry samples. The next collection matrix can therefore include both turn signs.

## Static-lead diagnostic subset

`md_serpentine_lane0_temporal_v06_gamma_tight_dagger_speed2_static_lead20_dataset_v1` is a separate, fixed 20 m stationary-lead smoke collection. Its 10 RGB samples carry the usual camera metadata plus analysis-only nearest-actor distance, closing speed, TTC, actor count, and collision state. The first run recorded all 10 as traffic-labeled, with a 4.52 m minimum sampled distance and 3.40 s minimum sampled positive TTC; two samples carried a collision state. The run itself is retained as `valid/fail: collision`.

`simlab.runner audit` reports `traffic_labeled_sample_count`, nearest-distance minimum, TTC minimum, and collision-labeled sample count for this subset. These labels are simulator ground truth for offline audit only: they must not be fed into the replay controller. The installed MetaDrive minimal asset package omits vehicle meshes, so this physics lead is not visible in the RGB frames; this subset is not lead-perception data or evidence for following, braking, or avoidance.

The three-seed matrix version uses seeds `20260831`, `20260901`, and held-out `20260902`. Its completed collection produced 30 labeled images with a 20/10 train/validation split; all three runs were `valid/fail: collision`. The audit found 30 traffic-labeled images, 13 collision-state images, 3.66 m minimum sampled distance, and 3.37 s minimum sampled positive TTC. This confirms repeatability of the fixed encounter and offline-label contract, not a visual-perception dataset.

## Visible static-obstacle proxy smoke

The minimal package does contain `box.bam`, so `lead_vehicle.visual_proxy: box` attaches a black rectangular visual proxy to the same non-rendered static physics lead. A first 20 m smoke captured the proxy in RGB at 2 and 8 s and wrote 10 traffic-labeled samples (three collision-state samples; 4.52 m minimum sampled distance; 3.40 s minimum sampled positive TTC). The run was `valid/fail` for lane departure, collision, and lateral-error KPI.

This establishes only an explicit synthetic **box-obstacle** camera/physics alignment path. It is not a vehicle, pedestrian, or traffic-participant representation; no detector, distance estimator, braking policy, or avoidance policy is trained or evaluated. The black box's rendering and geometry are fixed and intentionally unsuitable for a real-world or vehicle-perception claim.
