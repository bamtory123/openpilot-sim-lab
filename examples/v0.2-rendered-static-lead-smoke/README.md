# v0.2 rendered static-lead smoke sample

This sample verifies only that MetaDrive 0.4.2.3's optional full asset archive can render a static Ferra lead vehicle in the road RGB stream. It is an environment smoke, not part of the v0.1 repeatability study.

The 20 m lead run completed 400 camera frames and produced `valid/fail: collision`; it had no lane departure and 0.35976 m lateral RMSE. The expected collision is evidence that no detector, range estimator, braking policy, or avoidance controller consumes the rendered actor. Ground truth remains offline and no claim about vehicle perception or real-road behaviour is made.

The source environment is intentionally restored to MetaDrive's minimal assets after this smoke. Running the scenario requires separately installing the matching full asset archive; its manifest records asset version `0.4.2.3` and Ferra mesh SHA-256 `6f99d045…5182e79e`. A separate long full-asset attempt exposed WSL/DXG instability, so this is not a release gate or repeatable-performance claim.
