# R3 핸드오프 — UI 재구조 (관리자 보고용)

> 새 세션이 이 문서만 읽고 R3 작업 이어갈 수 있도록 정리.
> 작성: 2026-06-08. R1 (제안 확정) + R2 (데이터 파이프) 완료 시점.

## 한 줄 요약

CoP Physical AI 대시보드 UI 를 **관리자 보고용** 으로 재구조. 메뉴 12→5 압축, 비전·D-day 히어로 추가, 영상 갤러리·날짜별 활동 카드·Obsidian 월별 보고서 풀 임베드. 톤은 비전공자 친화 + 비즈니스 outcome 우선, 기술 라벨은 부수.

## 완료 (skip)

### R1 — 제안 확정 (사용자 confirm)
- 메뉴 12개 → **5 핵심 + 도구 sidebar collapsible**
- Obsidian `03 Areas/회사문서/CoP_PhysicalAI/CoP_*_활동보고서.md` 풀 임베드 + 자동 동기화
- 영상 serve 방식: hermes-mark 에 static route 추가 (`/static/cop/...`)
- Git 중첩: 대시보드 표현만 — 날짜별 그룹 카드 (git history 자체 squash X)

### R2 — 데이터 파이프 (build.py)
data.json 에 7개 신규 키 emit. 확인:
```bash
python3 -c "import json; d=json.load(open('/Volumes/MARK_DATA/dev/2026-cop-physical-ai/dashboard/data.json')); print(sorted(d.keys()))"
```
예상 결과: `[..., 'activity_timeline', 'business_kpi', 'monthly_reports', ..., 'videos', 'vision']`

| 키 | 데이터 | 비고 |
|---|---|---|
| `vision` | 비전 + 시연 날짜 + 목표 (PCB 70% / RS232 40%) | 정적 (PROJECT_VISION 상수) |
| `business_kpi` | `d_day` / `target_progress` / `time_elapsed` / `progress_vs_time_gap` / `next_actions[3]` | Overview 히어로용 |
| `phases[*].business_label` | "5월: 실기 없이 학습할 수 있는 환경 구축" | 비전공자용 큰 라벨 |
| `phases[*].outcome` | "실기 로봇 없이도 학습 데이터 합성 가능. ..." | "이게 완료되면" 한 줄 |
| `phases[*].report_label` | "하드웨어 조립, 환경 구축" | 보고서 매핑 |
| `monthly_reports` | 8건 (4월 v1/v2 + 5~10월). `body_md` 가 풀 마크다운 | Obsidian 동기화 |
| `videos` | 3개 (pick_place / 6dof / overhead 30 frames). 각 영상에 `description` 비전공자 한 줄 | `path` 가 `research/simulation/video/...` |
| `activity_timeline` | 날짜별 1 카드. `commit_count` + `self_heal_count` + `categories` + `summary` 한국어 | 60일 |

## 할 일 (R3 — UI 재구조)

template.html 의 view-* 영역 5개 재작성. 톤·색·사이드바·다크모드는 유지. **변경은 페이지 레이아웃 + 새 컴포넌트만.**

### R3-1. Overview (📊 현재 단계) — 한 페이지 종합 보고서

```
┌─────────────────────────────────────────────────────┐
│ 🎯 2026-10 사내 시연                       D-145    │
│ PCB 픽앤플레이스 자동화 — 정비현장 첫걸음             │
│                                                     │
│ 목표 달성률 ████░░░░░░░░░░░░░░ 20%  (시간 20%, 정시) │
│ 현재: 6월: AI 모델 사전학습 (Phase 1 W3)              │
└─────────────────────────────────────────────────────┘

KPI 4: [시연까지 D-145] [달성률 20%] [이번 달 마일스톤] [위험 신호]

Gantt 6개월 timeline (Phase 0~5 한 화면, 색상=status):
Phase 0  ████████████ 5월 (완료)
Phase 1  ████░░░░░░░░ 6월 (진행 20%)
Phase 2  ░░░░░░░░░░░░ 7월
Phase 3  ░░░░░░░░░░░░ 8월
Phase 4  ░░░░░░░░░░░░ 9월
Phase 5  ░░░░░░░░░░░░ 10월

다음 액션 3개 (business_kpi.next_actions)
60일 활동 heatmap (작게, 카테고리 색)
```

데이터: `D.vision`, `D.business_kpi`, `D.phases`, `D.stats.heatmap`, `D.activity_timeline`

### R3-2. Phase 로드맵 (🗓 6개월 여정)

각 Phase 카드:
- **큰 글씨**: `phase.business_label` ("5월: 실기 없이 학습할 수 있는 환경 구축")
- 작게: `phase.name` ("Phase 0 — 시뮬 환경 셋업")
- **이게 완료되면** 영역: `phase.outcome` (강조 박스)
- 진행률 progress bar + 주차별 sub-bar (R2 의 phases[*].weeks)
- 그 phase 의 월별 활동보고서 link (monthly_reports 의 같은 month)
- 보고서 매핑: `phase.report_label`

### R3-3. 🎥 시뮬 시각자료 (NEW)

영상 갤러리:
- `<video controls poster="<poster path>">` × 2 (pick_place, 6dof)
- 각 영상 옆에: `description` (비전공자용 한 줄) + 메트릭 + 다음으로 이어지는 것
- overhead_frame_sequence: CSS scroll-snap carousel (30장)
- 비전공자 영역: "이 영상이 보여주는 것 / 왜 중요한지"

영상 URL: `/static/cop/research/simulation/video/<filename>` (R3-6 의 라우트 필요)

### R3-4. 📅 활동 타임라인 (날짜별 통합)

- 좌측 날짜 axis + 우측 카드 stack
- 각 카드 = 1 날짜:
  - 큰 글씨: `summary` ("시뮬 작업 · 테스트·메트릭")
  - 메트릭: `commit_count`, `self_heal_count` (작은 아이콘)
  - 그날의 sim_task titles (최대 3개)
  - hover → 디테일 (commit 메시지들)
- self-heal 은 작은 🛟 아이콘 + 카운트 (별도 카드 X)
- 비전공자용: 카테고리는 한국어 라벨 (이미 R2 에서 변환됨)

데이터: `D.activity_timeline`

### R3-5. 📋 보고용 자료 (Obsidian 임베드)

- 월별 카드 8개 (4월 v1/v2 + 5~10월)
- 각 카드 클릭 → 마크다운 풀 본문 렌더 (JS lightweight markdown — Hdel template 의 `renderMarkdown` 함수 재사용 가능)
- 인쇄 / PDF 친화 (한 페이지 요약 버튼)
- 우측: 외부 의존 (마감/담당자) + 결정 기록 (timeline)

데이터: `D.monthly_reports`, `D.blockers`, `D.decisions`

### R3-6. hermes-mark static route 추가

영상/이미지 serve. `/static/cop/<path>` → CoP repo 의 상대경로 매핑.

수정 대상: `/Volumes/MARK_DATA/dev/hermes-mark/server/index.ts` 또는 `server/readers/projects-cop.ts` 의 새 export.

패턴 (Fastify):
```ts
import fastifyStatic from '@fastify/static';
import { COP_REPO } from './readers/projects-cop.ts';

app.register(fastifyStatic, {
  root: COP_REPO,
  prefix: '/static/cop/',
  decorateReply: false,
  // 보안: dotfile 차단, 특정 디렉토리만 (research/simulation/video, models/SO-ARM100/media)
});
```

테스트: `curl -sI https://cop-physical-ai.hermesmark.site/static/cop/research/simulation/video/sim_6dof_animation.mp4` → 200 OK.

### R3-7. Sidebar 메뉴 12→5 + 도구 collapsible

현재 (12개) → 새 (5 + 도구 4):

**주요 5개:**
1. 📊 Overview (현재 단계)
2. 🗓 Phase 로드맵
3. 🎥 시뮬 시각자료 **NEW**
4. 📅 활동 타임라인
5. 📋 보고용 자료

**도구 (sidebar collapsible):**
- 샘플 코드 상태
- 분석 (차트)
- 북마크
- 사용가이드 / 사이트 설명

라우트 키 보존 가능한 것:
- `apps` → "Phase 로드맵"
- `daily` → 활동 타임라인 (재구성됨)
- `magazines` → "보고용 자료" (Obsidian 추가)
- `bookmarks/analytics/about/guide` → 도구

신규 라우트:
- `videos` → 시뮬 시각자료
- 옛 `proposals`, `blockers`, `samples`, `decisions` 라우트는 사용 안 함 (도구로 흡수 또는 deprecated)

## 톤 가이드 (필수 준수)

| 영역 | ❌ 너무 기술 | ❌ 너무 아동 | ✅ 적절 |
|---|---|---|---|
| Phase | "MuJoCo 3.x + MJCF + SO-ARM101" | "와! 로봇 친구를 컴퓨터에 만들었어요!" | "5월: 실기 없이도 학습할 수 있는 환경 구축" |
| 진척 | "33 commits across 9 sim docs" | "엄청 많이 작업했어요!" | "이번 달 시뮬 작업 33회 완료 · 다음 ACT 학습 시작" |
| 자가치유 | "self_heal_count_30d: 5" | "5번이나 컴퓨터가 알아서 고쳐줬어요!" | "자동 복구 5회 (시스템이 일시 장애를 스스로 해결)" |

핵심 원칙:
- 숫자에 의미 부여 ("33회" → "33회 완료, 다음은 학습 시작")
- 약어 풀어쓰기 첫 등장 시 ("ACT" → "ACT 학습 (모방학습 알고리즘)")
- 불필요한 과장 X ("성공!", "달성!" 같은 강조 톤 금지)
- 기술 라벨은 *작게* 보존 (검색 가능성)
- 색상: 완료=진초록 ✅, 진행=파랑 🔄, 예정=회색 ⏳ (경고색 yellow/orange/red 금지)

## 운영 정보 (변경 X)

| 항목 | 값 |
|---|---|
| **외부 URL** | https://cop-physical-ai.hermesmark.site/ |
| **API** | /api/projects/cop-physical-ai/data |
| **WS** | wss://.../ws (chokidar 자동 push) |
| **CoP repo** | /Volumes/MARK_DATA/dev/2026-cop-physical-ai |
| **hermes-mark repo** | /Volumes/MARK_DATA/dev/hermes-mark |
| **Obsidian 월별 보고서** | ~/Documents/second-brain/03 Areas/회사문서/CoP_PhysicalAI/ |
| **자동 빌드 시각** | 매일 23:30 (cop_sim_test.py 끝) |
| **PROJECT_SLUG / COP_SLUG** | `cop-physical-ai` |

## 새 세션 시작 시 즉시 실행할 검증 (sanity check)

```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai

# 1. R2 데이터 emit 잘 되고 있는지
python3 -c "
import json
d = json.load(open('dashboard/data.json'))
print('keys:', sorted(d.keys()))
print('D-day:', d['business_kpi']['d_day'])
print('phases:', [(p['id'], p['progress'], p['business_label']) for p in d['phases'][:2]])
print('videos:', [(v['kind'], v['description']) for v in d['videos']])
print('reports:', [r['month'] for r in d['monthly_reports']])
print('timeline[0]:', d['activity_timeline'][0] if d['activity_timeline'] else None)
"

# 2. 외부 도메인 살아있는지
curl -sI https://cop-physical-ai.hermesmark.site/ | head -2

# 3. 마지막 커밋 (R2 작업)
git log --oneline -3
```

## R3 진행 순서 (사용자 결정 필요)

다음 중 우선순위:
- **(A) R3-1 + R3-2 부터** — Overview + Phase 로드맵 (가장 핵심, 비전 + 진척 시각화)
- **(B) R3-3 부터** — 시뮬 시각자료 + R3-6 static route (시각 임팩트 가장 큼)
- **(C) R3-7 부터** — Sidebar 압축 (UI 정리 우선, 컨텐츠는 그 후)

권장: **(A) → (B/R3-6) → (C) → (R3-4) → (R3-5)** 순서 (점진적 확장, 사용자가 매 단계 확인 가능).

## 새 세션 첫 프롬프트 예시

> "/Volumes/MARK_DATA/dev/2026-cop-physical-ai/dashboard/R3_PLAN.md 읽고 R3-1 (Overview) + R3-2 (Phase 로드맵) 부터 진행. 톤 가이드 지키면서 — 비즈니스 outcome 우선, 기술 라벨은 작게."

또는 미리 보고 우선순위 정한 경우:

> "R3_PLAN.md 의 R3-3 (시뮬 시각자료) + R3-6 (hermes-mark static route) 부터 진행. 영상 임팩트 먼저 보고 싶음."
