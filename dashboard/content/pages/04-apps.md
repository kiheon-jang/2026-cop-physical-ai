---
id: apps
title: "Phase 로드맵"
order: 4
menu_route: apps
screenshot: apps.png
category: 핵심
---
## 기능명세

<!-- slide title="Phase 로드맵 — 개요" -->

Phase 로드맵 화면(`view-apps`)은 프로젝트의 6개월 진행 계획(4월 사전학습 + Phase 0~4)을 단계별 카드로 보여준다.

**헤더**
제목: "6개월 여정 (4월 사전학습 + 5~9월 작업)". 부제: "실기 없이 학습할 수 있는 환경 구축 → 9월 1차 기능 완성 (10월 시연). 각 단계의 비즈니스 결과와 주차별 진행률."

<!-- slide title="Phase 카드 구성" screenshot="" -->

**Phase 카드 목록 (apps-cards)**
`build_phase_roadmap()`이 `PHASE_ROADMAP.md`를 파싱해 반환한 `phases` 배열에서 JavaScript가 `phase-card-v2` 카드를 동적으로 생성한다. 각 카드 구성:
- 상단: 비즈니스 라벨(예: "5월: 실기 없이 학습할 수 있는 환경 구축") + 기술 라벨(예: "Phase 0 — 시뮬 환경 셋업") + 날짜 범위 + 상태 배지(완료/진행/예정)
- outcome 텍스트: "이 단계가 완료되면" 무엇이 가능한지 설명
- 주차별 진행률 바(W1~W4): 각 주의 완료율(done/total)
- 주차별 체크리스트 항목: `[v]` 체크된 항목은 완료, `[ ]`는 미완료로 표시. 날짜 레이블(date_label)과 작업명(task) 함께 표시

<!-- slide title="Phase 목록 (총 6개)" screenshot="" -->

**Phase 목록 (총 6개)**
- **사전학습 / Kick-off** (2026.04, is_prep): progress=1.0(완료). CoP 발족, 하드웨어 발주, ACT/DP 핵심 자료 학습. 체크리스트 없음.
- **Phase 0 — 시뮬 환경 셋업** (2026.05): MuJoCo 설치, SO-ARM101 MJCF import, 카메라/매핑/Pick-Place 구현.
- **Phase 1 — 사전학습** (2026.06): 데이터 합성 200ep, ACT 학습, 추가 데이터/재학습.
- **Phase 2 — Sim2Real 검증** (2026.07): 실기 50ep 수집, 시뮬↔실기 비교.
- **Phase 3 — PCB 조정** (2026.08): 실제 PCB 픽앤플레이스 학습.
- **Phase 4 — RS232 케이블 분리 / 1차 기능 완성** (2026.09): RS232 HHT 케이블 분리 + DP 비교 + 10월 시연 준비.

<!-- slide title="상태 스타일링 · 데이터 · 상호작용" screenshot="" -->

**카드 상태 스타일링**
- `is-done`: 완료 단계 (초록 배지)
- `is-active`: 현재 진행 중 (파란 배지)
- `is-plan`: 예정 (회색 배지, 투명도 0.82)

**데이터 출처**: `build_phase_roadmap()`이 `research/simulation/PHASE_ROADMAP.md`를 파싱. `PHASE_META` 상수(build.py)에서 비즈니스 라벨/outcome/report_label을 보강한다.

**Alias**: `data.apps`는 `data.phases`와 동일한 배열(빌드 시 aliasing).

**상호작용**
- 카드는 클릭 불가(상세 시트 없음). 진행률/체크리스트가 PHASE_ROADMAP.md 업데이트 후 자동 갱신.

## 사용가이드

<!-- slide title="사용가이드 — 개요" -->

Phase 로드맵은 프로젝트 전체 일정과 각 단계의 세부 작업을 확인하는 화면입니다.

**Phase 카드 읽는 법**
각 카드 맨 위의 굵은 제목이 비즈니스 관점 설명(예: "5월: 실기 없이 학습할 수 있는 환경 구축"), 그 아래 작은 글씨가 기술 이름(예: "Phase 0 — 시뮬 환경 셋업")입니다.

<!-- slide title="상태 배지 · 주차별 체크리스트" screenshot="" -->

**상태 배지**
카드 오른쪽 위의 작은 배지로 현재 상태를 확인할 수 있습니다:
- 초록 "완료" = 이미 끝났습니다
- 파란 "진행" = 지금 진행 중입니다
- 회색 "예정" = 아직 시작 전입니다

**주차별 체크리스트**
각 Phase 카드 안에 W1~W4로 주차가 나뉘며, 각 주에 완료해야 할 작업 항목이 체크리스트로 표시됩니다. 체크(v)된 항목이 완료된 작업입니다. 진행 중인 Phase의 미완료 항목을 보면 "지금 어떤 작업을 하고 있는지" 파악할 수 있습니다.

<!-- slide title="Outcome 텍스트 · 홈 화면 연결" screenshot="" -->

**Outcome(결과) 텍스트**
각 카드 상단의 설명 문장은 "이 Phase가 끝나면 무엇이 가능해지는지"를 설명합니다. 보고 자료에 복사해 쓸 수 있습니다.

**홈 화면과 연결**
홈(Overview) 화면의 6개월 Gantt "자세히 →"를 클릭하면 이 화면으로 바로 이동합니다.
