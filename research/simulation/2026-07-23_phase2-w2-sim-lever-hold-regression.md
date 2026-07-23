# 2026-07-23 — Phase 2 W2: sim 성공률 레버 결착 후 hold + 우선순위 5종 회귀

## 상태 요약
드라이버 STAGE=완료/유지. 새 사이클 미트리거 → 수집/학습/측정 재실행 없음.
sim 트랙 성공률 레버(배치 다양성)는 7/22 4-seed 공정추정(4/4=1.0)으로 이미 결착.
오늘은 hold 일 — 무결성 재확인 + 우선순위 5종 회귀 독립 실행으로 신선 증거 확보.

## 파이프라인 상태 (증거)
- 타겟: `logs/cop_dataset_target` = `episodes_floor` (전환 없음)
- 마커 3자 정합:
  - trained_on = `episodes_floor:1783324998`
  - measured = `episodes_floor:1783710169`
- 운영 `rollout_summary.json` = `act_floor/epoch_0041`, seed42, 10/10, success_rate **1.0**, median lift **66.0mm**
  - md5 = `5207f67b189645de1bb26c124873b683` (7/22 값과 **동일 = 측정 후 불변**)
- 학습 프로세스 없음 (`ps` train_act 무). `act_floor` ckpt = epoch_0039/0041/0049/0059
  (0049/0059 는 과거 crash run 잔재, 운영 모델은 완주본 epoch_0041)
- datasets floor/cl/cl_dr 각 50ep 불변

## 우선순위 5종 회귀 (야간 독립 실행)
- **sim_camera_verification**: 2대 카메라 각 30프레임 캡처 — PASS
- **sim_headless_6dof_video**: 6관절 애니 2501프레임 렌더 — PASS
- **sim_pick_place**: min_approach **0.3228327114m** 결정론(7/18·7/21·7/22 동일값),
  max_lift 0.0 (고정포즈 expert 미접근 = 기지 기대값) — PASS
- **sim_data_collector** (2ep 스모크, `data/_smoke_0723` 격리→삭제): 성공 2/2, yield 100%,
  lift 41.8mm — PASS
- **joint_angle_comparison_sim**: 최대오차 **0.0244°**(elbow_flex) < 1° — PASS
  (6관절 전부 <0.025°)
- 5종 전부 회귀 이상 없음. 운영 데이터셋 무접촉(스모크 격리 루트, 삭제 확인).

## 다음 단계 연결
sim 트랙 성공률 레버는 규명 완료(open-loop 0% → closed-loop 0.70 → floor 1.000).
남은 두 항목 모두 외부 의존:
1. **실기 스텝(W2 zero-shot 실기 추론)**: Orin Nano SSH 외부의존 미수신 → 진입 불가, 대기.
2. **full-epoch(100) 공정비교 복원**: 42ep<100ep 는 04:04 외부 SIGKILL killer 탓.
   killer 규명·제거엔 `log show`/`launchctl`/`ps` 진단권한 필요(현재 sandbox 차단,
   `agent/external-dependencies.md` 에스컬레이션 대기).
두 외부 의존이 풀리기 전까지 드라이버는 hold 유지, 야간 에이전트는 회귀 감시 + 무결성 봉인.
