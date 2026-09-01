# Test plan

| Test Case | Purpose | Requirements | Current evidence |
|---|---|---|---|
| TC-PREFLIGHT-001 | Check provenance, dirty policy and runtime availability. | ENV-001 | `simlab.runner preflight` |
| TC-DATA-001 | Check coverage, timestamp and frame integrity. | DATA-001, DATA-002 | unit tests and run summaries |
| TC-DELAY-000/050/100/150 | Measure target and actual delay per formal condition. | TIM-001 | formal matrix camera artifacts |
| TC-QUEUE-OVERFLOW-001 | Classify queue/drop failure as invalid. | TIM-002 | delay queue tests |
| TC-BASE-001 | Measure fixed reference-lane tracking outcome. | FUNC-001 | `md_default_loop_lane0_v1` |
| TC-REG-001 | Compare approved baseline KPI deltas. | REG-001, REG-002 | planned |
| TC-RELEASE-001 | Check traceability and qualification package. | REL-001, REL-002 | in progress |

Formal KPI starts only after simulator ready, SUT ready, engagement, fault enable and settle. Startup robustness is not a v0.1 functional KPI.
