# ACT W3 D4 status 점검 — 2026-06-18 (목)

## 오늘 단계

Phase 1 - W3 D4 — ACT 학습 status 점검 (6/15 D1 ~ 6/17 D3 사용자 수동 절차 미시행 누적 → D4 동일 패턴 반복).

PHASE_ROADMAP W3 (6/15~6/21) 대상 항목:
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`)
- [ ] nohup 백그라운드로 epoch 100 학습 실행
- [ ] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log 진행률 기록

## 정적 점검 (Glob 통과)

- `scripts/` 4종 그대로: `build_report_pptx.py`, `train_act.py`, `start_act_train.sh`, `check_act_train.sh` (6/13 D1 작성분 변경 없음).
- `logs/` **미존재** — 학습 미시작 재확인.
- `checkpoints/` **미존재** — 학습 미시작 재확인.
- `data/episodes/` 50 에피소드 (Phase 0 W4 산출물) 그대로.

## 런타임 점검

- 런타임 실행 0건. `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; ..."` 본 회차 Bash sandbox "requires approval" 거절 — **16일 연속**. `.venv` 심볼릭 링크 대상 (`/Users/markmini/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14`) 이 working-dir 밖이라 sandbox 가 차단.
- `chmod +x scripts/*.sh` 본 회차 sandbox 거절 — 16일 연속. `start_act_train.sh` / `check_act_train.sh` 실행 비트 미부착 추정 그대로.
- `bash scripts/check_act_train.sh` 본 회차 미시도 (chmod 미통과로 의미 없음).

## PHASE_ROADMAP 갱신

- W3 첫 두 `[ ]` 체크박스 변경 **보류** — 런타임 통과 전까지 `[ ]` 유지. 4일차 누적.

## 자가치유 액션

- [자가치유] `.venv/bin/python3` 런타임 호출 sandbox 거절 (16일 연속).
- [자가치유] `chmod +x scripts/*.sh` sandbox 거절 (16일 연속).
- [자가치유] Obsidian 미러 `cp ... 00_AI_Wiki/CoP_PhysicalAI/2026-06/` working-dir 밖 쓰기 sandbox 차단 (16일 연속) — 사용자 수동 동기화 필요.
- [자가치유] `git add` / `commit` / `push` mutation 차단 예상 — 6/7~6/17 미커밋 산출물 위에 본 일자 신규 2건 (`agent/research-log/2026-06-18.md` + 본 파일) append. 누적 미커밋 약 24건.

## 다음 단계 연결

- **사용자 수동 (즉시 1회)**: `chmod +x scripts/*.sh && .venv/bin/python3 scripts/train_act.py --smoke && bash scripts/start_act_train.sh --epochs 100` → 그 시점에서 PHASE_ROADMAP W3 첫 두 `[ ]` → `[v]` 일괄 체크 + `git add -A && git commit -m "📊 [로그] 2026-06-07~18 누적 산출물 — sandbox 16일 연속 차단 해소" && git push origin main` 1회 일괄 처리.
- **2026-06-19 (금) W3 D5 nightly**: 사용자 절차 통과 가정 시 `check_act_train.sh` 표준 status 블록 (`pid=N alive=yes ckpt_count=≥1 log_age_sec<86400`) 을 당일 research-log "## ACT 학습 진행률" 섹션에 append. 미통과 시 본 D4 패턴 반복.
- **2026-06-22 (월) W4 D1**: ACT 학습 완료 대기 + 시뮬 추가 200 에피소드 생성 시작 (`sim_data_collector.py`).

## 보고용 증거 후보

- [ ] 본 파일 — W3 D4 status 점검 + sandbox 16일 연속 블로커 누적. 6월 보고서 [2.사전학습] W3 일일 운영 절차 증거.
