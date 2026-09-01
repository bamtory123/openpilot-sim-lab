# Baseline, regression and release process

1. Freeze environment and provenance.
2. Run excluded warm-up and three 0 ms baseline runs.
3. Review data integrity and individual variation.
4. Store baseline provenance and project-defined acceptance gates.
5. Run formal interleaved fault matrix.
6. Preserve valid pass, valid fail, invalid and retry provenance.
7. Generate qualification report that separates framework qualification from SUT outcome.

Baseline/regression automation is planned. The provisional contract is [acceptance.yaml](../baselines/md_default_loop_lane0_v1/acceptance.yaml); null performance gates are intentional until an approved baseline exists.
