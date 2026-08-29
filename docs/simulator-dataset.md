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
