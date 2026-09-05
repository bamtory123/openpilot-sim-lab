# OpenPilot patch bundles

These bundles make the simulator integration reproducible without publishing a
second full OpenPilot mirror. They are not a replacement for upstream source.

1. Start from `commaai/openpilot@084747c75d2cbd23af65ab7a9e770bbd7b98bac9`.
2. Verify and apply the v0.1 instrumentation bundle.
3. Apply the v0.2 bundle only for the separate adapter-pilot or actuator-calibration work.

```bash
simlab=/path/to/openpilot-sim-lab
openpilot=/path/to/openpilot
git -C "$openpilot" apply --check "$simlab/patches/openpilot-v01-sim-instrumentation.patch"
git -C "$openpilot" apply "$simlab/patches/openpilot-v01-sim-instrumentation.patch"

# Optional: v0.2 only. It is not a v0.1 release input.
git -C "$openpilot" apply --check "$simlab/patches/openpilot-v02-carla-adapter.patch"
git -C "$openpilot" apply "$simlab/patches/openpilot-v02-carla-adapter.patch"
```

| Bundle | SHA-256 | Scope |
|---|---|---|
| `openpilot-v01-sim-instrumentation.patch` | `959e1846cd9b1a0111de346befcf749218f70ad74e06af574f284d687e6661c4` | MetaDrive instrumentation, non-blocking transport, telemetry, diagnostics |
| `openpilot-v02-carla-adapter.patch` | `2af5111111d4f02cab6be938d70ad764c3100c3fc21ee783170a4a62af658286` | Optional CARLA adapter/capture, actuator-ratio, and camera-domain diagnostics only |

The v0.1 bundle contains dormant experimental interfaces accumulated in the
instrumented checkout. The formal v0.1 scenario never enables specialist or
CARLA control; only the configuration and evidence boundaries in this
repository define a formal result.

To repeat the clean-base application check without changing the supplied
checkout, run:

```bash
scripts/verify_openpilot_patch_bundles.sh --openpilot-root /path/to/openpilot
```
