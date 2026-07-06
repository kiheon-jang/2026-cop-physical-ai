# CoP Physical AI Dashboard — 핸드오프 가이드

> Hdel `hdelMobileResearch/dashboard/HANDOFF.md` 와 동일 톤. CoP 구성으로 맞춤.

## 평소 사용

**dashboard.html 더블클릭** (또는 build 후 `--open`) — 정적 단일 HTML, 인터넷 없어도 동작.

오늘 밤 23:30 cron 잡이 끝나면 `data.json` 자동 갱신 → 다음에 새로고침하면 최신 진척.

---

## 운영 컴포넌트

| 위치 | 역할 |
|---|---|
| `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/` | 데이터 저장소 (CoP 본 repo) |
| `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/dashboard/` | 대시보드 (PLAN.md / build.py / template.html) |
| `/Volumes/MARK_DATA/dev/hermes-mark/` | Fastify + WebSocket 서버 (옵션 — Hdel 과 공유) |
| `~/.hermes/scripts/cop_*.py` | 3개 cron 잡 (sim_env / sim_test / retry_watcher) |
| `~/.hermes/scripts/cop_common.py` | claude-p 위임 + `rebuild_dashboard_data()` helper |

cron 등록 확인:
```bash
hermes cron list 2>&1 | grep -E "v3.2|야간 잡|아침 보고"
```

---

## 갱신 안 됐을 때 디버깅

### 1. `data.json` 이 옛날 것 (mtime 안 변함)

`cop_sim_test.py` 의 dashboard rebuild 단계 결과 확인:
```bash
# 잡 stdout (JSON line) 에서 "dashboard_rebuild" 키 확인
ls -t ~/.hermes/cron/output/f88b3198c9b6/ | head -3
# 또는 mtime 직접
stat -f "%Sm %z" /Volumes/MARK_DATA/dev/2026-cop-physical-ai/dashboard/data.json
```

수동 재빌드:
```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
python3 dashboard/build.py --json-only       # data.json 만
python3 dashboard/build.py                   # data.json + dashboard.html
python3 dashboard/build.py --open            # 빌드 후 브라우저로 열기
```

### 2. 빌드 자체가 실패 (subprocess 에러)

```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
python3 dashboard/build.py --json-only 2>&1 | tail -20
```
PHASE_ROADMAP.md / research-log / SAMPLE_STATUS.md 등의 형식이 바뀌면 파서가 깨질 수 있음.

### 3. 잡은 도는데 dashboard 텍스트가 옛날 것

`template.html` 직접 수정 후 한 번 풀 빌드해서 dashboard.html 새로 만들기:
```bash
python3 dashboard/build.py
```
template.html 변경분은 git 에 commit 하면 다른 맥에서도 반영됨 (template.html 은 .gitignore 안 됨, dashboard.html / data.json 만 ignore).

---

## 개발 (build.py / template.html 수정)

### 파서 추가 (예: 새 데이터 소스)

1. `build.py` 에 `build_<source>()` 함수 작성 → JSON 키 추가
2. `template.html` 에 `<div class="view hidden" id="view-<route>">` 섹션 + `<a class="nav-item">` 추가
3. `template.html` JS 에 `render<Source>()` 함수 + `setRoute` 분기 추가
4. 신규 라우트 키는 `ROUTES` 배열 + `ROUTE_LABEL` 에 추가

### DATA_MARKER 라인 (라인 707 근처)

```javascript
window.DATA = /*__DATA__*/{"meta":{...},"phases":[],...};
```
**반드시 한 줄로 유지**. build.py 의 `render()` 가 정규식으로 이 한 줄을 찾아 교체.

### 카테고리 룰 변경

`build.py` 의 `CATEGORY_RULES` 리스트 수정. 키워드 매칭 (대소문자 무시), 최대 2개까지 표시.

---

## 다른 맥으로 옮길 때

1. git pull 후 `dashboard/template.html` 와 `dashboard/build.py` 동기화됨
2. 그 맥에서 한 번 빌드:
   ```bash
   cd /path/to/2026-cop-physical-ai && python3 dashboard/build.py --open
   ```
3. 또는 dashboard.html 한 파일만 USB 로 (`data.json` 임베드됨, 인터넷 없이도 동작)

`data.json` / `dashboard.html` 은 .gitignore 라 git 으로 안 옮겨짐 — build.py 로 재생성하거나 산출물 파일 직접 옮김.

---

## 개인 상태 (북마크 · 메모)

브라우저 localStorage 에 저장 (도메인 종속). 다른 맥/브라우저로 옮기려면 localStorage 직접 export (개발자 도구) 또는 PLAN.md §10 의 Phase 2 JSON Export 기능 (미구현).

---

## Phase 2 polishing (PLAN.md §10)

- mockup/ 디렉토리 — Hdel 의 mockup 패턴 차용해 CoP 용 색상 시안
- hermes-mark watch 통합 — `/Volumes/MARK_DATA/dev/hermes-mark/` 의 watch 경로에 CoP 추가
- 분석 페이지 강화 — 커밋 빈도 시계열, Phase 진척 속도 차트
- 카테고리 필터 다중 선택
- localStorage JSON Export / Import

---

## 디버그 명령 모음

```bash
# 잡 상태
hermes cron list 2>&1 | grep -A4 "v3.2"

# 마지막 sim_test 결과
ls -t ~/.hermes/cron/output/f88b3198c9b6/ | head -1 | xargs -I {} cat ~/.hermes/cron/output/f88b3198c9b6/{}

# 마지막 watcher 결과
ls -t ~/.hermes/cron/output/b76453176bb4/ | head -1 | xargs -I {} cat ~/.hermes/cron/output/b76453176bb4/{}

# data.json 통계
python3 -c "
import json
d = json.load(open('dashboard/data.json'))
print(f'phases={len(d[\"phases\"])} sim_tasks={len(d[\"sim_tasks\"])} daily={len(d[\"daily\"])} blockers={len(d[\"blockers\"])}')
print(f'current: {d[\"meta\"][\"current_phase\"]}')
print(f'built_at: {d[\"meta\"][\"built_at\"]}')
"

# 옛 잡 복구 (롤백)
hermes cron pause 76b3cd4eb4fc && hermes cron pause f88b3198c9b6
hermes cron resume 9ad85007cf27 && hermes cron resume 85d322d3b37c
```

---

## R4 (2026-07-06) — 인터랙티브 보고: 3D 리플레이 / 성과 지표

새 페이지 2개 + 홈 하이라이트. 전부 **data.json 단일 경로**로 흐르므로 야간 크론 rebuild 만으로 자동 갱신.

| 구성 | 소스 | 갱신 주체 |
|---|---|---|
| 3D 리플레이 (view-sim3d) | `web3d_chain.json`(체인+경량메시, `scripts/export_web3d.py` 1회) + `data/episodes_cl*` parquet(수집 에피소드 100개) + `inference_progress/rollout_traj_latest.json`(정책 rollout, 측정마다 갱신) | build.py `build_web3d()` |
| 성과 지표 (view-results) | `inference_progress/rollout_summary*.json` 8종 + `history/`(측정마다 자동 축적) + `dr_samples/` 썸네일 + `logs/`(파이프라인 라이브) + 큐레이션 뉴스 | build.py `build_rollout_metrics()` 등 |
| 학습 데이터 영상 | `assets/reports/sim/episodes_cl*.mp4` (서버모드 `/static/cop/` 재생) | 수동 복사 (데이터셋 재수집 시 갱신) |

- three.js r152 UMD 가 template.html 에 인라인(자체완결 — CDN 불필요, 오프라인 동작).
- 씬(XML) 변경 시: `.venv/bin/python3 scripts/export_web3d.py` 재실행 후 커밋.
- 야간 훅: `~/.hermes/scripts/cop_common.py::rebuild_dashboard_data` 가 **레포 .venv python 풀빌드(HTML+JSON)** 로 전환됨 (pyarrow/PIL 필요 + 오프라인 파일 신선도).
