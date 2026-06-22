# ACT 100 epoch 학습 완료 — 2026-06-22

## 무엇을 했나

W3 마지막 미체크 항목 2건 처리:
1. `logs/act_train.log` / `logs/act_train_metrics.jsonl` 확인 → 학습 종료 확인
2. `checkpoints/act/epoch_0099/model.safetensors` → `models/act_phase1.pt` 복사

## 검증

- PID 40835: 23:00 시점 **종료** (`ps -p 40835` → no process).
- 메트릭 라인 수: 100 (`wc -l logs/act_train_metrics.jsonl`).
- 마지막 epoch (99) loss: **0.001202** (l1 0.001007, kld 1.95e-5).
- wall_clock_sec: 117647 ≈ **32.7시간** (6/21 13:46 → 6/22 22:27).
- 체크포인트: `epoch_0009 ... epoch_0099` 10개 모두 존재 (`model.safetensors` 320MB + `config.json` + `trainer_state.pt`).
- 산출:
  - `models/act_phase1.pt` (320MB, gitignored — `.gitignore:30 models/*.pt`)
  - `models/act_phase1.config.json` (1.5KB, 커밋됨)

## loss 곡선 요약 (epoch별 마지막 step)

| epoch | loss |
|---|---|
| 0 | 0.0177 |
| 27 | 0.00355 |
| 50 | 0.00184 |
| 75 | 0.00135 |
| 99 | 0.00120 |

단조 감소, 발산 없음. KLD 항 일정 (~2e-5) → posterior 안정.

## 다음 단계와의 연결

- PHASE_ROADMAP W3 4개 항목 모두 `[v]` 완료.
- 다만 본 모델로 측정한 **Pick 성공률 0%** (6/22 grasp-task-root-cause.md 참조) → 데이터 자체에 성공 시연 0개 → 모델 한계 아님.
- W4 핵심 작업: **시뮬 grasp 정상화** (IK 기반 cube-aware expert + 큐브 축소). 워킹트리 `scripts/_grasp_*.py` 14종 진행중.
- Orin Nano SSH 정보 (장기헌, 6/22 마감) 미수신 → 배포 건너뜀. 모델 파일은 로컬 보존.

## 모델 배포 노트

`models/act_phase1.pt` 는 320MB 이므로 git push 불가 (`models/*.pt` gitignore + GitHub 100MB 한도).
- 진정한 모델 아티팩트는 `checkpoints/act/epoch_0099/` (역시 gitignored, 로컬 보존).
- 재현 가능성: `logs/act_train_metrics.jsonl` (100 epoch loss) + `models/act_phase1.config.json` (모델 구조) 만 git 커밋.
- Orin 배포 시: 로컬 scp 또는 별도 모델 저장소 필요.
