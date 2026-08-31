# v0.2 static-obstacle bounding-box matrix sample

This sample records an explicit black `box.bam` proxy attached to a non-rendered static physics lead in MetaDrive. It is a synthetic obstacle-label contract, not a vehicle representation.

Three fixed seeds produced 30 RGB samples with a 20/10 train/held-out split. Every sample has a projected `static_obstacle_bbox_xyxy_px` label; label areas span 21,673–439,333 px² and the audit found zero invalid boxes. All three closed-loop runs remain `valid/fail` for collision, with two lane-departure failures.

The raw images, telemetry, and local report remain untracked. No detector, range estimator, braking policy, or avoidance policy is trained or evaluated. Ground truth stays offline and is never provided to the runtime controller.
