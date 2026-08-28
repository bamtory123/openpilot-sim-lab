# Camera-domain-gap diagnostic

This document records evidence about the simulator camera input. It does not measure real-road perception accuracy or justify a steering-gain change.

## Fixed input contract

- MetaDrive road camera: 1928×1208 RGB.
- Bridge transport: immediate copy, BT.601 NV12 conversion, then VisionIPC at the same resolution.
- Modeld PC/tici narrow-camera expectation: 1928×1208 with 2648 px focal length.
- Simulator horizontal FOV: 40 degrees, equivalent to about 2648 px at 1928 px width.

The first-order resolution/FOV/focal-length geometry therefore matches. The RGB→NV12 limited-range contract has a unit fixture: black RGB becomes luma 16 with neutral chroma 128.

## Frame-aligned evidence

The 2026-08-29 diagnostic run captured the road image at simulation frame 2500 and emitted a JSON companion file. The matching telemetry row reported:

| Field | Value |
|---|---:|
| Current reference curvature | 0.000000 1/m |
| Reference curvature from frame 2600 | +0.008658 1/m |
| Lateral error | -0.978 m |
| Model/control target curvature | about +0.0000035 1/m |

The image visibly contains the upcoming left curve while the current segment is still straight. This is consistent with a near-zero model response to a visually present upcoming turn. It is not a ground-truth label for model outputs.

A later three-frame set used the same 40-degree, 2648.57 px camera contract:

| Simulation frame | Reference curvature (1/m) | Model/control target curvature (1/m) | Lateral error (m) |
|---:|---:|---:|---:|
| 2400 | 0.000000 | +0.0000054 | -0.877 |
| 2600 | +0.008658 | -0.0000066 | -1.029 |
| 2800 | +0.008658 | -0.0000054 | -0.737 |

The frame set reinforces that the near-zero model response persists after the reference segment enters the curve. It does not identify the cause within rendering, camera pose, calibration, or model generalization.

## Photometric baseline

For that capture, simple RGB-derived statistics were:

| Region | Luma mean | Luma std | Luma median | Chroma mean |
|---|---:|---:|---:|---:|
| Full frame | 128.33 | 33.07 | 130.72 | 18.21 |
| Lower-half road region | 98.73 | 13.33 | 95.94 | 10.20 |
| Centre lower road region | 98.58 | 11.76 | 96.24 | 9.84 |

These values are regression baselines only. They cannot be compared to a real camera without a matched real-road data protocol.

## Next controlled work

1. Capture matched frame sets at fixed map positions before and during the curve; retain frame metadata and telemetry joins.
2. Inspect model path/curvature output against those frame sets without changing controller gains.
3. If a camera change is proposed, alter one documented variable at a time and preserve the 40-degree formal baseline unchanged.
