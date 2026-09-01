# SDV ADAS SIL Regression Validation Lab — v0.1 계획

## 프로젝트 목적

OpenPilot을 System Under Test(SUT)로, MetaDrive를 Software-in-the-Loop(SIL) 환경으로 사용해 실행 형상 고정, 요구사항 기반 시험, camera transport-delay 결함 주입, ground-truth 수집, 성능 회귀 판정 및 릴리스 증적 생성을 자동화한다.

`openpilot-sim-lab`은 SUT 자체가 아니라 orchestration, telemetry, fault, verdict, report 프레임워크다. 공식 v0.1 시나리오는 `md_default_loop_lane0_v1`: OpenPilot 기본 **2차로** loop map의 고정 reference lane 추종이다.

## 범위와 비목표

- SUT: OpenPilot. SIL simulator: MetaDrive. 실행: WSL2 Ubuntu.
- formal fault: 0/50/100/150 ms camera transport delay, warm-up 제외 조건별 3회 interleave.
- CARLA, TensorRT, Chestnut 비교, HIL, 실차 CAN/ECU, 실차 검증은 v0.1 비목표 또는 후속 roadmap이다.
- 이 프로젝트는 repeatability study이며, 통계적 일반화나 OpenPilot의 일반적 우수성 입증이 아니다.

## 아키텍처와 형상

두 저장소 commit/dirty/submodule, MetaDrive package·asset, Python, WSL kernel, GPU/driver, scenario SHA-256, command는 run manifest에 기록한다. `configs/compatibility.yaml`은 기대 형상, manifest는 실제 형상이다. 자세한 구조는 [architecture](docs/architecture.md)를 따른다.

## 요구사항·시험·판정

요구사항은 ENV/DATA/TIM/FUNC/REG/REL로 분류한다. Test Case와 artifact 관계는 [requirements](docs/requirements.md), [test plan](docs/test-plan.md), [traceability](docs/traceability.md)에 정의한다.

The governing baseline, regression, and qualification choices are retained in the [decision log](docs/decisions.md).

개별 run은 `valid/pass`, `valid/fail`, `invalid/not_evaluated`로 판정한다. infrastructure/data 오류는 invalid이며, SUT lane departure는 coverage가 충족될 때만 valid fail이다. 프레임워크 release qualification은 SUT outcome과 별도다.

## v0.1 milestones

| Milestone | 상태 | 증적 |
|---|---|---|
| M0 형상/문서 | 구현됨 | compatibility, manifest, 이 계획 |
| M1 ground truth | 구현됨 | telemetry/reference-lane instrumentation |
| M2 non-blocking delay | 구현됨 | queue tests, camera.csv |
| M3 lifecycle/verdict | 구현됨 | runner, invalid recovery |
| M4 requirements/test traceability | 구현됨 | CI traceability checks, 이 문서 세트 |
| M5 baseline/regression gate | 구현됨 | baseline audit, regression-review hard/provenance gates |
| M6 formal v0.1 experiment | 완료 | v0.1 formal matrix artifact |
| M7 qualification release package | closed: not qualified | package complete; candidate Phase 1 hard-gate fail |

## Definition of Done와 roadmap

v0.1은 formal 12-run evidence, provenance, data-integrity verdict, requirements-to-artifact traceability, provisional baseline/regression contract, qualification report와 known limitations을 갖추는 것을 목표로 한다. 그 전 release qualification은 `not_qualified_yet`이며, P0 artifact 완성과 Phase 1 regression gate 통과가 있어야만 framework verdict `pass_with_limitations`을 허용한다. 실제 GitHub Release 자동화는 구현 전까지 계획으로만 둔다. v0.2 이후에는 GPU runtime regression, CARLA/OpenX adapter, CAN/HIL interface design을 별도 확장으로 다룬다.

## 한계

모든 threshold는 자동차/OEM 기준이 아닌 `project_defined` 기준이어야 하며 baseline 측정 전 performance threshold를 확정하지 않는다. 상세 한계는 [limitations](docs/limitations.md)를 따른다.
