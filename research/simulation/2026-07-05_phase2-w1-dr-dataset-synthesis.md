# Phase 2 W1 — DR 50ep 데이터셋 합성 완료 (2026-07-05)

> **단계**: Phase 2 (Sim2Real) · W1 (7/1~7/7) Domain Randomization
> **위치**: W1 본격 잔여의 **첫 절반 = "DR 50ep 합성"** 달성.
> **성격**: 실제 데이터 생성(비프록시). 운영 파이프라인/측정치는 불변.

## 오늘 한 일

지난 4일(7/1~7/4)은 전부 **비파괴 프록시**로 "DR 섭동에 정책이 강건함 + 남은 실패는
큐브배치(모방격차)"를 실증했고, 매 로그의 결론은 동일하게 **"본격 잔여: DR 50ep 합성 →
재학습 → 비교"** 였다. 오늘 그 잔여의 **첫 절반(합성)이 완료**되었다.

- **산출물**: `data/episodes_cl_dr/` — LeRobot Dataset 포맷 **50 에피소드 / 3350 프레임**
  (운영 `episodes_cl` 과 동일 규모: 50/3350).
- **수집 방식**: closed-loop expert(`sim_data_collector.py`) + `--dr` opt-in Domain
  Randomization(조명·마찰·카메라노이즈 3축) 을 **매 에피소드 reset 훅에서 무작위화**.
  `snapshot_baseline`/`restore_baseline` 로 friction 곱셈·light_pos 덧셈 누적 방지(7/1 배선 그대로).
- **수집 결과**(`logs/dr_collect_50ep.log`, 01:02~01:17):
  **성공 50/50 · 시도 58회 · yield 86%**. lift 범위 40.2~45.3mm(전부 40mm lift 필터 통과).
- **DR 실제 적용 증거**(에피소드별 파라미터 이동):
  | | light_diffuse | light_ambient | friction_scale | camera_noise_std |
  |---|---|---|---|---|
  | 첫 ep | 0.71 | 0.31 | 0.757 | 9.805 |
  | 끝 ep | 0.694 | 0.378 | 0.89 | 5.167 |
  → friction 0.757~0.89, 조명·카메라노이즈 모두 에피소드마다 변동 = **DR 정상 인가**.

## 어떻게 검증했나 (무결성)

| 항목 | 값 | 판정 |
|---|---|---|
| DR `episodes_cl_dr` | **50 ep / 3350 frame** | 신규·정상 |
| 운영 `episodes_cl` | 50 ep / 3350 frame | **불변** |
| 운영 `rollout_summary.json` | success_rate 0.70 · median 43.7mm | **불변** |
| 마커 `cop_measured`/`cop_trained_on` | 1782134830 / 1782287560 (6/25·6/24) | **불변** |
| 드라이버 STAGE | 완료/유지 · 50ep · 0.7 | 새 사이클 미트리거 |

- DR 수집은 **별도 데이터셋 루트(`data/episodes_cl_dr`)** 로 격리되어 운영 `episodes_cl`·
  운영 rollout 측정치·학습 마커를 **일절 건드리지 않음**. yield 86%(운영 91%와 동급)로 DR 인가가
  grasp 성공을 무너뜨리지 않음을 재확인(7/2~7/3 강건성 결론과 정합).

## 다음 단계로의 연결

- **W1 본격 잔여의 남은 절반 = 재학습·비교**(드라이버 사이클, 수 시간):
  `train_act` 를 `COP_DATASET_ROOT=data/episodes_cl_dr` 로 재학습 → DR-trained 정책을
  rollout 측정 → **DR-trained vs 현행(non-DR) 일반화 비교**.
  이는 **파이프라인 학습/측정 단계**이므로 결정론적 드라이버(`cop_pipeline_advance.sh`) 담당이며,
  본 야간 에이전트는 실행하지 않음(하드룰: 수집/학습/측정 재실행 금지). 트리거 조건 =
  DR 마커 설정 또는 `COP_DATASET_ROOT` 전환으로 다음 드라이버 사이클에서 수행.
- **가설 검증 목표**(7/4 확증한 방향): 남은 gap 은 섭동강건성이 아니라 **큐브배치 커버리지**.
  DR 데이터가 배치·외관 다양성을 넓혀 헤드라인 0.70(seed42, 비관 끝단) → 4-seed 공정추정
  ~0.82 이상으로 정책 실력을 끌어올리는지 재학습 후 정량 확인.
- **W2**: zero-shot 실기 추론 격차 측정(외부의존: 장기헌 Orin/실기 SSH). sim-side 기준선 ~82% 사용.
