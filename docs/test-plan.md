# Test plan

| Test Case | Purpose | Requirements | Current evidence |
|---|---|---|---|
| TC-PREFLIGHT-001 | Check provenance, dirty policy and runtime availability. | ENV-001 | `simlab.runner preflight` |
| TC-COMP-001 | Audit frozen baseline completeness, then run two consecutive current-host confirmation probes without changing the baseline. | ENV-002 | 2026-09-01: 2 × `valid/pass`; local artifact root recorded in baseline contract |
| TC-DATA-001 | Check coverage, timestamp and frame integrity. | DATA-001, DATA-002 | unit tests and run summaries |
| TC-DELAY-000/050/100/150 | Measure target and actual delay per formal condition. | TIM-001 | formal matrix camera artifacts |
| TC-QUEUE-OVERFLOW-001 | Classify queue/drop failure as invalid. | TIM-002 | delay queue tests |
| TC-BASE-001 | Measure fixed reference-lane tracking outcome. | FUNC-001 | `md_default_loop_lane0_v1` |
| TC-REG-001 | Compare same-scenario/delay KPI deltas; hard-fail invalid/new collision/disengagement or incompatible scenario provenance, otherwise emit review-required. | REG-001, REG-002 | unit tests and historical self-consistency smoke |
| TC-RELEASE-001 | Check requirement/test/traceability consistency and qualification package. | REL-001, REL-002 | CI traceability test; completed package with final v0.1 `not_qualified_yet` disposition |

Formal KPI starts only after simulator ready, SUT ready, engagement, fault enable and settle. Startup robustness is not a v0.1 functional KPI.
