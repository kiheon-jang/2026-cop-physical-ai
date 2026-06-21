# Phase 1 W4 D1 — ACT 학습 진행 모니터링 (2026-06-22)

## 작업 내용

PHASE_ROADMAP W3 항목 `[ ] 매일 크론이 logs/act_train.log 마지막 줄 확인 → research-log에 진행률 기록` 의 6/22 회차 진척 보고.

W4 (6/22~6/30) 첫날이지만 W3 ACT 학습이 6/22 자정 시점 epoch 34 진행 중이므로 학습 모니터링이 우선. W4 1번 (`sim_data_collector.py` 추가 200 에피소드) 은 학습 완료 후 (예상 2026-06-23 자정) 진입.

## 학습 프로세스 상태 (2026-06-22 01:02 KST 기준)

- PID **40835** alive — `scripts/train_act.py --epochs 100`
- CPU 누적: **163분 43초**
- 실시간 경과: 시작 2026-06-21 13:46 → 약 **11h 16m** 경과
- 진행률: **epoch 34 / 100** (현재 epoch 내 step ~240/1550)
- 직전 epoch 완료 33: loss=0.002725, l1=0.002396, kl=3.28e-5 (1247.0초 소요)
- epoch-end metrics jsonl: 34 줄 (`logs/act_train_metrics.jsonl`)

## 학습 곡선 추이

| epoch | loss | l1 | kl | epoch 소요 (sec) |
|---|---|---|---|---|
| 29 | 0.003136 | 0.002740 | 3.95e-5 | 1289.3 |
| 30 | 0.003255 | 0.002889 | 3.65e-5 | 1305.3 |
| 31 | 0.002924 | 0.002562 | 3.62e-5 | 1286.6 |
| 32 | 0.002932 | 0.002583 | 3.49e-5 | 1261.6 |
| 33 | 0.002725 | 0.002396 | 3.28e-5 | 1247.0 |

- loss 감소세 유지 (epoch 0 0.0177 → epoch 33 0.00272, 약 -85%).
- 평균 epoch 소요 **~20.9분/epoch**. 남은 66 epoch ≈ **23h** → **완료 예상 2026-06-23 (화) 00~01시 KST**.
- 체크포인트 진척: `checkpoints/act/epoch_{0009, 0019, 0029}` 모두 저장됨 (10 epoch 주기).

## 검증

```bash
ps -p 40835                   # 프로세스 alive 확인
tail -30 logs/act_train.log   # epoch 34 step 240 진행 중 확인
wc -l logs/act_train_metrics.jsonl  # 34 줄 (epoch 0~33 완료)
ls checkpoints/act/           # epoch_0009, epoch_0019, epoch_0029
```

## 관찰

- 어제 23:30 회차 시뮬 회귀 테스트 3종 병행에도 학습 정상 진행 (병렬 CPU 경합 제한적).
- 단, 학습 가동 중 `sim_data_collector.py` 200 에피소드 신규 수집은 CPU 경합 + 학습 epoch 속도 저하 우려로 **6/23 학습 완료 후 진입** 결정.
- 워킹트리 dirty 항목: 서브모듈 2종 (`SO-ARM100`, `models/SO-ARM100`) 만 변동 — Hard rule "submodule add 금지"로 본 회차도 미반영.

## 다음 단계 연결

- **6/22 23:00 회차 (다음 크론)**: 학습 진척 재확인. epoch ~40 도달 예상. epoch_0039 체크포인트 존재 확인.
- **6/23 (화) — 학습 완료 예상**: W3 #3·#4 모두 `[v]`. `checkpoints/act/epoch_0099/model.safetensors` → `models/act_phase1.pt` 변환 + commit. W4 #1 `sim_data_collector.py` 추가 200 에피소드 백그라운드 시작.

## 보고용 증거 후보

- [ ] `logs/act_train_metrics.jsonl` (34 epoch end-loss) — 6월 보고서 [2.사전학습] 학습 단조 감소 증거.
- [ ] `checkpoints/act/epoch_0029/model.safetensors` — 중간 체크포인트 정상 저장 증거.
