# Real-camera model replay reference

## Purpose

This track answers one narrow question: can the pinned pretrained OpenPilot model produce complete, meaningful outputs when fed OpenPilot's fixed real-camera CI route? It does not test control response because prerecorded frames cannot react to steering or acceleration.

The split follows the public tool boundaries. OpenPilot documents MetaDrive as a simulator bridge and uses it for full-stack integration tests, while MetaDrive explicitly prioritizes efficiency and configurability rather than photorealism. A reported OpenPilot MetaDrive regression also shows that model changes can make the loop leave lane. Those facts support using MetaDrive for integration and fault regression, not assuming its RGB is an equivalent pretrained-perception benchmark.

- [OpenPilot simulator README](https://github.com/commaai/openpilot/blob/master/openpilot/tools/sim/README.md)
- [comma 0.9.5 release: MetaDrive tests](https://blog.comma.ai/095release/)
- [MetaDrive paper](https://arxiv.org/abs/2109.12674)
- [OpenPilot MetaDrive regression report](https://github.com/commaai/openpilot/issues/34044)

## Fixed contract

- Upstream route: `8494c69d3c710e81|000001d4--2648a9a404`, segment 4.
- Frames: `[0, 60)` from upstream `model_replay.py`.
- Inputs: front, wide, cabin HEVC and rlog; URL content metadata is retained.
- Outputs: aggregate `modelV2`/`driverStateV2` counts, frame age/drop, lane probabilities, path horizon, curvature, and execution time.
- Public bundle: aggregate JSON, generated Markdown, SVG, and SHA-256 links to retained local summary/MetaDrive evidence. No video, decoded frame, per-frame telemetry, model, or local path is published.

## Reproduce

The pinned OpenPilot FrameReader passes the deprecated `-vsync` argument, which current FFmpeg 8/9 no longer accepts. Install the hash-verified FFmpeg 7.1 helper, then run with OpenPilot's tools dependencies available in its virtual environment:

```bash
cd /home/hyunsung/src/openpilot-sim-lab
scripts/setup_real_camera_replay.sh
uv pip install --python /home/hyunsung/src/openpilot/.venv/bin/python matplotlib
PATH="$PWD/.tools/bin:$PATH" /home/hyunsung/src/openpilot/.venv/bin/python \
  scripts/run_real_camera_model_replay.py \
  --openpilot-root /home/hyunsung/src/openpilot \
  --output outputs/real-camera-model-replay-$(date -u +%Y%m%dT%H%M%SZ)
```

Dirty source trees are rejected unless `--allow-dirty` is explicitly used for a diagnostic. Output contains `manifest.json`, `model_metrics.csv`, and `summary.json`. Four explicitly selected raw RGB frames and their model overlays are retained under `diagnostics/` for local source-hashed domain analysis; neither is public evidence. The first timing sample is excluded exactly like upstream `model_replay.py`.

## Verdict model

`functional_status` checks exact output counts, ordered unique model frame IDs, and finite core output values. `timing_status` independently checks the upstream model/driver execution limits. A result may therefore be `functional_pass_timing_not_qualified`; this is the correct classification for a complete replay on a host that is not a qualified device-timing environment.

The retained control produced 60/60 model and driver outputs. It showed high lane probabilities and a long path horizon on the real-camera route, in sharp contrast to the fresh but low-confidence, short-horizon MetaDrive output. This supports an input-domain mismatch diagnosis. It does not establish ground-truth perception accuracy or road safety.
