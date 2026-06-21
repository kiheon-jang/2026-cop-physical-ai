# ACT 학습 W3 D5 status 점검 — 2026-06-19 (금요일)

## 무엇을 했나

PHASE_ROADMAP Phase 1 W3 (6/15~6/21) 5일차 status 점검. 사용자 수동 절차(`chmod +x scripts/*.sh && bash scripts/start_act_train.sh --epochs 100`) 미시행 가정 하에서, sandbox 차단으로 인한 런타임 메트릭 0건 상태를 정적으로 재확인.

W3 대상 항목:
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`) — 파일 존재, smoke 미통과
- [ ] nohup 백그라운드로 epoch 100 학습 실행 — 미시작
- [ ] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log 진행률 기록 — `logs/` 미존재

## 어떻게 검증했나

정적 점검 (Bash `ls` 통과):
- `scripts/`: `build_report_pptx.py`, `train_act.py -rwxr-xr-x`, `start_act_train.sh -rw-r--r--`, `check_act_train.sh -rw-r--r--`, `daily-report/`, `weekly-report/` — 6/14 이후 변경 없음.
- `logs/`: **No such file or directory** — ACT 학습 미시작 18일 연속.
- `checkpoints/`: **No such file or directory** — 동일.

런타임 점검 (sandbox 거절):
- `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; ..."` → "This command requires approval". `.venv/bin/python3` → `~/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14` 심볼릭 링크 대상이 working-dir 밖 → sandbox allowlist 밖. 18일 연속 동일 패턴.
- `git add agent/research-log/2026-06-18.md` → "This command requires approval". mutation 차단 18일 연속.

연속 차단 기록: 6/7~6/19 = **13일 연속 (sandbox 누적 18일째)**. 워킹트리 미커밋 산출물 누적 ~44건 (research-log 13, 시뮬 리포트 13, scripts/ 3, daily-reports 11, 수정 4종).

## 다음 단계와의 연결

- **사용자 1회 수동 절차** (즉시): `cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai && chmod +x scripts/*.sh && .venv/bin/python3 scripts/train_act.py --smoke && bash scripts/start_act_train.sh --epochs 100 &` 백그라운드 실행 → 이 시점에서 PHASE_ROADMAP W3 첫 2개 `[ ]` → `[v]` 일괄 체크 + `git add -A && git commit -m "📊 [로그] 2026-06-07~19 누적 산출물 + sandbox 18일 연속 차단 해소" && git push origin main` 일괄 처리.
- **2026-06-20 (토) W3 D6 nightly**: 사용자 절차 통과 시 `check_act_train.sh` 표준 status 블록 (`pid=N alive=yes ckpt_count=≥1 log_age_sec<86400`) 을 당일 research-log "## ACT 학습 진행률" 섹션에 append. 미통과 시 본 D5 패턴 반복 (6/21 W3 마지막일).
- **2026-06-22 (월) W4 D1**: ACT 학습 진행 중 + 시뮬 추가 200 에피소드 생성 시작 (`sim_data_collector.py`). Orin Nano SSH 정보 마감일과 일치.
