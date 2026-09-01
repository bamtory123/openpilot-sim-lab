# Baseline, regression and release process

1. Freeze environment and provenance.
2. Use the selected pretrained OpenPilot 0 ms three-run formal result for `md_default_loop_lane0_v1` after its excluded warm-up.
3. Review data integrity and individual variation.
4. Store baseline provenance and project-defined acceptance gates.
5. Run formal interleaved fault matrix.
6. Preserve valid pass, valid fail, invalid and retry provenance.
7. Generate qualification report that separates framework qualification from SUT outcome.

For the selected pretrained baseline, the observed lane departure is a known SUT functional failure, not a framework qualification failure. Regression comparison must instead detect KPI worsening (lateral error and applied steering rate), a newly observed collision or disengagement, and any data-integrity violation. A lane-departure-only baseline must never be relabeled as a passing SUT result.

Regression uses three phases. Phase 1 is an immediate hard gate for data integrity (coverage, unexpected drop, overflow, timestamp/order) and newly observed collision or disengagement. Phase 2 reports baseline-relative lateral/steering changes and earlier departure as `review_required`; three baseline replicates are not treated as sufficient statistical authority for an automatic performance fail. Phase 3 is enabled only after a documented project-defined threshold, rationale, baseline ID and approval date are recorded.

Until baseline provenance, traceability, regression-review artifact and qualification report are present, the release state is `not_qualified_yet`. Only then may the framework receive `pass_with_limitations`; its SUT outcome remains separately reported as the known baseline functional failure.

The v0.1 comparison reference is the frozen historical 0 ms, three-run baseline. Audit its required per-run artifacts and provenance before approval. A missing required artifact is `evidence_gap`: do not reconstruct it or replace the reference with a current-host run. A replacement needs explicit approval of a new baseline version. Execute a separate current-host compatibility check after the audit, record its manifest and outcome, and do not let it replace or redefine the historical baseline.

Baseline/regression automation is planned. The provisional contract is [acceptance.yaml](../baselines/md_default_loop_lane0_v1/acceptance.yaml); null performance gates are intentional until an approved baseline exists.
