---
id: analytics
title: "분석"
order: 13
menu_route: analytics
screenshot: analytics.png
category: 상세
---
## 기능명세
<!-- slide title="분석 — 개요" -->

분석 화면(`view-analytics`)은 시뮬 작업 데이터를 주간 추이, 카테고리 점유율, Phase별 누적으로 시각화하는 차트 화면이다.

**헤더**
제목: "분석". 부제: "시계열·앱별·카테고리별 추이".

<!-- slide title="3개 차트 패널" screenshot="" -->
**차트 그리드 (charts-grid)**
3개 패널:
1. **주간 신규/디벨롭 추이 (trend-chart)**: 최근 30일 일별 시뮬 작업(n)과 연구 로그(d) 수를 겹쳐진 바 차트로 표시. `stats.trend` 배열 사용(w: MM/DD 레이블, n: sim_tasks 수, d: daily 수).
2. **카테고리 점유율 (cat-chart)**: 카테고리별 항목 수를 가로 바 차트로 표시. `stats.catChart` 배열(name, v)에서 상위 8개. `stats.donut` 배열(상위 3개 + 기타)은 별도 도넛/pie 차트로 사용 가능.
3. **Phase별 누적 (appbar2, full 너비)**: Phase별 완료된 체크리스트 항목(n=완료, d=미완료)을 이중 스택 바 차트로 표시. `stats.appbar` 배열(name: Phase명, n: 완료수, d: 미완료수).

<!-- slide title="데이터 출처·상호작용" screenshot="" -->
**데이터 출처**: `_build_chart_stats()`가 `sim_tasks`, `daily`, `phases`에서 계산. `stats` 키 아래 `trend`, `catChart`, `donut`, `appbar` 배열로 제공.

**상호작용**
- 차트는 SVG 또는 JS 기반 커스텀 렌더러로 그려진다(외부 차트 라이브러리 없음).
- 클릭 인터랙션 없음(순수 시각화).

## 사용가이드
<!-- slide title="분석 활용 — 개요" -->

분석 화면은 이 프로젝트의 활동 데이터를 차트로 시각화한 화면입니다.

**차트 읽는 법**
- **주간 추이 차트**: 최근 30일 동안 매일 얼마나 많은 시뮬 작업과 연구 기록이 쌓였는지 보여줍니다. 막대가 높을수록 그날 활동이 많았습니다.
<!-- slide title="차트 읽는 법·활용 시점" screenshot="" -->
- **카테고리 점유율**: 지금까지 어떤 종류의 작업을 가장 많이 했는지 보여줍니다. 예를 들어 "MuJoCo/MJCF"가 많다면 시뮬레이터 환경 구축 작업이 많았다는 뜻입니다.
- **Phase별 누적**: 각 Phase에서 체크리스트 항목이 얼마나 완료됐고 얼마나 남았는지 한눈에 비교합니다.

**언제 활용하나요?**
- 보고 준비 시: "지난달 대비 이번 달 활동량이 어떤가" 확인
- 진척 점검 시: Phase별 완료율을 비교해 어느 단계가 뒤처지는지 확인
