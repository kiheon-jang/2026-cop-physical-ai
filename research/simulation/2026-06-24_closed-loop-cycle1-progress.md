# Closed-loop 자동수집 1사이클 — 진행 (수집✓ → 학습중 → 측정대기)

> **날짜**: 2026-06-24 (수)
> **Phase**: Phase 1 - W4 - "closed-loop 자동수집 1사이클 완주" (PHASE_ROADMAP L162, 6/22~6/30)
> **상태**: 진행중 (드라이버 `scripts/cop_pipeline_advance.sh` 가 결정론적으로 전진)

## 무엇을 했나

야간 전진은 결정론적 드라이버가 처리했고(재실행 금지 대상), 본 회차는 그 STAGE 결과를
문서화·동기화·보고했다. 23:00 기준 파이프라인 상태:

```
STAGE=학습중
pid=20078 alive=yes
ckpt_latest=epoch_0099 ckpt_count=10
log_size=2443636 log_mtime=2026-06-24T14:00:52Z log_age_sec=6
last: {"epoch": 64, "step": 230, "loss": 0.007674, "l1": 0.005053, "kl": 0.000262}
```

### 1) 수집 ✓ — closed-loop 50 에피소드
- 출력: `data/episodes_cl/` (LeRobot v3.0 포맷)
- `meta/info.json`: `total_episodes=50`, `total_frames=3350`, `fps=30`,
  `observation.images.top` 480×640 h264, robot `so101`, split `train 0:50`
- 수집기 = closed-loop expert (`sim_data_collector.py`, scene_grasp_pads, 큐브 30mm,
  forcerange 3.0=12V 실스펙, lift≥40mm 필터). 로그 `logs/cop_data_collect.log` (16:39~16:52 완료).

### 2) 학습 진행중 — ACT 재학습 (data/episodes_cl)
- pid **20078** alive, `COP_DATASET_ROOT=data/episodes_cl` 로 신규 closed-loop 데이터 학습.
- 진척: **epoch 64/100**, loss 0.00767 (l1 0.00505, kld 0.000262), ~322s/epoch (MPS).
- loss 곡선 단조 감소 정상 (e61 0.00842 → e62 0.00823 → e63 0.00804 → e64 0.00767).
- 로그 `logs/act_train.log` (mtime 23:01, 활성), 메트릭 `logs/act_train_metrics.jsonl`.
- ETA: 100 epoch 완료 ~02:00 (잔여 36 epoch × 322s ≈ 3.2h).

### 3) 측정 — baseline 스모크만 존재 (closed-loop 모델 측정은 학습 완료 후)
- `research/simulation/inference_progress/rollout_summary.json`:
  checkpoint `epoch_0009`, scene `scene_grasp_pads.xml`, **rollouts 2**, success **0/2**,
  median_lift **6.4mm** (임계 40mm), wall 5.1s, cpu.
- ⚠ 이 측정은 드라이버의 측정 스테이지(--rollouts 10)가 **아니다**(rollouts=2).
  commit `16d2548` ("render_act_rollout closed-loop 정합 + 견고화")의 **2-rollout 정합 검증**으로,
  closed-loop 씬 end-to-end 추론 경로가 동작함을 확인한 산출물이다.
- 측정 대상 `epoch_0009`는 **6/21 open-loop 학습 baseline 체크포인트**(mtime Jun 21 16:58)다.
  → 0%/6.4mm 는 closed-loop 재학습 모델의 성적이 **아니라** pre-closed-loop baseline 이며 예상된 값.
- 신규 closed-loop 모델의 유효 측정은 학습(2번) 완료 후 드라이버 측정 스테이지가 새 모델
  서명(MEASURED_MARK 불일치)으로 자동 수행한다.

## 어떻게 검증했나

- 수집: `data/episodes_cl/meta/info.json` 파싱 → 50 ep / 3350 frame 확인.
- 학습: `logs/act_train_metrics.jsonl` tail 3줄 + `act_train.log` tail → epoch 64, loss 단조감소,
  로그 mtime 23:01(활성), pid 파일 `20078` 일치, 드라이버 alive=yes.
- 측정: `rollout_summary.json` 직접 판독 + `render_act_rollout.py` 체크포인트 선택 로직 확인
  (`find_latest_checkpoint` = mtime 최신), rollouts=2 ↔ 드라이버 10 불일치로 스모크 판별.

## 다음 단계 연결

- **학습 완료(~02:00) 후**: 드라이버 측정 스테이지가 신규 closed-loop 모델 10-rollout 측정 →
  `rollout_summary.json` 갱신. 이때 비로소 closed-loop 자동수집 1사이클의 **유효 Pick 성공률** 확보.
- 그 성공률이 closed-loop expert 수집 성적(30mm 75% @forcerange3.0)에 근접하면
  PHASE_ROADMAP L162 항목을 `[v]` 클로즈, Phase 1 W4 완료 기준(🔄)을 닫는다.
- 측정기 정합(L163 caveat)은 commit 16d2548 으로 closed-loop 씬에 맞춤 완료 — 잔여는 측정이
  baseline 아닌 신규 모델을 잡도록 학습 완료를 기다리는 것뿐.
