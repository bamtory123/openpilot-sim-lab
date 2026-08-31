# v0.2 static-lead camera-alignment sample

This release-friendly subset records one deterministic local static-lead fixture: the ego follows the reference lane at a 2.0 m/s specialist target while a stationary synthetic lead starts 20 m ahead on that lane. The local run was deliberately retained as `valid/fail: collision`; it is a baseline for future perception and longitudinal-control work, not a success claim.

`camera-alignment-sample.json` joins three saved RGB capture identities to MetaDrive telemetry. Distance and TTC fall from 18.17 m / 11.61 s at 2 s to 6.76 m / 3.40 s at 8 s. The raw images, full telemetry, logs, and local specialist artifact remain untracked.

The labels are analysis-only. They are not injected into the camera stream, planner, or vehicle control path, and no lead-perception or braking model is trained or evaluated here. This result does not demonstrate lead detection, following, braking, collision avoidance, pretrained openpilot behavior, vehicle performance, or real-road capability.
