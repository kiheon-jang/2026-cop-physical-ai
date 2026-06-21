# ACT W3 D2 — 학습 status 점검 (2026-06-16)

## 대상 단계

PHASE_ROADMAP W3 (6/15~6/21):
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`)
- [ ] nohup 백그라운드로 epoch 100 학습 실행
- [ ] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log에 진행률 기록

본 회차(6/16) 목표: 어제(6/15) "다음 단계" 항목 — `check_act_train.sh` status 블록 append. 사용자 수동 절차(chmod +x → smoke → start_act_train.sh) 통과 확인 시 PHASE_ROADMAP 첫 두 `[ ]` → `[v]` 일괄 체크.

## 본 회차 점검 결과 (정적, sandbox 한계 내)

- `logs/` 디렉터리: 미존재 (`ls logs/` → No such file or directory)
- `checkpoints/` 디렉터리: 미존재 (`ls checkpoints/` → No such file or directory)
- `scripts/start_act_train.sh` 권한: `-rw-r--r--` (실행 비트 없음, 6/13 작성 후 그대로)
- `scripts/check_act_train.sh` 권한: `-rw-r--r--` (실행 비트 없음, 6/14 작성 후 그대로)
- `scripts/train_act.py` 권한: `-rwxr-xr-x` (6/12 cpu/workers 분기 추가 후 그대로)

→ 사용자 수동 절차 **미시행 상태 그대로**. ACT 학습 미시작.

## 런타임 점검 시도

- `chmod +x scripts/start_act_train.sh scripts/check_act_train.sh` → sandbox "requires approval" 거절 (15일+1 연속, 6/2~6/16)
- `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; print(...)"` → sandbox "requires approval" 거절 (15일+1 연속)
- `bash scripts/check_act_train.sh` 미시도 (chmod 미통과로 의미 없음)

## PHASE_ROADMAP W3 체크박스

- 첫 두 항목 `[ ]` 유지. 런타임 검증 통과 전까지 변경 보류. (6/15 결정 그대로 연장)

## 연결 — 다음 단계

- **사용자 수동 (오늘~내일까지)**: 6/15 research-log "다음 단계" 블록 그대로 유효.
  1. `chmod +x scripts/start_act_train.sh scripts/check_act_train.sh`
  2. `.venv/bin/python3 scripts/train_act.py --smoke` 통과 확인
  3. `bash scripts/start_act_train.sh --epochs 100` 백그라운드 실행
  4. PHASE_ROADMAP W3 첫 두 `[ ]` → `[v]` 일괄 체크 후 `git add -A && git commit -m "..." && git push`
- **2026-06-17 (수) W3 D3 nightly**: 사용자 절차 통과 가정 시, `check_act_train.sh` 표준 status 블록 (`pid=N alive=yes ckpt_count=≥1 log_age_sec<86400`) 을 당일 research-log "## ACT 학습 진행률" 섹션에 append. 통과 미확인 시 동일 패턴 반복 (15일+2).
- **2026-06-22 (월) W4 D1**: ACT 학습 완료 대기 + 시뮬 추가 200 에피소드 생성 시작 (`sim_data_collector.py`).

## 근본 원인

`agent/external-dependencies.md` 우선순위 3 — [장기헌] Claude Code v3.2 harness allowlist 점검 블로커. 15일+1 연속 (6/2 누적 시작 기준). 모든 nightly 런타임 실행 차단.
