# Phase 4 W2 — RS232 DR 수집 배선 + DR 데이터셋 합성 (2026-09-19)

## 배경 / 오늘의 단계
- 드라이버(`cop_pipeline_advance.sh` RS232 분기)는 STAGE=**완료/유지**: `episodes_rs232` 100ep,
  정합·핀치 baseline 최종 성공률 **0.600**(목표 0.50 충족) — 9/18 클로즈된 사이클 유지, 재실행 없음.
- 로드맵 다음 `[ ]` 실행가능 항목 = Phase 4 W2 **RS232 DR 합성 + 재학습**(866행).
  - **합성**(DR 데이터셋 만들기) = 시뮬 구현 작업 → 야간 에이전트 담당(7/5 `episodes_cl_dr` 선례와 동일).
  - **재학습** = 드라이버 담당(데이터셋 타겟 전환 시 다음 사이클). 하드룰상 에이전트가 학습 직접 실행 안 함.

## 한 문제: RS232 수집기에 DR 배선이 없었다
- S1 수집기(`sim_pcb_reset_collector.py`)는 이미 `COP_COLLECT_DR=1` env-gate 로 DR 수집을 지원.
- RS232 수집기(`sim_rs232_unplug_collector.py`)는 미지원 → DR 데이터셋을 만들 수단이 없었다.
- **DR 축은 sim 성공 천장을 못 올린다**는 Phase 2 W1 실증(baseline 0.825 ↔ DR-trained 0.800)이 있으나,
  로드맵 항목이므로 **데이터셋 합성까지 수행**하고 재학습 트리거는 드라이버에 맡긴다(비교 근거 확보용).

## 한 작업: S1 패턴 그대로 이식 (surgical, 하위호환)
`sim_rs232_unplug_collector.py` `main()` 에 S1 수집기와 동일 계약으로 3곳 배선:
1. `rng` 직후 env-gate 블록 — `COP_COLLECT_DR`/`COP_COLLECT_DR_AXES`, `snapshot_baseline`,
   DR rng 는 배치 rng 와 분리 스트림(seed+99991) → **플러그 배치 시퀀스는 nominal 수집과 동일**(비교 가능).
2. `record()` — top/closeup 렌더에 `apply_camera_noise` 적용(측정기와 동일 계약).
3. 수집 루프 `twin.reset()` 직후 — `restore_baseline` → `randomize_scene(axes=)` → `mj_setConst`
   (매 reset 원본복원 후 무작위화 = 누적 방지, render 측정기와 동일 순서).
- **환경치수 불변 원칙 유지**: 포트/커넥터/존/판정 상수는 안 건드리고 조명·마찰·카메라 노이즈만 섭동·복원.
- 기본 off(`COP_COLLECT_DR` 미설정) → 드라이버 nominal 파이프라인 불변.

## 검증
- **DR 스모크 2ep**(throwaway root `data/_smoke_rs232_dr_20260919`, 실행 후 삭제): **성공 2/2, yield 100%**,
  `[DR 수집] axes=('light','friction','camera')` 배너 출력, LeRobot v3 저장 정상.
- **DR 실인가 단위검증**: friction 무작위 변동 확인, camera_noise_std 5.27 산출, `restore_baseline` 후
  friction `np.allclose` 원본 복원 = **비파괴/비누적 확정**.
- **DR 데이터셋 합성**(`data/episodes_rs232_dr`, 100ep, `COP_COLLECT_DR=1`): 23:00 잡에서 6/100 중단(부모 프로세스 종료에 자식 수집기 킬) → 23:30 sim-test 잡이 `setsid` detached 로 클린 재기동(PID 29014)하여 완주 처리. 완주 검증 = `meta/info.json` total_episodes=100(내일 잡).

## 무결성 격리
- 별도 데이터셋 루트(`episodes_rs232_dr`)라 운영 `episodes_rs232`(100ep)·`checkpoints/act_rs232_sim`·
  마커(trained_on `episodes_rs232:1789546321`·measured `episodes_rs232:1789666953`)·
  `rollout_summary_rs232.json`(0.600) **전부 불변**. 드라이버 STAGE=완료/유지 재실행 없음.

## 다음 단계로의 연결
- DR 데이터셋 준비 완료 → 드라이버 새 사이클 조건(`logs/cop_dataset_target` 를 `episodes_rs232_dr` 로
  전환 / 마커 삭제)이 세팅되면 드라이버가 DR 재학습(42epoch, 세션 분리로 04:04 killer 회피) → DR-trained
  4-seed 측정 → nominal 0.600 과 공정 비교. 에이전트는 하드룰상 타겟 전환을 직접 하지 않고 **준비 완료를 표면화**.
- Phase 2 선례상 DR 은 천장을 못 올릴 공산이 크나(0.825↔0.800), RS232 정합 환경에서 실측으로 확증하는 것이 항목의 목적.
