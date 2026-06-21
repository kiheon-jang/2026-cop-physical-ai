# ACT W3 D6 status 점검 — 2026-06-20 (토요일)

## 컨텍스트
PHASE_ROADMAP Phase 1 W3 (6/15~6/21) ACT 학습 항목 3종 미진입 6일 연속:
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`)
- [ ] nohup 백그라운드로 epoch 100 학습 실행
- [ ] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log 진행률 기록

## 정적 점검 (Bash `ls` 통과)

- `scripts/train_act.py -rwxr-xr-x` (실행권한 보유, 6/12 작성 그대로)
- `scripts/start_act_train.sh -rw-r--r--` (실행권한 미부여 유지 — 6/13 작성)
- `scripts/check_act_train.sh -rw-r--r--` (실행권한 미부여 유지 — 6/14 작성)
- `logs/` 부재 — ACT 학습 미시작 20일 연속
- `checkpoints/` 부재 — ACT 학습 미시작 20일 연속
- `data/episodes/meta/info.json` so101 / 200 ep / 12400 frames / fps 30 그대로

## 런타임 점검

- `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; print(mujoco.__version__)"` 본 회차 sandbox "requires approval" 거절 — 20일 연속.
- 학습 손실 N/A, 시뮬 동작 성공률 N/A, CPU/메모리 N/A.

## PHASE_ROADMAP 갱신 판정

W3 첫 두 항목 체크박스 `[ ]` 유지 — 런타임 통과/학습 시작 전까지 변경 보류 (6일차 누적, 6/21 W3 마지막일까지 1일 남음).

## 다음 단계와의 연결

- **6/21 (일) W3 D7 마지막일**: 사용자 수동 절차 통과 시 `check_act_train.sh` status 블록 (`pid=N alive=yes ckpt_count=≥1 log_age_sec<86400`) append + W3 첫 두 항목 `[v]` 일괄 체크. 미통과 시 W4 (6/22~) 진입이 ACT 학습 완료 대기 상태로 변경.
- **6/22 (월) W4 D1**: ACT 학습 완료 대기 + 시뮬 추가 200 에피소드 생성 시작 (`sim_data_collector.py`). Orin Nano SSH 정보 마감일.

## 사용자 수동 1회 절차 (권고 그대로)

```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
chmod +x scripts/*.sh
.venv/bin/python3 scripts/train_act.py --smoke
nohup bash scripts/start_act_train.sh --epochs 100 > logs/act_train.log 2>&1 &
echo $! > logs/act_train.pid
git add -A
git commit -m "📊 [로그] 2026-06-07~20 누적 산출물 — sandbox 20일 차단 해소"
git push origin main
```
