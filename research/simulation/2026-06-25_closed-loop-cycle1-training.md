# closed-loop 자동수집 1사이클 — 학습 스테이지 (2026-06-25)

> Phase 1 - W4 - **closed-loop 자동수집 1사이클 완주** (PHASE_ROADMAP L162, 6/22~6/30 범위 첫 `[ ]`)
> 야간 전진(수집→학습→측정)은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.
> 본 회차는 STAGE 결과를 검증·문서화·보고했다(파이프라인 재실행 없음).

## 오늘 한 일 (STAGE=학습중)

01:00 드라이버 출력 STAGE=**학습중**. 산출물을 직접 검증하여 무결성·정합성을 확인했다.

- **학습 진행중**: ACT 재학습 pid **20078** alive (`pgrep -lf train_act` 확인).
  - `epoch 85/100`, loss **0.00556** (l1 0.00445, kld 0.000110), MPS(`mps:0`), loss 단조감소 정상.
  - `logs/act_train.log` mtime 01:00:50 = 활성 기록 중. 어제 ETA(~02:00) 대로 진행, 잔여 15 epoch.

- **데이터셋 정합 검증 (중요)**: 학습이 **closed-loop 데이터셋(`data/episodes_cl`)을 올바르게 사용 중**임을 확인.
  - 근거: run2 per-epoch step 수가 **~360–419 step/epoch** (3350 frame ÷ batch 8 ≈ 419) → 50ep closed-loop 규모와 일치.
  - 대조: `logs/act_train.log` L16421~16470 의 config dump(dataset_root=`data/episodes`, **1550 step/epoch**)는
    **run1(6/22 open-loop 200ep) 종료 요약**이며 현재 run2 와 무관. 한 로그파일에 두 런이 append 되어 혼동 소지 있었으나 정합 확인됨.

- **체크포인트 저장 정상**: closed-loop run2 가 epoch_0009~0079 까지 저장 완료.
  - `epoch_0079/model.safetensors` mtime **Jun 25 00:26** (최신, closed-loop).
  - `epoch_0099/model.safetensors` mtime Jun 22 22:27 = run1 open-loop, run2가 아직 epoch 85라 미갱신.
  - ⚠ 디렉터리 mtime(6/21~22)은 `save_pretrained` 가 기존 파일 덮어쓰기만 해 디렉터리 mtime을 안 바꾸기 때문 —
    **파일 mtime 기준으로 보면 정상**. (ls 디렉터리 mtime 만 보면 오해 가능 → 본 문서에 명시.)

- **측정 대기**: `research/simulation/inference_progress/rollout_summary.json` = epoch_0009 / 2 rollout / 0% / 6.4mm,
  mtime 6/24 17:30. 이는 commit `16d2548` 의 **2-rollout 정합 스모크**(대상 epoch_0009 = open-loop baseline)이며
  closed-loop 유효 측정 아님. 학습 완료 후(~02:20) 드라이버 측정 스테이지가 신규 closed-loop 모델 10-rollout 측정 수행 예정.

## 검증 방법

- `pgrep -lf train_act` → pid 20078 alive
- `tail logs/act_train.log` → epoch 85/100, loss 0.00556 단조감소
- `awk 'NR>16470 && /checkpoint_saved/'` → run2 epoch_0009~0079 저장 확인
- `stat -f '%Sm' .../model.safetensors` → epoch_0079 파일 mtime 00:26 (closed-loop 신선)
- run2 step/epoch ≈ 419 (=episodes_cl 규모) vs run1 1550 (=episodes) 대조로 데이터셋 정합 확정

## 자가치유

없음. 수집✓·학습 정상 진행·산출물 무결·데이터셋 정합·체크포인트 저장 정상, 에러 없음.
(checkpoint 디렉터리 mtime / 두 런 append 혼동은 실제 결함이 아니라 관측 함정 → 문서로 명확화만.)

## 다음 단계와의 연결

학습 완료(~02:20) → **다음 cron 회차에서 드라이버 측정 스테이지**가 closed-loop 모델 10-rollout 측정 →
`rollout_summary.json` 갱신. 유효 Pick 성공률 확보 시 PHASE_ROADMAP L162 `[v]` 클로즈 + Phase 1 W4 완료 기준(🔄) 닫기.
오늘은 학습 미완(epoch 85/100)이므로 L162 는 `[ ]` 유지.
