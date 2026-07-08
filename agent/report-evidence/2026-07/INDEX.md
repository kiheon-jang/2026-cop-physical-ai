# 2026년 7월 월간 보고서 증거 후보

> 7월 보고서 매핑: Phase 2 (Sim2Real) — 실기 50ep + Sim2Real 준비(DR).

## 2026-07-01
- Phase 2 W1 착수 — Domain Randomization 모듈 신규 + 수집기/측정기 연결(opt-in `--dr`): `agent/research-log/2026-07-01.md`, `research/simulation/2026-07-01_phase2-w1-domain-randomization.md`, `research/simulation/2026-07-01_phase2-w1-dr-wiring.md` → 7월 보고서 [Sim2Real 준비] 섹션.
- DR 3축 무작위화 8샘플 검증 프레임: `research/simulation/dr_samples/dr_sample_00~07.png`
- 23:30 nightly sim-test — 우선순위 4종 회귀(실행 12/12 성공): `agent/research-log/2026-07-01.md` (야간 sim-test 회차)
  - `sim_headless_6dof_video.py` 비디오: `research/simulation/video/sim_6dof_animation.mp4` (2501프레임, 9.1s)
  - `sim_camera_verification.py` 2카메라 동기 캡처(30프레임, 0.6s)
  - `sim_pick_place.py` legacy open-loop grasp 0/3 기준선(정상 기대치) — 실 성능은 closed-loop 70%
  - `sim_data_collector.py` closed-loop 수집 스모크 yield 3/3=100%, lift 41.5~43.2mm (임시 루트, 운영 무접촉)
- closed-loop 정책 성공률 유지: `research/simulation/inference_progress/rollout_summary.json` 7/10=0.70, median lift 43.7mm → 7월 보고서 [진척: Phase 1→2 전환] 섹션.

## 2026-07-02
- Phase 2 W1 — **DR on/off rollout 프록시 측정**(정책 강건성): `agent/research-log/2026-07-02.md`, `research/simulation/2026-07-02_phase2-w1-dr-onoff-proxy.md` → 7월 보고서 [Sim2Real 준비 / robustness] 섹션.
  - DR-off 0.70(7/10) vs DR-on 0.80(8/10), median lift 43.7 vs 44.1mm — 추론-시점 조명/마찰/카메라노이즈 섭동에 **성능 동등**(강건). `rollout_summary_dr.json`.
- 23:30 nightly sim-test — 우선순위 3종 회귀 재확인: `agent/research-log/2026-07-02.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적, min_approach 0.3228m — 기대된 기준선)
  - 운영 데이터 무결성: `episodes_cl` 50ep/3350frame·`rollout_summary.json` 0.70 불변.

## 2026-07-03
- Phase 2 W1 — **DR 축별(per-axis) ablation**(지배 섭동축 규명): `agent/research-log/2026-07-03.md`, `research/simulation/2026-07-03_phase2-w1-dr-axis-ablation.md` → 7월 보고서 [Sim2Real 준비 / robustness] 섹션.
  - light/friction/camera 각 단독 0.70(7/10), 실패집합 {2,5,8} 운영 baseline 과 완전 동일 → **지배적 Sim2Real 섭동축 없음, 정책 축별 강건**. `rollout_summary_dr_{light,friction,camera}.json`.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-03.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임)
  - `sim_pick_place.py` open-loop baseline 0/2(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 43.2~43.7mm (throwaway 루트, 운영 무접촉)
  - 운영 데이터 무결성: `episodes_cl` 50ep/3350frame·`rollout_summary.json` 0.70 불변.

## 2026-07-05
- Phase 2 W1 — **DR 50ep 데이터셋 합성 완료**(비프록시 실데이터): `agent/research-log/2026-07-05.md`, `research/simulation/2026-07-05_phase2-w1-dr-dataset-synthesis.md` → 7월 보고서 [Sim2Real 준비 / 데이터 다양성] 섹션.
  - `data/episodes_cl_dr` 50ep/3350frame 신규 합성, 성공 50/50·yield 86%, friction 0.757~0.89 등 ep별 DR 변동 확인. 큐브배치 커버리지 확장 트랙의 데이터 산출물 근거.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-05.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 42.5mm (throwaway 루트, 실행 후 삭제, 운영 무접촉)
  - 운영 데이터 무결성: `episodes_cl` 50ep/3350frame·`episodes_cl_dr` 50ep/3350frame·`rollout_summary.json` 0.70 불변.

## 2026-07-06
- Phase 2 W1 — **DR 재학습 트리거→진행→완료**(W1 잔여 절반): `agent/research-log/2026-07-06.md`, `research/simulation/2026-07-06_phase2-w1-pipeline-audit-dr-retrain-trigger.md`, `research/simulation/2026-07-06_phase2-w1-dr-retrain-inflight.md` → 7월 보고서 [Sim2Real 준비 / DR 재학습] 섹션.
  - 적대적 파이프라인 감사(19건 확정, critical 6건 수정) 후 `episodes_cl_dr`→`checkpoints/act_cl_dr` 100epoch 재학습 트리거(13:31)→**23:02 완료**(wall_clock ≈9.5h, final loss 0.00498). 측정은 다음 드라이버 사이클 담당.
- 23:30 nightly sim-test — DR 학습완료 감지 + 우선순위 4종 회귀: `agent/research-log/2026-07-06.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 41.5~42.0mm (throwaway 루트, 실행 후 삭제, 운영 무접촉)
  - 운영 데이터 무결성: `episodes_cl` 50ep/3350frame·`episodes_cl_dr` 50ep/3350frame·baseline `rollout_summary.json` 0.70/43.7mm 불변, DR ckpt 격리(`act_cl_dr`) 유지.

## 2026-07-07
- Phase 2 W1 — **DR-trained 측정 + 다중시드 공정추정 비교 → W1 종료**: `agent/research-log/2026-07-07.md`, `research/simulation/2026-07-07_phase2-w1-dr-trained-rollout-compare.md` → 7월 보고서 [Sim2Real 준비 / DR 결론] 섹션.
  - 4-seed 공정추정 **baseline 0.825 vs DR-trained 0.800**(통계적 동등, seed7 실패 +1=노이즈), 유일 개선=**median lift ~44→~50mm 전 시드 +6mm**(임계값 위→이진판정 무영향).
  - 실패 큐브배치 거의 불변(42{2,5,8}·123{0,1}·2026{5}) → **병목=섭동강건성 아닌 배치 커버리지(모방격차)**, DR 축은 sim 성공 천장 못 올림. 다음 레버=`.next=episodes_floor`(배치 다양성↑).
  - baseline 아카이브 `rollout_summary_baseline_cl.json`(0.70/43.7mm) 보존, 신규 `rollout_summary_cldr_seed{7,123,2026}.json` 3종.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-07.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임 3/3), `sim_camera_verification.py` PASS(2카메라 30프레임)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 41.5~42.0mm (throwaway 루트, 운영 무접촉)
  - 운영 데이터 무결성: `episodes_cl` 50ep·`episodes_cl_dr` 50ep·운영 `rollout_summary.json`(현 DR-trained act_cl_dr 0.70/50.2mm)·baseline 아카이브 보존.

## 2026-07-08
- Phase 2 W2 진입 — **W1(DR) 사이클 종료 → 배치 다양성(floor) 사이클 ACT 재학습 착수**: `agent/research-log/2026-07-08.md`, `research/simulation/2026-07-08_phase2-w2-floor-placement-retrain-inflight.md` → 7월 보고서 [Sim2Real 준비 / 다음 레버] 섹션.
  - 드라이버가 `episodes_cl_dr`→`act_cl_dr` STAGE=완료/유지(0.7)로 닫고 예약 `.next=episodes_floor`(바닥/받침대 없는 파지, 배치 커버리지↑)로 전환 → `episodes_floor` 50ep/3350frame(수집 yield 98%, 배치 x0.11~0.15)로 100epoch 재학습(pid 94316, `--no-resume`→`checkpoints/act_floor`). "DR 축 아닌 배치 다양성이 sim 천장을 올리는가" 첫 실측 준비.
  - 마커 2단계(target=`episodes_floor`·marker=`episodes_cl_dr:1783181837` 유지·pending=`episodes_floor:1783324998`)+ckpt 3자 격리로 학습중 baseline(운영 rollout 0.70/50.2mm) 무손상 — 무결성 설계 작동.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-08.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 41.2~42.4mm (throwaway 루트, 운영 무접촉)
  - floor ACT 학습 alive(loss 25.5→0.681 정상 수렴), 운영 데이터 무결성: `episodes_cl`/`episodes_cl_dr`/`episodes_floor` 각 50ep·3350frame·운영 `rollout_summary.json` 0.70/50.2mm 불변.
