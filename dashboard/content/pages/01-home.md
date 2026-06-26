---
id: home
title: "Overview (현재 단계)"
order: 1
menu_route: home
screenshot: home.png
category: 핵심
---
## 기능명세
<!-- slide title="Overview — 개요" -->

Overview 화면은 프로젝트 전체 진행 상황을 한 페이지에 압축해 보여주는 대시보드 홈이다.

**비전 히어로 (vision-hero)**
- 프로젝트명("CoP Physical AI")과 두 줄 요약(PCB 픽앤플레이스 모방학습 / AI 자동화 운영 설명)을 표시한다.
- 우측 D-day 카드: `completion_date`(2026-09-30, 9월 기능 완성) 기준 남은 일수를 실시간 계산해 표시한다.
- 진행률 바: Phase 시작(2026-05-01)~완료(2026-09-30) 구간에서 오늘의 시간 경과 마커(세로선)와 Phase 0~4 평균 달성률(초록 fill)을 함께 표시한다. 상단에 "진척 X% / 경과 Y%" 두 값을 비교 표시한다.
- 스케일 레이블: "4월 시작 / 50% / 9월 완료"

<!-- slide title="KPI 카드 · 핵심 목표" screenshot="" -->
**KPI 카드 행 (kpi-row)**
`build.py`의 `build_business_kpi()`가 계산한 값에서 3개 카드를 자동 생성한다:
- **목표 달성률** — `target_progress` % (Phase 0~4 평균 진행률)
- **이번 달 마일스톤** — `current_phase_business` 비즈니스 라벨 (현재 Phase의 목표 요약)
- **일정 대비** — `progress_vs_time_gap` 값: 양수이면 "+X%p 선행", 음수이면 "−X%p 지연"으로 표시

**핵심 목표 섹션 (targets-section)**
`PROJECT_VISION["targets"]`에서 정적으로 정의된 2개 목표 카드를 표시한다:
1. PCB 픽앤플레이스 성공률 70% (Phase 3, 8월 평가 기준)
2. RS232 HHT 결선 부분 성공률 40% (Phase 4, 9월 평가 기준)
각 카드에 아이콘·설명 컨텍스트가 함께 표시된다. 현재 수치가 아닌 목표치다.

<!-- slide title="2열 그리드 — Gantt · 히트맵" screenshot="" -->
**2열 그리드 (grid-2)**
- 좌: 6개월 Gantt 차트. Phase 별(사전학습/Phase 0~4) 진행률 바를 `build_phase_roadmap()`의 progress 값으로 렌더링한다. 각 행에 비즈니스 라벨(예: "5월: 시뮬 환경 구축"), 날짜 범위, 완료율(%)을 표시한다. "자세히 →" 링크로 Phase 로드맵(apps) 화면으로 이동한다.
- 우: 지난 60일 활동 히트맵. `_build_chart_stats()`가 계산한 heatmap 배열(날짜별 count/level/items)을 20×3 그리드로 렌더링한다. 셀 색상은 0~4단계(회색→진초록). 마우스 오버 시 커스텀 툴팁(날짜, 활동 항목 최대 3개)이 표시된다. 하단에 범례("적음 ··· 많음").

<!-- slide title="데이터 출처 · 상호작용" screenshot="" -->
**데이터 출처**: `build.py`의 `build_business_kpi()`, `build_phase_roadmap()`, `compute_stats()`, `_build_chart_stats()` 함수. 실제 레포지토리 파일(`PHASE_ROADMAP.md`, `research/simulation/*.md`, `agent/research-log/*.md`, `agent/external-dependencies.md`)에서 읽는다.

**상호작용**
- D-day, 진행률, KPI는 `data.json`을 통해 매일 23:30 cron 이후 자동 갱신되며 WebSocket으로 새로고침 없이 반영된다.
- Gantt의 "자세히 →" 클릭 시 Phase 로드맵 화면으로 이동.
- 히트맵 셀 hover 시 커스텀 tooltip(날짜·활동 항목) 표시.

## 사용가이드
<!-- slide title="사용가이드 — 개요" -->

Overview는 사이트에 처음 들어왔을 때 기본으로 보이는 화면입니다. 이 화면 하나에서 "지금 어느 단계를 진행 중인지", "목표까지 얼마나 남았는지"를 한눈에 확인할 수 있습니다.

**D-day 카드 (오른쪽 초록 박스)**
9월 30일(기능 완성 목표일)까지 남은 날수를 보여줍니다. 매일 자동으로 갱신됩니다.

**진행률 바**
초록 막대가 현재 AI 모델 학습 달성률, 세로선이 "오늘 날짜 기준으로 전체 일정 중 몇 %가 지났는지"를 나타냅니다. 세로선보다 초록 막대가 더 오른쪽에 있으면 일정보다 앞서가는 것입니다.

<!-- slide title="KPI 카드 · 핵심 목표 읽는 법" screenshot="" -->
**KPI 카드 3개**
- **목표 달성률**: Phase 전체 평균 진행률(%)
- **이번 달 마일스톤**: 현재 Phase의 비즈니스 목표 요약 텍스트
- **일정 대비**: 시간 경과 대비 진척 차이("+X%p 선행" 또는 "−X%p 지연")

**핵심 목표 카드**
프로젝트가 9월 말 달성해야 할 구체적 수치(PCB 픽앤플레이스 70%, RS232 결선 40%)를 보여줍니다. 이 수치는 목표치이며, 학습이 완료된 후 달성 여부를 평가합니다.

<!-- slide title="Gantt · 히트맵 읽는 법" screenshot="" -->
**6개월 Gantt (왼쪽 패널)**
4월 사전학습부터 Phase 0~4 각각의 완료율을 막대로 보여줍니다. "자세히 →"를 클릭하면 주차별 세부 체크리스트를 볼 수 있습니다.

**60일 활동 히트맵 (오른쪽 패널)**
각 칸이 하루를 의미합니다. 칸이 진할수록 그날 시뮬 작업이나 연구 기록이 많았다는 뜻입니다. 칸에 마우스를 올리면 그날 무엇을 했는지 간략히 표시됩니다.
