---
id: proposals
title: "시뮬 작업"
order: 8
menu_route: proposals
screenshot: proposals.png
category: 도구
---
## 기능명세
<!-- slide title="시뮬 작업 — 개요" -->

시뮬 작업 화면(`view-proposals`)은 `research/simulation/` 디렉토리의 모든 마크다운 파일(PHASE_ROADMAP.md 제외)을 카드 또는 리스트로 탐색하는 화면이다. Phase·카테고리 필터, 정렬, 북마크, 상세 시트가 모두 지원된다.

**헤더**
제목: "시뮬 작업". 부제: "research/simulation/ 단계별 작업 기록 · Phase / 카테고리별 검색·필터·정렬".

<!-- slide title="필터 툴바" screenshot="" -->
**필터 툴바 (proposals-toolbar)**
- **Phase 필터 chip**: 전체 / Phase 0 / Phase 1 / Phase 2 / Phase 3 / Phase 4. 각 chip 옆에 해당 Phase 항목 수 표시(`g-phase0`~`g-phase4`, `f-all`).
- **카테고리 드롭다운 (`status-filter`)**: 전체 / MuJoCo/MJCF / Camera / Kinematics / Pick-Place / Data Collection / ACT / DP / Sim2Real / Hardware. `build.py`의 `CATEGORY_RULES` 키워드 매칭으로 각 파일에 카테고리가 자동 부여된다.
- **정렬 드롭다운 (`sort-sel`)**: 최신순(date-desc) / 오래된순(date-asc) / 카테고리순(app) / 북마크된 순(bookmark).
- **뷰 토글**: 카드 보기(기본) / 리스트 보기.

<!-- slide title="카드/리스트 항목 구조" screenshot="" -->
**카드 목록 (proposals-cards) / 리스트 (proposals-rows)**
`build_sim_tasks()`가 반환한 배열에서 생성. 각 항목:
- `title`: 파일 내 첫 `# 제목` (없으면 파일명 stem)
- `date`: 파일명에서 추출한 YYYY-MM-DD
- `category`: 키워드 매칭 자동 부여(최대 2개 카테고리, ` · ` 구분)
- `phase_id` / `group`: phase0~phase4 (Phase 필터 chip 호환)
- `phase_label`: 파일 내 `## 오늘 진행 단계` 섹션 첫 줄
- `excerpt`: 파일 내 첫 비어있지 않은 비제목 줄(최대 200자)
- `scripts_mentioned`: 본문에 언급된 `sim_*.py` 스크립트 목록
- `path`: 파일 상대 경로 (소스 파일 링크용)
- 북마크 아이콘(☆/★), localStorage 저장

<!-- slide title="상세 시트 · 검색 · 데이터 출처" screenshot="" -->
**카드 클릭 → 상세 시트 (sheet)**
카드 클릭 시 우측에서 사이드 시트 오버레이가 슬라이드인:
- 상단: 카테고리·날짜 메타, 파일 제목
- 본문: 파일 본문 발췌 또는 요약
- 액션: 북마크 토글, 메모 입력(localStorage), 소스 파일 열기(`agent/research-log/` 또는 상대 경로), 상태 마킹(검토중/채택/보류/보관)
- 닫기: Esc 또는 오버레이 클릭

**검색 연동**
상단 검색창(`/` 키 또는 우상단 입력)에 키워드 입력 시 제목·발췌·phase_label·카테고리·scripts_mentioned 전체 대상으로 필터링.

**데이터 출처**: `build_sim_tasks()`. `research/simulation/*.md` 전체 스캔(PHASE_ROADMAP.md 제외). `data.proposals`는 `data.sim_tasks`의 alias.

**상호작용**
- Phase chip, 카테고리 드롭다운, 정렬 드롭다운은 상태를 조합해 동시 필터링.
- 카드/리스트 토글은 URL hash 없이 UI만 전환.

## 사용가이드
<!-- slide title="사용가이드 — 개요" -->

시뮬 작업은 지금까지 진행한 모든 시뮬레이션 작업 파일을 검색하고 탐색하는 화면입니다.

**기본 탐색**
화면 상단에 Phase 0~4 버튼을 클릭하면 해당 Phase의 작업만 필터링됩니다. 원하는 카드를 클릭하면 오른쪽에 상세 내용이 펼쳐집니다.

<!-- slide title="카테고리 필터 · 정렬" screenshot="" -->
**카테고리 필터**
상단 오른쪽 드롭다운에서 기술 카테고리별로 필터링할 수 있습니다. 예를 들어 "ACT"를 선택하면 ACT 모방학습과 관련된 작업만 보입니다. 카테고리는 파일 내용을 분석해 자동으로 부여됩니다.

**정렬**
최신순이 기본입니다. "북마크된 순"을 선택하면 내가 표시한 중요 항목이 위로 올라옵니다.

<!-- slide title="북마크 · 메모 · 소스 · 검색" screenshot="" -->
**북마크 & 메모**
카드 오른쪽 위 ☆ 아이콘을 클릭하면 북마크됩니다. 상세 시트를 열고 "메모" 버튼을 클릭하면 해당 작업에 메모를 저장할 수 있습니다. 북마크와 메모는 이 브라우저에만 저장됩니다.

**소스 파일 열기**
상세 시트 오른쪽 위 "소스 파일 →" 버튼을 클릭하면 원본 마크다운 파일 경로를 확인할 수 있습니다.

**검색**
우상단 검색창(또는 / 키)에 키워드를 입력하면 제목, 내용 요약, Phase, 카테고리, 스크립트명까지 전체 검색합니다.
