# OpenPilot patch bundles

These bundles make the simulator integration reproducible without publishing a
second full OpenPilot mirror. They are not a replacement for upstream source.

1. Start from `commaai/openpilot@084747c75d2cbd23af65ab7a9e770bbd7b98bac9`.
2. Verify and apply the v0.1 instrumentation bundle.
3. Apply the CARLA bundle only for the separate v0.2 adapter pilot.

```bash
git apply --check patches/openpilot-v01-sim-instrumentation.patch
git apply patches/openpilot-v01-sim-instrumentation.patch

# Optional: CARLA v0.2 only. It is not a v0.1 release input.
git apply --check patches/openpilot-v02-carla-adapter.patch
git apply patches/openpilot-v02-carla-adapter.patch
```

| Bundle | SHA-256 | Scope |
|---|---|---|
| `openpilot-v01-sim-instrumentation.patch` | `959e1846cd9b1a0111de346befcf749218f70ad74e06af574f284d687e6661c4` | MetaDrive instrumentation, non-blocking transport, telemetry, diagnostics |
| `openpilot-v02-carla-adapter.patch` | `776346bd54554caac7bbff1b1b65f37a5dc474f0d9565368ffcad6f3cd1a2eab` | Optional CARLA adapter/capture only |

The v0.1 bundle contains dormant experimental interfaces accumulated in the
instrumented checkout. The formal v0.1 scenario never enables specialist or
CARLA control; only the configuration and evidence boundaries in this
repository define a formal result.
