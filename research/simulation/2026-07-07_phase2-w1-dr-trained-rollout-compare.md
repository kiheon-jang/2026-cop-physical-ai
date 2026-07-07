# Phase 2 W1 — DR-trained rollout 측정 + 다중시드 공정추정 비교 (2026-07-07)

## 요약
어제(7/6) 야간에 학습 완료된 **DR 재학습 모델**(`checkpoints/act_cl_dr/epoch_0099`,
`episodes_cl_dr` 50ep 학습)을 오늘 드라이버가 **측정**했고(STAGE=측정, seed42 0.70),
야간 에이전트가 여기에 **다중시드(7/123/2026) 공정추정 비교**를 붙였다(비파괴, `_cldr_seed*` 접미사).

**결론(정직):** DR 재학습은 **성공률을 올리지 못했다** — 4-seed 공정추정 baseline 0.825 →
DR-trained 0.800(seed7 실패 1건 추가 = n=10 노이즈 수준, 통계적 동등). 유일하게 **일관되게
개선된 지표는 median lift(~44 → ~50mm, 전 시드 +6mm)**. 그리고 **실패 큐브배치가 거의 동일**
(42{2,5,8}·123{0,1}·2026{5} 불변). → **병목은 섭동강건성이 아니라 큐브배치 커버리지(모방격차)**
라는 7/3~7/4 가설을 DR 실모델로 실증. DR축 추가가 아니라 **배치 다양성 데이터**가 다음 레버.

## 드라이버 결과 (재실행 없음 — 측정 스테이지)
```
타겟: 데이터=episodes_cl_dr  ckpt=checkpoints/act_cl_dr
학습완료 확정 (episodes_cl_dr, 100epoch) → 측정 단계로 진행
STAGE=측정  (epoch_0099 rollout, closed-loop 정합 씬 scene_grasp_pads)
  "success_rate": 0.7   (seed42, 7/10, median lift 50.2mm)
```
- 마커 2단계 승격 정상: `.pending`(episodes_cl_dr:1783181837) → `cop_trained_on.marker` 승격,
  `.pending` 제거됨. `cop_dataset_target`=episodes_cl_dr, `.next`=episodes_floor(다음 사이클).
- 운영 `rollout_summary.json` 은 이제 **DR-trained(act_cl_dr)** 성적으로 갱신됨(마커 승격 → 정당한 운영 덮어쓰기).
  이전 baseline 은 `rollout_summary_baseline_cl.json`(0.70/43.7mm, ckpt=act/epoch_0099)에 **보존**.

## 다중시드 공정추정 비교 (야간 에이전트, 비파괴 프록시)
DR-trained 모델을 baseline 과 **동일 3 seed**(7/123/2026, N=10)로 측정, 별도 `_cldr_seed*` 파일 저장.
seed42 는 드라이버 운영 측정값 사용.

| seed | baseline (act) | DR-trained (act_cl_dr) |
|---|---|---|
| 42   | sr **0.70** · lift 43.7 · fail {2,5,8} | sr **0.70** · lift **50.2** · fail {2,5,8} |
| 7    | sr **0.90** · lift 44.8 · fail {9}     | sr **0.80** · lift **49.8** · fail {3,9}   |
| 123  | sr **0.80** · lift 43.7 · fail {0,1}   | sr **0.80** · lift **50.2** · fail {0,1}   |
| 2026 | sr **0.90** · lift 44.8 · fail {5}     | sr **0.90** · lift **50.5** · fail {5}     |
| **4-seed 평균** | **0.825** | **0.800** |

### 판독 (3가지, 정직하게)
1. **성공률: 개선 없음 (통계적 동등).** 0.825 → 0.800. 유일한 차이는 seed7 에서 실패 1건 추가
   (rollout 3). n=10 단일시드 해상도 ±0.1 안 = **노이즈**. DR 재학습이 binary 성공률을 올렸다고
   말할 수 없다.
2. **median lift: 일관된 +6mm 개선 (44→50mm, 4/4 시드).** 이건 노이즈가 아니라 체계적 신호 —
   DR-trained 정책이 더 높고 깔끔하게 든다(성공 rollout 들이 전부 ~0.050m). 단, lift 임계값(40mm)
   위 개선이라 **성공/실패 이진 판정은 안 바뀜** → 헤드라인 무영향.
3. **실패 큐브배치 거의 불변.** 42{2,5,8}·123{0,1}·2026{5} = baseline 과 완전 동일, seed7 만 {9}→{3,9}.
   → 실패는 **특정 큐브배치에 고정**돼 있고 조명/마찰/카메라노이즈 DR 로는 안 흔들린다.

### 왜 이 결과가 예측대로인가
7/2(DR on/off 동등)·7/3(축별 ablation 전부 0.70, 실패 {2,5,8} 불변)·7/4(seed마다 실패 이동 =
모방격차)에서 이미 **정책이 섭동에 강건**하고 **병목은 배치 커버리지**임을 프록시로 규명했다.
DR 데이터로 **재학습**해도 섭동강건성을 이미 갖춘 정책에 섭동 증강을 더한 것 → 성공률 무변화가
**정합적 예측 결과**. lift 품질만 소폭 향상. **결론: DR 축 증강은 sim 성공 천장을 못 올린다.
올리려면 학습 데이터의 큐브배치 다양성(placement coverage)을 넓혀야 한다.**

## 무결성 확인 (비파괴 — 격리 유지)
| 항목 | 값 | 판정 |
|---|---|---|
| 운영 `rollout_summary.json` | DR-trained act_cl_dr/epoch_0099, 0.70/50.2mm | 정당 갱신(마커 승격) |
| baseline 아카이브 `rollout_summary_baseline_cl.json` | 0.70/43.7mm, ckpt=act/epoch_0099 | **보존** |
| baseline seed 요약 `_seed{7,123,2026}` | 0.90/0.80/0.90 (7/4값) | **불변**(다른 접미사) |
| `episodes_cl` / `episodes_cl_dr` | 각 50ep | 불변 |
| 마커 `cop_trained_on.marker` | episodes_cl_dr:1783181837 | 승격 완료(`.pending` 제거) |
| train_act 프로세스 | 없음 | 학습 종료(7/6 23:02) |

- 신규 산출물: `rollout_summary_cldr_seed{7,123,2026}.json` 3종만 추가. 운영 traj_latest 는
  suffix 측정이라 미변경(드라이버 seed42 측정본 유지).

## 다음 단계로의 연결
- **W1 (7/1~7/7) 종료.** DR 배선(7/1)→합성(7/5)→재학습(7/6)→측정·다중시드비교(7/7) 전 구간 완주.
  실증 결론: **DR 는 Sim2Real 섭동강건성 확보엔 유효(이미 강건 확인)하나 sim 성공률 천장은 못 올림.
  천장 = 배치 커버리지.** → `.next=episodes_floor`(바닥 파지, 배치 다양성↑) 사이클이 정공법.
- **W2 (7/8~):** zero-shot 실기 추론 → Sim2Real 격차 측정. **외부의존**: 장기헌 Orin/실기 SSH
  (external-dependencies.md 미수신). sim-side 공정추정 기준선 = **~0.80~0.825**(seed42 0.70 은
  비관적 끝단). DR-trained 모델이 실기에서 섭동에 더 강건한지가 W2 의 핵심 검증점.
