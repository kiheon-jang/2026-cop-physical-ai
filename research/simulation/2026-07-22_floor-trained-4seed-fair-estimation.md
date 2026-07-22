# floor-trained ACT — 4-seed 공정추정 (배치 다양성이 성공률 천장을 올렸다)

- **일자**: 2026-07-22 (수요일)
- **Phase**: Phase 2 - W2 - floor-trained 4-seed 공정추정
- **모델**: `checkpoints/act_floor/epoch_0041` (42epoch, floor 배치 다양성 데이터셋 `episodes_floor`)
- **씬**: `SO-ARM100/Simulation/SO101/scene_grasp_floor.xml`

## 무엇을 했나

7/21 에 seed42 단일 측정(10/10=1.0)이 나왔으나, 정식 판정은 **4-seed 공정추정**이 남아 있었다
(7/4~7/7 baseline·DR-trained 비교와 동일 프로토콜). 오늘 드라이버는 STAGE=완료/유지(새 사이클
미트리거)여서 파이프라인 수집/학습/측정은 재실행하지 않았고, **비파괴 프록시 측정**으로 나머지 3
seed(7/123/2026)를 동일 checkpoint(`act_floor/epoch_0041`)에 추가 rollout 했다.

```
render_act_rollout.py --checkpoint checkpoints/act_floor/epoch_0041 \
  --seed {7,123,2026} --rollouts 10 --video-rollouts 0 \
  --summary-suffix _floor_seed{N}
COP_SCENE=scene_grasp_floor.xml
```

`--summary-suffix` 로 운영 `rollout_summary.json` 을 건드리지 않고 별도 파일에만 기록.

## 결과 — 4 seed 전부 만점

| seed | success | success_rate | median lift | 실패 rollout |
|------|---------|--------------|-------------|--------------|
| 42 (7/21 운영) | 10/10 | **1.00** | 66.0mm | 없음 |
| 7   | 10/10 | **1.00** | 65.3mm | 없음 |
| 123 | 10/10 | **1.00** | 60.0mm | 없음 |
| 2026| 10/10 | **1.00** | 64.9mm | 없음 |
| **4-seed 평균** | **40/40** | **1.000** | **64.0mm** | **0건** |

전 40 rollout 성공, max_lift 전부 임계 0.04m 여유 초과.

## 결론 — 배치 다양성 = 성공률 천장을 올리는 레버 (실증 완료)

| 트랙 | 4-seed 평균 성공률 | median lift |
|------|-----|-----|
| baseline (cl, 100ep) | 0.825 | ~44mm |
| DR-trained (cl_dr, 100ep) | 0.800 | ~50mm |
| **floor-trained (42ep)** | **1.000** | **64mm** |

- 7/7 W1 결론(**병목 = DR 섭동강건성 아닌 큐브배치 커버리지**)의 처방 = 배치 다양성 데이터 재학습.
  7/21 seed42, 오늘 4-seed 로 **실측 확증**: 0.825/0.800 → **1.000**.
- baseline·DR-trained 은 seed 마다 특정 배치에서 실패(모방격차)했으나(42{2,5,8}·123{0,1}·2026{5}),
  **floor-trained 은 4 seed 전부 실패 배치 0** → 배치 커버리지가 모방격차를 실제로 메웠음.

## 한계 (정직 보고)

- **42epoch < baseline 100epoch**: 04:04 외부 SIGKILL(7/19 확정) 탓 full-epoch 불가 → epoch 수는
  공정하지 않음. 즉 "42ep 저학습에도 1.0" 이라 성능은 오히려 과소, 결론 방향(배치 다양성 우위)은
  더 강해지지만, **엄밀한 apples-to-apples 100ep 비교는 04:04 killer 규명(외부 에스컬레이션) 후속**.
- floor 씬은 바닥/받침대 없는 파지로 30mm 큐브 전용. 50mm·RS232 정밀삽입은 별도 트랙.

## 무결성 격리 (비파괴 검증)

- 운영 `rollout_summary.json` md5 = `5207f67b189645de1bb26c124873b683` **측정 전후 불변**.
- 신규 파일만 추가: `rollout_summary_floor_seed{7,123,2026}.json`.
- datasets floor/cl/cl_dr 각 **50ep/3350frame 불변**. 마커 3자 정합 유지
  (target=`episodes_floor`, trained_on=`episodes_floor:1783324998`, measured=`episodes_floor:1783710169`).

## 다음 단계

배치 다양성 우위가 4-seed 로 확정 → sim 트랙의 성공률 레버는 규명 완료. 남은 것:
- **실기 스텝**(W2 zero-shot 실기 추론): Orin Nano SSH 외부의존 미수신 → 진입 불가, 대기.
- **full-epoch(100) 공정비교 복원**: 04:04 killer 규명 필요(external-dependencies.md 진단권한 대기).
