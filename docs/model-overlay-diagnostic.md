# Source-aligned model overlay diagnostic

## Purpose and boundary

This diagnostic projects the pretrained OpenPilot `modelV2` path and lane-line geometry onto the exact MetaDrive road-camera frame consumed by the model. It is analysis-only: the projection does not feed the planner, controller, or simulator. Green lines are model lane hypotheses, red is the model path, and the label reports the inner-lane probabilities and path horizon.

The join key is the camera transport `source_frame_id`, not a simulator or bridge loop counter. `SimulatedSensors` saves the immutable pre-NV12 RGB buffer for explicitly requested source IDs; the bridge saves geometry only when `modelV2.frameId` reaches the same ID. The runner renders an overlay only for an exact match and records the join in `model_overlay_alignment.json`. This replaced an initial diagnostic that incorrectly treated independent process counters as a shared clock.

## 2026-09-05 bounded results

The fixed single-camera baseline produced exact joins at source IDs 30, 45, and 60. The overlays show populated lane geometry near visible markings, but the inner-lane probabilities remain roughly 1% and the path collapses to about 1.5–3.4 m. This supports low semantic confidence rather than an empty message or stale-frame explanation.

Two isolated candidates were rejected:

| Candidate | Observed result | Decision |
|---|---|---|
| map lane width 4.5 → 3.7 m | lower lane confidence, shorter active run, still invalid after early departure | reject; retain frozen 4.5 m default |
| narrow-only → narrow+wide camera | modeld confirmed `use_extra_client: True`; early horizon increased, but right-lane confidence fell, steering-command RMS rose to 106.96°, and the run became invalid after 3.29 s active time | reject as a driving candidate; retain as input-contract diagnostic |

All runs above were dirty-tree diagnostics and are not formal evidence. Neither candidate changes the frozen v0.1 scenario. The result narrows the next perception experiment to rendered road/marking appearance with source-aligned overlays; it does not justify actuator tuning or a pretrained-driving claim.

The next single-variable experiment replaced MetaDrive's approximately 2 m line / 2 m gap semantic pattern with an opt-in `mutcd_highway_v1` profile using 3.048 m line segments and 9.144 m gaps. These dimensions follow the [FHWA MUTCD 11th Edition](https://mutcd.fhwa.dot.gov/pdfs/11th_Edition/mutcd11theditionhl.pdf) broken-line guidance. Exact source-ID overlays confirmed that the rendered spacing changed.

Mean left/right lane confidence changed from `0.00953/0.01467` to `0.01111/0.01597`, but mean path horizon fell from `3.39 m` to `3.30 m`, measured median horizon fell from `2.89 m` to `2.73 m`, and lateral RMSE increased from `0.850 m` to `0.869 m`. The run remained `invalid/not_evaluated` after early departure and insufficient coverage. The marking profile is therefore retained only as appearance-sensitivity evidence, not a driving candidate.

An asphalt-only contrast diagnostic then set `road_texture_gain: 0.75` while leaving lane textures, camera output, map geometry, and image gamma unchanged. The source-aligned frame-30 lower-centre luma changed from `96.30` to `81.53`, confirming that the intended road region—not the full image—was darkened. Mean left/right lane confidence fell to `0.00922/0.01122`, mean path horizon fell to `3.26 m`, and lateral RMSE remained effectively unchanged at `0.852 m`. The run again ended `invalid/not_evaluated` after 24.39 s measured active time. Darker asphalt is rejected as a driving candidate.

A subsequent source-hashed fixed-band structure audit found that MetaDrive has only 0.18× the real-replay upper-band gradient energy, while its lower-band gradient energy is 3.49× and its horizontal edge density is over two orders of magnitude higher. Because these are unmatched scenes and non-semantic bands, the comparison selects no rendering candidate. It instead closes the sequence of ungrounded single-pixel adjustments: the remaining gap is structural and requires matched-scene evidence or simulator-specialist training.

## Reproduction

```bash
OPENPILOT_ROOT=/path/to/openpilot \
PYTHONPATH=src /path/to/openpilot/.venv/bin/python -m simlab.runner run \
  --scenario configs/scenarios/md_default_loop_lane0_frame_alignment_diagnostic_v1.yaml \
  --outputs outputs/model-overlay-single

OPENPILOT_ROOT=/path/to/openpilot \
PYTHONPATH=src /path/to/openpilot/.venv/bin/python -m simlab.runner run \
  --scenario configs/scenarios/md_default_loop_lane0_dual_camera_diagnostic_v1.yaml \
  --outputs outputs/model-overlay-dual
```

Local outputs include the raw diagnostic PNGs and JSON geometry. They are intentionally excluded from the public evidence bundle.
