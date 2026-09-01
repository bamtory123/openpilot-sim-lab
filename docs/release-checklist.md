# v0.1 release checklist

This checklist controls framework qualification only. It does not convert the pretrained OpenPilot SUT's known lane-departure outcome into a driving pass.

| Item | State | Evidence |
|---|---|---|
| Frozen historical 0 ms baseline is complete | complete | `baselines/md_default_loop_lane0_v1/historical-audit.json` |
| Current host transport/engagement path is confirmed | complete | contract-listed two-run local probe evidence |
| Formal 12-run 0/50/100/150 ms matrix is preserved | complete | local `outputs/v0.2-formal-delay-matrix-20260828` |
| Regression-review hard/provenance gates | complete | `simlab regression-review`, unit tests |
| Independent same-provenance candidate comparison | complete: hard-gate fail | 3 × current 0 ms candidate runs, all invalid for coverage after known departure |
| Requirements-to-artifact release trace | in progress | `docs/traceability.md` |
| Qualification report and limitations | in progress | `docs/qualification-report.md`, `docs/limitations.md` |
| GitHub release tag and selected sample attachment | pending | do not create while qualification is `not_qualified_yet` |

The current release state is `not_qualified_yet`. The completed candidate comparison is a Phase 1 hard-gate failure, so it cannot advance qualification. A release may be considered only after every pending item is resolved and the qualification report explicitly records `pass_with_limitations` for the framework, while retaining the SUT outcome separately.

## Historical tag archive

Earlier portfolio tags (`v0.1.0-portfolio`, `v0.1.1-portfolio`, and `v0.1.2-portfolio`) predate this revised baseline-approval and qualification contract. They preserve prior harness snapshots only; they do not override the current `not_qualified_yet` decision or authorize a new release statement.

## Retained evidence boundaries

- The frozen formal matrix remains reproducible `valid/fail` lane-departure evidence, never a successful closed-loop OpenPilot claim.
- The simulator-specialist and `openpilot_serpentine_v1` material remains v0.2 experimental evidence. It cannot change the v0.1 baseline or release statement.
- Host interruption integrity remains implemented: manifests record UTC and WSL boot ID, recovery preserves interruption evidence, and bounded CUDA/renderer/preflight probes are available.
- Long CUDA-backed bridge stability remains open. Two foreground 59.99-second probes retained their boot ID, but this is not root-cause isolation or long-run clearance.
