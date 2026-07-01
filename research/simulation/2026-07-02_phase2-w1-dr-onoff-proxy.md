# Phase 2 W1 — DR on/off rollout 프록시 측정 (2026-07-02, 목요일)

## 오늘 진행 단계
Phase 2 - W1 - **DR 연결의 "측정" 절반 수행**: 기존 closed-loop 체크포인트(epoch_0099)에
Domain Randomization 을 **추론 시점에만** 적용한 on/off rollout 비교로 정책의 DR 강건성(robustness)을
프록시 측정했다. (DR 50ep 합성→재학습은 드라이버 사이클 담당 — 오늘 드라이버 STAGE=완료/유지.)

## 배경 / 결정론적 드라이버 결과 (재실행 없음)
- 야간 `scripts/cop_pipeline_advance.sh`(01:00) 출력: **STAGE=완료/유지 · 데이터 50ep · 최종 성공률=0.7 (목표 0.90)**.
- 마커·산출물 3자 정합 확인: `data/episodes_cl` 50ep/3350frame, `rollout_summary.json` 7/10=0.70(mtime 6/25),
  `logs/cop_measured.marker`/`cop_trained_on.marker` 존재. 새 사이클 미트리거 → 파이프라인 재실행 없음.
- 7/1 야간에 DR **배선(wiring)** 완료(opt-in `--dr`, 기본 off). 남은 W1 항목 = "DR 데이터셋 합성·측정".
  합성+재학습은 드라이버 사이클(수 시간) → 오늘은 재학습 불필요한 **측정 절반**을 프록시로 수행.

## 실행한 것
```bash
.venv/bin/python3 scripts/render_act_rollout.py \
    --checkpoint checkpoints/act/epoch_0099 --rollouts 10 --seed 42 --dr
```
- `--dr` 는 rollout reset + 관측 RGB 에 DR(조명/마찰/카메라노이즈) 적용, 결과를
  **`rollout_summary_dr.json` 로 별도 저장** → 운영 `rollout_summary.json` 불변(설계상 분리).
- DR-off 기준선은 **재실행하지 않음**: 운영 summary(seed 42, N=10) 7/10=0.70 이 곧 DR-off 대조군.
  동일 seed·동일 N 으로 DR-on 만 신규 실행 → apples-to-apples 비교.

## 결과 (동일 seed 42, N=10, epoch_0099)
| 조건 | 성공 | 성공률 | median lift | 실패 rollout |
|---|---|---|---|---|
| DR-off (운영 대조군) | 7/10 | **0.70** | 43.7mm | 2, 5, 8 |
| DR-on (신규) | 8/10 | **0.80** | 44.1mm | 2, 8 |

- DR-on per-rollout lift(mm): [45.4, 43.6, **6.1**, 42.8, 44.6, 46.5, 44.2, 44.1, **5.1**, 42.0].
- **해석**: DR-on 이 오히려 +1 성공(0.70→0.80). 1 rollout 차이 = 노이즈 범위 → **성능 동등**.
  즉 추론 시점 조명/마찰/카메라노이즈 섭동이 grasp 을 무너뜨리지 않음 → closed-loop 정책이
  **시각·물리 섭동에 강건**하다는 긍정적 Sim2Real 신호.
- 실패 모드 일관성: 두 조건 모두 rollout 2·8 이 저-lift(~5–6mm)로 실패 → 특정 초기 큐브 배치에서의
  구조적 실패이지 DR 로 유발된 실패가 아님(seed 공통).

## 검증 (비파괴)
- 운영 `rollout_summary.json`: **7/10=0.70 불변** ✓ (프로그램 확인 출력)
- `data/episodes_cl`: **50ep / 3350frame 무손상** ✓
- 변경 파일 = `research/simulation/inference_progress/rollout_summary_dr.json` **단 하나** (`git status` 확인) ✓
- 서브모듈 변경 없음, `--dr` 는 rmtree 없음(운영 데이터 미접촉).

## 다음 단계로의 연결
- **본격 W1 잔여(드라이버 사이클)**: `sim_data_collector.py --dr` 로 DR 50ep 합성(`data/episodes_cl_dr`) →
  ACT 재학습 → DR-학습 모델 vs 기준 모델 성공률 비교. 이는 수 시간 소요 → 야간 드라이버가 담당
  (COP_TARGET_EP 상향 또는 DR 전용 마커 트리거 시 진행).
- 오늘 프록시 결과(DR-on 8/10)는 **추론-시점** 강건성만 측정. 재학습(DR 데이터로 학습)은
  일반화·Sim2Real 격차 축소를 더 직접적으로 검증 → W2 zero-shot 실기 추론과 짝을 이룸.
- **W2**: zero-shot 실기 추론 → 격차 측정(외부의존: 장기헌 Orin/실기 SSH). 미수신 시 DR on/off 학습 비교가 프록시.
