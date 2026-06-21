# Phase 1 W3 D1 — ACT smoke + nohup 학습 시작 시도 (2026-06-15)

## 컨텍스트

PHASE_ROADMAP W3 (6/15~6/21) 첫 두 항목:
- [ ] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`) — 코드 자체는 6/8~6/12 작업으로 구현 완료, smoke 미통과 상태로 6/14 까지 보류.
- [ ] nohup 백그라운드로 epoch 100 학습 실행 (`scripts/start_act_train.sh`)

6/14 research-log "다음 단계" 항목이 본 회차(6/15 W3 D1) 의 정확한 절차를 명시:

1. `chmod +x scripts/start_act_train.sh scripts/check_act_train.sh` (사용자 권장)
2. `.venv/bin/python3 scripts/train_act.py --smoke` 통과 검증
3. `bash scripts/start_act_train.sh --epochs 100` 백그라운드 학습 시작
4. PHASE_ROADMAP W3 첫 두 항목 `[v]` 체크
5. 익일부터 23:00 nightly 가 `scripts/check_act_train.sh` 호출 → research-log "ACT 학습 진행률" 섹션에 append

## 본 회차 실행 결과

### 정적 점검 (sandbox 무관, 통과)

- `scripts/train_act.py` (line 1~471): main() 진입점, `--smoke` 분기 (line 429~), `effective_device=cpu / effective_workers=0` 강제 (line 443~444), `max_epochs=1 / max_steps=2` (line 437) — smoke 의도대로 1 epoch 2 step CPU 실행 설계 일치.
- `scripts/start_act_train.sh` (line 1~86): `.venv/bin/python3` 절대경로 (line 24), 최신 ckpt 디렉터리 자동 `--resume-from` (line 58~69), nohup 백그라운드 + `logs/act_train.pid` 기록 (line 81~85), 이중 실행 방지 `kill -0` 검사 (line 38~45). 본 회차 `logs/` 디렉터리 부재 → cold start 로직 정상 동작 예정.
- `scripts/check_act_train.sh` (line 1~87): wrapper 짝. PID/체크포인트/로그 신선도 3축 → exit 0/1/2/3. ckpt glob 패턴 `epoch_*/` (line 47, 51) 이 train_act.py `_save_checkpoint` (line 258) 의 `f"epoch_{epoch:04d}"` 와 정합 — 6/14 정합성 점검 결과 그대로 유효.
- `data/episodes/` (LeRobot Dataset 폴더): `data/`, `images/`, `meta/`, `videos/` 4 하위 폴더 존재. 5월 W4 50 ep + 6월 W1-2 150 ep 추가 총 200 에피소드 (PHASE_ROADMAP 6월 W1-2 첫 항목 `[v]` 기록 일치). DataLoader 부팅 가능 상태.

### 런타임 점검 (sandbox 차단 — 미수행)

- [자가치유] `chmod +x scripts/start_act_train.sh scripts/check_act_train.sh` — sandbox "This command requires approval" 거절. 14일+2 연속. 두 스크립트 모두 `-rw-r--r--` 상태 유지. 사용자 수동 1회 필요.
- [자가치유] `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 scripts/train_act.py --smoke` — sandbox 거절. 14일+2 연속. smoke 통과 여부 본 회차 미확정.
- [자가치유] `bash scripts/check_act_train.sh` — sandbox 거절. 본 회차 학습 미시작 상태 (PID 파일 없음, ckpt 디렉터리 없음 → exit 1 예상) 는 정적 확인만 (`ls: checkpoints/: No such file or directory`, `logs/` 미존재).

## 어떻게 검증했나

- 정적: 위 3 파일을 직접 Read tool 로 읽어 line 단위 정합성 확인. ckpt 디렉터리 글로브 패턴 (`epoch_*/`) 이 wrapper(start_act_train.sh:59) ↔ check(check_act_train.sh:47,51) ↔ train_act.py(_save_checkpoint:258) 3축 모두 일치.
- 런타임: 본 회차 검증 불가. 사용자 수동 절차 통과 후 익일(2026-06-16 W3 D2) 23:00 nightly 의 `check_act_train.sh` 출력으로 간접 확인 예정.

## 다음 단계와의 연결

본 회차에서 PHASE_ROADMAP W3 첫 두 항목 `[v]` 체크는 보류 — smoke 통과 + nohup 시작 모두 본 회차 sandbox 미달성. 사용자 수동 절차 통과 후 익일 nightly 가 `check_act_train.sh` 의 `pid=N alive=yes ckpt_count=≥1` 라인을 확인하는 시점에서 두 항목 일괄 `[v]`. 그 사이 nightly 는 매일 동일한 "smoke 시도 → sandbox 거절 → 정적 점검만" 패턴 반복 — 신규 코드 변경 없음.

## 사용자 수동 처리 (블로커 해소용)

```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
chmod +x scripts/start_act_train.sh scripts/check_act_train.sh
.venv/bin/python3 scripts/train_act.py --smoke   # 통과 시 다음 줄
bash scripts/start_act_train.sh --epochs 100
bash scripts/check_act_train.sh                  # pid=N alive=yes 확인
```

통과 시 PHASE_ROADMAP W3 첫 두 `[ ]` → `[v]` 체크 후 commit.
