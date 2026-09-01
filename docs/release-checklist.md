# v0.1 release checklist

This checklist controls framework qualification only. It does not convert the pretrained OpenPilot SUT's known lane-departure outcome into a driving pass.

| Item | State | Evidence |
|---|---|---|
| Frozen historical 0 ms baseline is complete | complete | `baselines/md_default_loop_lane0_v1/historical-audit.json` |
| Current host transport/engagement path is confirmed | complete | contract-listed two-run local probe evidence |
| Formal 12-run 0/50/100/150 ms matrix is preserved | complete | local `outputs/v0.2-formal-delay-matrix-20260828` |
| Regression-review hard/provenance gates | complete | `simlab regression-review`, unit tests |
| Independent same-provenance candidate comparison | pending | candidate formal artifact plus review JSON |
| Requirements-to-artifact release trace | in progress | `docs/traceability.md` |
| Qualification report and limitations | in progress | `docs/qualification-report.md`, `docs/limitations.md` |
| GitHub release tag and selected sample attachment | pending | do not create while qualification is `not_qualified_yet` |

The current release state is `not_qualified_yet`. A release may be considered only after every pending item is resolved and the qualification report explicitly records `pass_with_limitations` for the framework, while retaining the SUT outcome separately.
