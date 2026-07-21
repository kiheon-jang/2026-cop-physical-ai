# floor-trained 첫 rollout 측정 — seed42 10/10 = 1.0 (12-run 만에 결착)

**날짜**: 2026-07-21 (화)
**Phase**: Phase 2 - W2 - 배치 다양성(floor) 사이클 측정
**단계**: 드라이버 STAGE=측정 (`act_floor/epoch_0041`, closed-loop 정합 씬 `scene_grasp_floor.xml`)

## 한 줄 결론

7/19 자가치유(`COP_EPOCHS=42`, 04:04 벽시계 killer 회피)가 발효 → floor 재학습이 **12-run
만에 처음 창 안에서 완주**(7/21 02:46, 42epoch, wall_clock 3.76h, loss 0.0259) → 드라이버가
`epoch_0041` 측정 → **seed42 10/10 = success_rate 1.0, median lift 66.0mm**. open-loop 0% →
closed-loop 0.70 → **floor(배치 다양성) 1.0**. W1 결론(병목=배치 커버리지)의 처방이 실측으로 적중.

## 무엇을 했나 (드라이버 담당, 본 에이전트는 문서화)

파이프라인 전진은 `scripts/cop_pipeline_advance.sh` 가 결정론적으로 처리(재실행 금지 규칙 준수).

1. **학습 완주 확정**: `episodes_floor`(50ep/3350f) → `checkpoints/act_floor`, 42epoch.
   - `checkpoints/act_floor/epoch_0041` mtime **2026-07-21 02:46** (창 04:04 이전 여유 완주).
   - `logs/act_train.log`: `"학습 42 epoch 완료"`, `wall_clock_sec` 13553.7 (3.76h).
   - metrics 마지막 = epoch 41 (0-index → 42 epoch), loss 0.0259, `rss_bytes` 925MB 평탄·
     `mps_mem` 5.66GB 평탄 (jetsam·GPU OOM 재반증 — 7/17~7/19 결론 유지).

2. **측정 스테이지**: 드라이버가 `epoch_0041` 을 seed 42, N=10 으로 rollout.

## 검증 (metric)

`research/simulation/inference_progress/rollout_summary.json` (measured_at 2026-07-21T23:00:53):

| 항목 | 값 |
|---|---|
| checkpoint | `act_floor/epoch_0041` |
| scene | `scene_grasp_floor.xml` |
| seed | 42 |
| success | **10 / 10** |
| success_rate | **1.0** |
| median_lift_mm | **66.0** |
| device / wall | cpu / 13.6s |

10 rollout 전부 성공, max_lift 0.056~0.068m (임계 0.04m 대비 큰 여유).
히스토리 아카이브: `inference_progress/history/20260721-230053_act_floor_epoch_0041.json` (+ `_traj.json`).

## 의의 — W1 가설의 실증

- 7/7 W1 종료 결론: **병목 = 섭동강건성(DR) 아닌 큐브배치 커버리지(모방격차)**. DR 축 증강은
  sim 천장을 못 올림(baseline 0.825 ↔ DR-trained 0.800). 처방 = **배치 다양성 데이터**(`episodes_floor`).
- 오늘 실측: 그 처방으로 재학습한 모델이 **seed42 에서 0.70(비관적 끝단) → 1.0** 으로 도약.
  배치 다양성이 성공률 천장을 올린다는 첫 직접 증거.

## 한계 / 정직한 단서

- **42epoch < baseline 100epoch** → 완전한 공정비교 아님(7/19 규명대로 04:04 killer 탓 full-epoch
  불가). 다만 baseline 이 100epoch 로도 seed42 0.70 이던 지점에서 42epoch floor 가 1.0 → 신호는 강함.
- **단일 seed(42)**. 정식 판정은 4-seed(42/7/123/2026) 공정추정 필요(다음 사이클, 드라이버 담당).
- full-epoch(100) 복원은 여전히 04:04 killer 규명·제거 대기(외부 의존 에스컬레이션,
  `agent/external-dependencies.md` 우선순위3).

## 무결성 격리 (불변 확인)

- datasets `episodes_floor`/`episodes_cl`/`episodes_cl_dr` 각 **50ep** 불변.
- 마커 3자 정합: target=`episodes_floor`, trained_on=`episodes_floor:1783324998`,
  measured=`episodes_floor:1783710169`. 승격 정상.

## 다음 단계 (드라이버)

`act_floor` 4-seed(42/7/123/2026) 공정추정 → baseline 0.825 / DR-trained 0.800 대비 배치
다양성이 성공률 천장을 올리는지 확정. 이후 실기 스텝(Orin SSH 외부의존 미수신) 대기 유지.
