# CoP Physical AI 대시보드 — 기획안 v0.1

> **목적**: CoP Physical AI 프로젝트의 시뮬 단계별 작업·일일 진척·외부 의존·샘플 코드 상태·월간 보고용 증거를 한 곳에서 **종합 열람·필터·북마크·분석** 할 수 있는 사내용 정적 대시보드.
>
> **위치**: `dashboard/` (본 저장소)
> **벤치마크**: `hdelMobileResearch/dashboard/` 의 톤앤매너 + 구조 일치, 메뉴/데이터 모델만 CoP 맞춤.
> **상태**: 기획 완료. Phase 1 MVP 구현 단계.

---

## 1. 왜 필요한가

현재 자산 흐름:

```
Hermes cron (v3.2 패턴, no_agent + claude -p)
   │
   ├─ research/simulation/YYYY-MM-DD_<단계>.md  (단계별 시뮬 작업)
   ├─ agent/research-log/YYYY-MM-DD.md         (일일 진척 로그)
   ├─ research/simulation/PHASE_ROADMAP.md     (Phase 0~5, 주차/일별 체크리스트)
   ├─ agent/report-evidence/YYYY-MM/INDEX.md   (월간 보고 증거)
   ├─ agent/external-dependencies.md           (외부 의존 / 차단 항목)
   ├─ samples/SAMPLE_STATUS.md                 (샘플 코드 완성도)
   └─ research/decisions/*.md                  (아키텍처 결정)
```

문제:
1. **분산** — 6개월(Phase 0~5)간 누적 N백 개 마크다운. 폴더 트리만으론 한눈에 안 보임.
2. **Phase 진척 시각화 부재** — 체크리스트 텍스트로만 봐서 어디까지 왔는지 즉시 인지 어려움.
3. **외부 의존 추적 어려움** — `external-dependencies.md` 가 점점 길어지면 우선순위·마감일 관리 어려움.
4. **샘플 코드 상태 산만** — 표는 있으나 카테고리·검증일·완성도별 필터 불가.
5. **월간 보고 준비 비효율** — 증거 후보가 일일 로그 곳곳에 흩어짐. 월말 수동 취합 부담.

→ **대시보드 한 페이지에서 모든 자산을 시각화·탐색·큐레이션**.

---

## 2. 핵심 사용자 시나리오

### S1. 평일 아침, 일정 점검
"오늘 PHASE_ROADMAP 의 [ ] 항목이 무엇인가? 어제 [자가치유] 가 발동했나? 외부 의존 차단 중인 게 뭔가?"

### S2. 주간 회고
"이번 주 시뮬 작업 5건 → 어느 카테고리 (MuJoCo/Camera/Pick-Place 등) 였나? 다음 주 Phase 진척 예측?"

### S3. 월말 보고서 작성
"이번 달 보고용 증거 후보 모아보기 → 카테고리별 분류 → 보고서 [2.X] 섹션에 매핑"

### S4. Sim2Real 의사결정 (실기팀 협업)
"옵션 외부 의존 (캘리브값/실측 무게) 중 받은 것 / 안 받은 것 한눈에"

### S5. 신규 합류 엔지니어
"우리 팀이 Phase 0 부터 무엇을 했는지 카테고리·날짜 필터로 onboarding"

### S6. 핸드오프 / 백업
"git pull 후 dashboard.html 더블클릭 → 즉시 동작 (정적 단일 HTML)"

---

## 3. 기능 명세 (우선순위별)

### Must (MVP)

| ID | 기능 | 설명 |
|---|---|---|
| M1 | **통합 리스트 뷰** | sim_tasks + daily + evidence + samples + blockers 한 페이지 카드 그리드 |
| M2 | **검색** | 풀텍스트 (제목·발췌·Phase·카테고리·태그) |
| M3 | **필터** | Phase (0~5), 카테고리(9개), 상태(완료/진행/계획), 기간, 태그 |
| M4 | **정렬** | 최신순 / 오래된순 / Phase 순 / 카테고리순 / 북마크순 |
| M5 | **Phase 진행률 시각화** | Phase 0~5 별 progress bar + 주차별 체크리스트 |

### Should

| ID | 기능 | 설명 |
|---|---|---|
| S1 | **북마크** | 카드별 ⭐ — localStorage 저장 |
| S2 | **메모** | 카드별 사용자 메모 — localStorage |
| S3 | **분석 차트** | 커밋 빈도, 카테고리 분포, Phase 진척 속도 |
| S4 | **외부 의존 우선순위 보드** | 마감일 임박 / 담당자별 / 우선순위 1·2 카드 |

### Could

| ID | 기능 | 설명 |
|---|---|---|
| C1 | **타임라인 뷰** | Phase 0~5 Gantt 풍 |
| C2 | **카테고리 트렌드** | 월별 카테고리 분포 차트 |

---

## 4. 메뉴 구조 (12개)

Hdel 9개 + CoP 특수 3개.

| # | 메뉴 | 데이터 소스 | 카드 형태 |
|---|---|---|---|
| 1 | **현재 단계** | PHASE_ROADMAP 의 현재 `[ ]` 항목 + 진행률 | 큰 히어로 + 다음 액션 리스트 |
| 2 | **시뮬 작업** | `research/simulation/*.md` | 카드 그리드 (제목·날짜·Phase·카테고리·발췌) |
| 3 | **일일 진척** | `agent/research-log/*.md` | 날짜별 카드 (단계·메트릭·이슈·자가치유) |
| 4 | **월간 보고용 증거** | `agent/report-evidence/YYYY-MM/INDEX.md` + `W?_summary.md` | 월별 컨테이너 |
| 5 | **Phase 로드맵** | PHASE_ROADMAP.md 파싱 | Phase 0~5 progress + 주차/일별 체크리스트 |
| 6 | **외부 의존 차단** ⭐ CoP 특수 | `agent/external-dependencies.md` | 우선순위 1·2 + 담당자 / 마감일 |
| 7 | **샘플 코드 상태** ⭐ CoP 특수 | `samples/SAMPLE_STATUS.md` + 디렉토리 스캔 | 카테고리별 완성도 표 + 검증일 |
| 8 | **결정** ⭐ CoP 특수 | `research/decisions/*.md` | 결정 카드 (제목·날짜·근거) |
| 9 | **사이트 설명** | 정적 | About 페이지 |
| 10 | **사용가이드** | 정적 (Hdel 가이드 차용 + CoP 용 수정) | Help 페이지 |
| 11 | **북마크** | localStorage | 사용자가 ⭐ 표시한 카드 |
| 12 | **분석** | 빌드 시점 계산 | 차트 (커밋/카테고리/Phase) |

---

## 5. 카테고리 자동 추론 (CoP 시뮬 단계 기반)

`build.py` 의 `CATEGORY_RULES`:

```python
CATEGORY_RULES = [
    ("MuJoCo/MJCF",     ["mujoco", "mjcf", "freejoint", "geom", "viewer"]),
    ("Camera",          ["camera", "renderer", "rgb", "오버헤드", "그리퍼 카메라"]),
    ("Kinematics",      ["joint", "관절", "kinematics", "calibration", "캘리브"]),
    ("Pick-Place",      ["pick", "place", "pick-place", "grasp", "큐브"]),
    ("Data Collection", ["dataset", "에피소드", "data_collector", "lerobot dataset"]),
    ("ACT",             ["act", "imitation", "모방학습", "policy"]),
    ("DP",              ["diffusion policy", "dp"]),
    ("Sim2Real",        ["sim2real", "sim-to-real", "domain randomization"]),
    ("Hardware",        ["pcb", "rs232", "serial", "hht", "결선"]),
]
```

키워드 매칭 (대소문자 무시), 최대 2개 카테고리 (`A · B`).

---

## 6. 데이터 모델 (data.json 구조)

```json
{
  "meta": {
    "built_at": "2026-06-07T23:32:00+09:00",
    "repo_head": "abc1234",
    "today": "2026-06-07",
    "current_phase": "Phase 1 - W3 - ACT 학습"
  },
  "phases": [
    {"id": "phase0", "name": "Phase 0 — 시뮬 환경 셋업",
     "date_range": "2026-05", "weeks": [...], "progress": 1.0, "status": "완료"},
    {"id": "phase1", "name": "Phase 1 — 사전학습", ...}
  ],
  "sim_tasks": [
    {"id": "sim-2026-06-06-test", "title": "시뮬 환경 테스트 및 메트릭 수집",
     "date": "2026-06-06", "phase": "phase1", "category": "Data Collection",
     "excerpt": "...", "path": "research/simulation/2026-06-06_시뮬-...",
     "scripts_mentioned": ["sim_pick_place.py", ...]}
  ],
  "daily": [
    {"id": "daily-2026-06-06", "date": "2026-06-06", "weekday": "목",
     "phase_label": "Phase 1 - W1-2",
     "scripts": [...], "metrics": {...}, "issues": [...],
     "self_heal_actions": [...], "next_steps": [...]}
  ],
  "evidence": [
    {"month": "2026-06", "index_path": "...", "items": [...],
     "weekly_summaries": [...]}
  ],
  "blockers": [
    {"id": "...", "owner": "실기 담당", "title": "...",
     "deadline": "2026-06-22", "priority": 1, "checked": false}
  ],
  "samples": {
    "summary": {"unit": [0, 0, 0, 2], "training": [7, 0, 0, 3], ...},
    "files": [
      {"path": "training/sim_pick_place.py", "category": "training",
       "status": "complete", "stars": 3, "last_verified": "2026-05-22",
       "description": "..."}
    ]
  },
  "decisions": [
    {"id": "...", "title": "시뮬레이터 선택", "date": "2026-04-22",
     "path": "research/decisions/2026-04-22_simulator-selection.md",
     "excerpt": "..."}
  ],
  "stats": {
    "total_sim_tasks": 34,
    "total_daily_entries": 30,
    "category_distribution": {...},
    "self_heal_count_30d": 5,
    "commit_velocity_7d": 1.2,
    "blockers_active": 3
  }
}
```

---

## 7. 파일 구조

```
2026-cop-physical-ai/
  dashboard/
    build.py              # Python — repo 스캔 + JSON + HTML 빌드 (~600 LOC)
    template.html         # UI (HTML+CSS+JS 인라인, /*__DATA__*/ 마커)
    data.json             # 빌드된 JSON (gitignored)
    dashboard.html        # 최종 산출 (gitignored — 또는 commit 결정)
    PLAN.md               # 본 문서
    HANDOFF.md            # 다음 작업자/머신용 핸드오프 가이드
    mockup/               # 옵션 — 디자인 시안 (Phase 2)
```

빌드 산출물 (`data.json`, `dashboard.html`) 은 `.gitignore` 추가 권장 (사이즈 큼, build.py 로 재생성 가능).

---

## 8. 빌드 흐름

매일 23:30 의 `cop_sim_test.py` 잡 마지막에 자동 rebuild:

```python
# cop_common.py 에 추가
def rebuild_dashboard_data(repo: Path, timeout: int = 60) -> dict:
    """잡 끝에 호출 — dashboard.html + data.json 갱신.
    Hdel 패턴과 동일. Best-effort: 실패해도 잡 자체는 ok.
    """
    build_py = repo / "dashboard" / "build.py"
    if not build_py.exists():
        return {"ok": False, "reason": "build.py 없음"}
    r = subprocess.run(
        ["python3", str(build_py)],
        cwd=repo, capture_output=True, text=True, timeout=timeout,
    )
    return {"ok": r.returncode == 0, ...}

# cop_sim_test.py main() 끝에 추가
dashboard = rebuild_dashboard_data(REPO)
phase("dashboard_rebuild", f"ok={dashboard.get('ok')}")
```

수동 실행도 가능:
```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
python3 dashboard/build.py           # 실데이터
python3 dashboard/build.py --open    # 빌드 후 브라우저
python3 dashboard/build.py --demo    # mock 데이터로 디자인 미리보기 (Phase 2)
```

---

## 9. hermes-mark 사이트 연동 (옵션)

Hdel 은 `/Volumes/MARK_DATA/dev/hermes-mark` 가 chokidar 로 `hdelMobileResearch/dashboard/data.json` watch + WS push.
CoP 도 같은 방식 가능 — hermes-mark 의 watch path 에 CoP 의 `dashboard/data.json` 추가하면 됨. **사용자가 hermes-mark 측 설정 수정 필요** (본 작업 범위 밖).

CoP 대시보드 자체는 **정적 단일 HTML** 로 우선 동작 — `dashboard.html` 더블클릭만으로 전체 기능 사용 가능. 사이트 연동은 nice-to-have.

---

## 10. 다음 단계

| 단계 | 산출물 | 작업량 |
|---|---|---|
| **Phase 1 MVP** | PLAN.md + build.py + template.html (Hdel template 차용 + 메뉴/데이터 모델 surgical 변경) + cop_common/sim_test 통합 | 본 작업 |
| Phase 2 — 디자인 시안 | mockup/ — Hdel 의 mockup 패턴 차용해 CoP 용 색상/카테고리 시안 | 후속 |
| Phase 3 — hermes-mark 연동 | hermes-mark watch 경로에 CoP 추가 | 사용자 작업 |

---

## 변경 이력
- 2026-06-07: 최초 작성. Hdel dashboard v0.1 의 메뉴/구조 패턴 차용. CoP 의 Phase 기반 + 외부 의존 트래킹 + 샘플 코드 상태 + 결정 기록 3개 특수 메뉴 추가.
