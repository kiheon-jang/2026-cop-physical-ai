# ACT W3 D3 status 점검 — 2026-06-17 (수)

## 단계

Phase 1 - W3 D3 (6/15~6/21 윈도우 3일차) — ACT 학습 status 점검.
PHASE_ROADMAP W3 대상:
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`)
- [ ] nohup 백그라운드로 epoch 100 학습 실행
- [ ] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log에 진행률 기록

## 한 일

### 정적 점검 (도구 허용)

- `git log --oneline -5` — 통과. 최근 커밋 5건 모두 `📝 [히스토리]` 일일 자동 커밋. 어제 시점 이후 `[시뮬]` prefix 신규 커밋 없음 — 사용자 수동 절차 미시행 또는 결과 미커밋.
- `ls scripts/ logs/ checkpoints/` — `scripts/` 7개 파일 존재 (`train_act.py`, `start_act_train.sh`, `check_act_train.sh`, `build_report_pptx.py`, `daily-report`, `weekly-report`). `logs/` `checkpoints/` 디렉터리 **미존재**. ACT 학습 미시작 상태 그대로.
- `git status --short` — 워킹트리에 6/7~6/16 research-log 10건 + 6/7~6/16 시뮬 리포트 10건 + `scripts/` 신규 3건 (`train_act.py`, `start_act_train.sh`, `check_act_train.sh`) + 6월 daily-reports 9건 + 수정된 4종 (`.gitignore`, `agent/external-dependencies.md`, `agent/report-evidence/2026-06/INDEX.md`, `samples/training/sim_pick_place.py`, `samples/training/sim_data_collector.py`) 미커밋 상태 — 어제 16회차 시점과 동일.

### 런타임 점검 (도구 차단)

- `chmod +x scripts/start_act_train.sh scripts/check_act_train.sh` — Bash sandbox "requires approval" 거절 (15일+2 연속). 두 스크립트 `-rw-r--r--` 그대로 유지 → bash 실행 비트 미부착 → `bash scripts/check_act_train.sh` 호출 시 권한 오류 예상.
- `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; print(mujoco.__version__)"` — Bash sandbox "requires approval" 거절 (15일+2 연속). `.venv` 심볼릭 링크 대상 (working dir 밖)이 sandbox 정책에 미allowlist 상태로 추정.

## 어떻게 검증했나

- 정적 점검 3종 (`git log`, `git status`, `ls`) 통과 확인 → ACT 학습 미시작 상태 변경 없음 확정.
- 런타임 점검 2종 (`chmod`, `.venv/python3`) 차단 확인 → 15일+2 연속 sandbox 블로커 누적.
- 메트릭 수집 없음 — `logs/act_train.log` 미존재로 `tail -n 3` 불가, `check_act_train.sh` 호출 의미 없음.

## 다음 단계와 연결

- **사용자 수동 절차 (어제 권고 유지)**: `chmod +x scripts/*.sh` → `train_act.py --smoke` → `start_act_train.sh --epochs 100` nohup 백그라운드 실행. 1회 완료 시 PHASE_ROADMAP W3 첫 두 `[ ]` → `[v]` 일괄 체크 + commit.
- **W3 D4 (2026-06-18, 목) nightly**: 사용자 수동 절차 완료 가정 시 `bash scripts/check_act_train.sh` 호출 → 표준 status 블록 (`pid=N alive=yes ckpt_count=≥1 log_age_sec<86400`) research-log 에 append. 미완료 시 본 D3 패턴 그대로 반복.
- **W4 D1 (2026-06-22, 월)**: ACT 학습 완료 대기와 병행해 `sim_data_collector.py` 추가 200 에피소드 생성 착수 — 6월 PHASE_ROADMAP W4 첫 항목.

## 보고용 증거

- `research/simulation/2026-06-17_act-w3-d3-status-check.md` (본 파일) — W3 D3 status 점검, sandbox 블로커 15일+2 연속 누적 기록. 6월 보고서 [2.사전학습] W3 일일 운영 절차 증거.
