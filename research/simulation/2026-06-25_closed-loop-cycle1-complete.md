# closed-loop 자동수집 1사이클 완주 — 2026-06-25

> Phase 1 - W4 - **closed-loop 자동수집 1사이클 완주** (PHASE_ROADMAP L162)
> 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 수집→학습→측정 전 구간을 처리.
> 본 회차(sim-env 에이전트)는 STAGE=측정 결과를 문서화·동기화·보고. 파이프라인 재실행 없음.

## 무엇을 했는가

6/24 23:00 시점 "학습중"이던 closed-loop 1사이클이 **완주**되어, ACT 모델의 실제
Pick 성공률이 처음으로 측정되었다. 사이클 전 구간 결과:

| 스테이지 | 결과 | 증거 |
|---|---|---|
| **수집** | 성공 50/50 (시도 55회, **yield 91%**) | `logs/cop_data_collect.log` → `data/episodes_cl` (3350 frame, 30fps, so101, LeRobot v3.0) |
| **학습** | ACT 100 epoch 완료, final loss **0.004564** (l1 0.00377 / kld 7.98e-5) | `logs/act_train.log` "학습 100 epoch 완료", wall_clock 32711s(≈9.1h), pid 20078 종료 |
| **측정** | **10 rollout 중 7 성공 = 성공률 70%**, median lift **43.7mm** | `research/simulation/inference_progress/rollout_summary.json` (mtime 23:00) |

### 측정 상세 (rollout_summary.json)
- checkpoint: `checkpoints/act/epoch_0099` (model.safetensors mtime **02:17** → closed-loop 신선)
- scene: `scene_grasp_pads.xml`, lift_threshold 0.04m(40mm), device cpu, wall 13.6s
- 성공 7/10 (lift 43.7~45.6mm), 실패 3개(rollout 2/5/8, lift 3.7~6.9mm = 들어올리기 실패)
- 산출 영상: `inference_progress/inference_epoch_0099_20260625.mp4`

## 어떻게 검증했는가

1. **학습 완료 확인**: `act_train.log` 마지막 레코드 epoch 99 + "학습 100 epoch 완료", pid 20078 DEAD.
2. **closed-loop 모델인지 확인**: `epoch_0099/model.safetensors` mtime = 2026-06-25 02:17.
   6/24 16:52 수집 종료 → 같은 날 학습 시작 → 02:17 종료. 6/22 open-loop baseline(어제 우려한
   stale 체크포인트)이 아니라, `COP_DATASET_ROOT=data/episodes_cl` 로 학습된 신규 모델임이
   타임스탬프로 확정. (save_pretrained 가 epoch_0099 디렉터리를 덮어쓰므로 같은 경로명 유지)
3. **측정 신선도**: `rollout_summary.json` mtime 23:00 = 드라이버 측정 스테이지 산출. 어제의
   2-rollout 정합 스모크(0%/6.4mm, epoch_0009 baseline)가 아니라 **--rollouts 10 정식 측정**.

→ **open-loop 0% → closed-loop 70%**. 6/22~23 규명한 "단일 회전조 호 스윕 + open-loop expert"
근본결함의 해법(closed-loop)이 데이터→학습→정책까지 end-to-end로 관통함을 처음 입증.

## 관찰 / 한계

- **정책 70% < expert 88%(FORCE6)/75%(FORCE3)**: ACT 정책이 closed-loop expert 데모를 완전히
  재현하진 못함(모방 격차). 실패 3건은 전부 lift<7mm(접근 후 들어올리기 실패) 패턴.
- **Sim 90%+ 목표와의 간극**: 메모리 grasp-sim-strategy 기준 Sim2Real 의미를 가지려면 sim 90%+.
  현 70%는 1사이클 결과 — 데이터량 증대(50→200ep)/epoch/씬 다양화로 끌어올릴 후속 여지.
- 큐브 30mm 진행(50mm 미적용)은 기존 결정 유지(grasp-rootcause-correction).

## 다음 단계로의 연결

- 이 결과로 PHASE_ROADMAP L162 `[ ]`→`[v]` 클로즈, Phase 1 W4 완료 기준의 🔄(시뮬 Pick 성공률
  확인 중) 항목을 **70% 측정치로 닫음**.
- 남은 Phase 1 항목은 L166 "Orin Nano 배포"뿐 → 외부 의존(장기헌 SSH, external-dependencies.md)
  미수신으로 이연 유지.
- **7월 Phase 2(Sim2Real)** 진입 전, sim 성공률 향상(데이터 증대/씬 다양화)이 자연스러운 후속.
