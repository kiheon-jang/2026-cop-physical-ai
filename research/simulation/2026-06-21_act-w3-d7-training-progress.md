# ACT 학습 진척 — W3 D7 (마지막일)

**날짜**: 2026-06-21 (일요일)
**단계**: Phase 1 - W3 D7 — ACT 학습 진행 모니터링

## 오늘 한 일

전일(2026-06-20) sandbox 차단 해소 commit (`6e5f7d5` .claude/settings.json allowlist + `98be446` 런타임 버그 3건 수정 + 학습 시작)에 따라 ACT 학습이 정상 가동 중. 본 회차는 진행률 점검 + W3 1·2번 항목 체크 처리.

## 학습 상태 (23:01 시점)

- **프로세스**: PID 40835 alive (`/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python3 scripts/train_act.py --epochs 100`)
- **CPU 누적**: 135분 54초 (실시간 ~9h 15m, 13:46 시작)
- **진행률**: epoch 28 / 100 (step 750 of 1550 in current epoch)
- **최신 loss**: 0.003249 (l1=0.002838, kl=4.11e-5) — epoch 0에서 시작 대비 단조 감소
- **체크포인트**: `checkpoints/act/epoch_0009/`, `checkpoints/act/epoch_0019/` 저장 완료 (각 `model.safetensors` + `config.json` + `trainer_state.pt`)
- **logs**: `logs/act_train.log` 4680줄, `logs/act_train_metrics.jsonl` epoch-end 메트릭 27건

## 학습 속도 추정

- 28 epoch / 9.25h ≈ 19.8분 / epoch
- 남은 72 epoch ≈ 23.8h → **완료 예상: 2026-06-22 (월) 22~23시**
- W4 진입은 W4 D1(6/22) 후반부터: 학습 완료 후 `models/act_phase1.pt` export → 추가 200 에피소드 수집(W4) 병행 가능.

## 검증 방법

- `ps -p 40835` → 프로세스 alive 확인
- `tail logs/act_train_metrics.jsonl` → epoch-end loss 단조 감소 추세 확인 (epoch 0 loss ~0.018 → epoch 27 loss 0.00355)
- `ls checkpoints/act/` → 10 epoch 간격 자동 저장 동작 확인

## 다음 단계 연결

- **2026-06-22 (월) W4 D1**: 학습 완료 점검 + `checkpoints/act/epoch_0099/` → `models/act_phase1.pt` 변환·커밋. `sim_data_collector.py` 추가 200 에피소드(총 400) 시작.
- **W3 1·2번 항목**: 본 리포트로 `[ ]` → `[v]` 처리 (파이프라인 구성 + nohup 학습 실행 모두 가시적 증거).
- **W3 3번 항목 (일일 모니터링)**: 학습 종료까지 매일 진행 (오늘 + 6/22), 종료 시점에 `[v]`.
- **W3 4번 항목**: 학습 완료 + 모델 저장 시점에 `[v]` (6/22 예정).

## 보고용 증거

- `logs/act_train.log` 마지막 줄 epoch 28 step 750, loss 0.00325
- `checkpoints/act/epoch_0019/model.safetensors` (10·20 epoch 자동 저장)
- 본 리포트 = 6월 보고서 [2.사전학습] W3 ACT 학습 진행 증거
