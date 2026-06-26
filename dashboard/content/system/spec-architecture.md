---
doc: spec
id: architecture
title: "기술 구조 및 자동화 파이프라인"
order: 91
screenshot: ""
---
<!-- slide title="레포지토리 구조" -->
## 레포지토리 구조 (핵심 경로)

```
2026-cop-physical-ai/
├── research/simulation/        # 시뮬 작업 마크다운 (view-proposals 데이터 소스)
│   ├── PHASE_ROADMAP.md        # Phase 0~4 체크리스트 (view-apps 데이터 소스)
│   ├── video/                  # 시뮬 영상 + 프레임 시퀀스 (view-videos)
│   └── inference_progress/     # 학습 진척 inference 영상 (view-videos)
├── agent/
│   ├── research-log/           # 일일 연구 로그 (view-daily 데이터 소스)
│   ├── external-dependencies.md # 외부 의존 차단 항목 (view-blockers)
│   └── report-evidence/YYYY-MM/ # 월간 보고용 증거 (view-magazines 보조)
├── research/decisions/         # 아키텍처 결정 기록 (view-decisions)
├── samples/SAMPLE_STATUS.md    # 샘플 코드 상태 테이블 (view-samples)
├── data/episodes/              # LeRobot Dataset v3.0 (영상+parquet)
├── models/SO-ARM100/media/     # 하드웨어 사진 (view-videos)
├── outputs/train/              # ACT 학습 출력 (metrics.jsonl)
├── logs/act_train_metrics.jsonl # ACT 학습 메트릭 (legacy path)
└── dashboard/
    ├── build.py                # 데이터 빌더 (JSON 생성)
    ├── template.html           # UI 템플릿
    ├── site_docs.py            # docs 빌더
    └── content/                # 기능명세·사용가이드 마크다운
```

<!-- slide title="데이터 흐름 — 핵심 소스" -->
## 데이터 흐름

```
PHASE_ROADMAP.md     → build_phase_roadmap()  → data.phases (view-apps, home Gantt)
research/simulation/ → build_sim_tasks()       → data.sim_tasks (view-proposals)
agent/research-log/  → build_daily()           → data.daily (view-daily)
agent/report-evidence/ → build_evidence()     → data.evidence (참고용)
external-dependencies.md → build_blockers()   → data.blockers (view-blockers)
samples/SAMPLE_STATUS.md → build_samples()    → data.samples (view-samples)
research/decisions/  → build_decisions()      → data.decisions (view-decisions)
Obsidian CoP_PhysicalAI/ → build_monthly_reports() → data.monthly_reports (view-magazines)
```

<!-- slide title="데이터 흐름 — 미디어·KPI·docs" -->
```
research/simulation/video/ → build_videos()   → data.videos (view-videos)
models/SO-ARM100/media/ → build_hardware_photos() → data.hardware_photos (view-videos)
outputs/train/       → build_training_metrics() → data.training_metrics (view-videos)
inference_progress/  → build_inference_progress() → data.inference_progress (view-videos)
git log (60일)       → build_activity_timeline() → data.activity_timeline (view-daily)
PHASE_META + phases  → build_business_kpi()  → data.business_kpi (view-home KPI·D-day·진행률)
dashboard/content/   → site_docs.build_site_docs() → data.docs (spec/guide 슬라이드)
```

모든 경로는 `build.py` 실행 환경(로컬 Mac Mini)의 파일시스템을 직접 읽는다. `data.json` 출력 후 hermes-mark 서버가 WebSocket으로 브라우저에 푸시.

<!-- slide title="자동화 스케줄 (KST)" -->
## 자동화 스케줄 (KST 기준)

| 시각 | 작업 | 출력 파일 |
|------|------|-----------|
| 매일 23:00 | Hermes Agent: PHASE_ROADMAP에서 오늘 단계 식별 → MuJoCo 코드 작성/실행 | `research/simulation/*.md`, `samples/training/*.py` |
| 매일 23:30 | 시뮬 테스트 + 메트릭 + `build.py` 실행 → `data.json` 갱신 + WebSocket 푸시 | `agent/research-log/YYYY-MM-DD.md`, `dashboard/data.json` |
| 매일 07:00 | 아침 보고 메일 (4명 발송) + `CHANGELOG.md` 갱신 + git push | 이메일, `CHANGELOG.md` |
| 일요 22:00 | 주간 정리 + 보고용 증거 식별 | `agent/report-evidence/YYYY-MM/INDEX.md` |

자가치유(Self-heal): 매 cron 종료 시 실패 항목 자동 기록(`chore(self-heal)` commit) → 다음 cron에서 자동 재시도.

<!-- slide title="서버·빌드 내부 구조" -->
## 대시보드 서버 구조

hermes-mark(`/Volumes/MARK_DATA/dev/hermes-mark`):
- Fastify 기반 HTTP 서버 + Cloudflare Tunnel(`cop-physical-ai.hermesmark.site`)
- chokidar: `dashboard/data.json` 변경 감지
- WebSocket: 변경 감지 시 연결된 브라우저에 갱신 신호 푸시 → 새로고침 없이 데이터 반영

빌드 모드:
- `--json-only`: `data.json`만 출력(HTML 생략)
- 기본: `dashboard.html` 단일 파일 생성(오프라인 배포용)

## 학습 메트릭 경로

ACT 학습 중에는 `train_act.py`가 epoch마다 다음 경로 중 하나에 metrics를 append:
- `outputs/train/*/metrics.jsonl` (primary)
- `logs/act_train_metrics.jsonl` (legacy)

`build_training_metrics()`는 두 경로를 모두 스캔해 최신 파일을 선택. 파일 없으면 `status="pending"` 반환.

## Alias 관계

`build.py`는 하위 호환을 위해 다음 alias를 유지:
- `data.proposals` = `data.sim_tasks`
- `data.apps` = `data.phases`
- `data.magazines` = `data.evidence`

## site_docs 구조

`dashboard/content/pages/*.md`와 `dashboard/content/system/*.md`를 파싱:
- pages: 각 파일에서 `## 기능명세` / `## 사용가이드` 섹션을 분리 → spec_slides + guide_slides 각 1개씩 생성
- system: `doc: spec` → spec_slides, `doc: guide` → guide_slides에 추가
- `data.docs.spec.slides`, `data.docs.guide.slides` 각각 order 오름차순 정렬
