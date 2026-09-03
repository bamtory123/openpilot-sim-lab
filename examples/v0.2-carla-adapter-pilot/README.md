# CARLA adapter-pilot public summary

This is a public-safe aggregate from a retained bounded CARLA v0.2 adapter-pilot matrix. It is outside the v0.1 MetaDrive release gate and does not demonstrate successful OpenPilot driving, CARLA closed-loop qualification, real-road performance, or generalization.

## Formal aggregate

| Field | Value |
|---|---|
| Retained pilot runs | 10 |
| Pilot status counts | integrated-but-not-stable=10 |
| Termination reason counts | lane_departure=10 |

All retained matrix runs were preserved as `integrated-but-not-stable: lane_departure`, rather than discarded as infrastructure failures or relabeled as a driving pass. The source SHA-256 is `aa5ee8a5dc1369a76a9301ddf6ca41e24c9690ac549d7b8b14f96af5395c516d`. This public sample excludes local paths, host/IP data, raw RGB, telemetry, logs, route transforms, and individual run IDs.
