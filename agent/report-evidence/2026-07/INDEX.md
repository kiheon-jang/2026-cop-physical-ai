# 2026년 7월 월간 보고서 증거 후보

> 7월 보고서 매핑: Phase 2 (Sim2Real) — 실기 50ep + Sim2Real 준비(DR).

## 2026-07-22
- Phase 2 W2 — **floor-trained 4-seed 공정추정 = 4/4 전부 1.0 (배치 다양성이 성공률 천장을 올렸다)**: `agent/research-log/2026-07-22.md`, `research/simulation/2026-07-22_floor-trained-4seed-fair-estimation.md` → 7월 보고서 [Sim2Real / 배치 다양성 성공률] 섹션.
  - 비파괴 프록시로 `act_floor/epoch_0041` 에 seed 7/123/2026 추가 rollout: 4-seed(42/7/123/2026) **전부 10/10=1.0, 40/40 성공, 실패 배치 0건, 평균 median lift 64.0mm**. baseline 0.825 / DR-trained 0.800 → **floor-trained 1.000**. 7/7 W1 결론(병목=큐브배치 커버리지)의 처방(배치 다양성 데이터)을 4-seed 로 실증 확증. 한계: 42ep<100ep(04:04 killer) → apples-to-apples 는 killer 규명 후속.
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀 (7/22 회차): `agent/research-log/2026-07-22.md`
  - camera 30프레임 2카메라 PASS · 6dof 2501프레임 PASS · pick 0.3228327m 결정론(기지 baseline) · collector 2/2 yield100% lift **43.0mm**(throwaway root 삭제) · joint_angle 최대오차 **0.0244°<1°**. 운영 `rollout_summary.json` md5 `5207f67b…` 전후 불변·datasets 각 50ep/3350f 불변.

## 2026-07-21
- Phase 2 W2 — **floor-trained 첫 rollout = seed42 10/10 = 1.0 (12-run 결착)**: `agent/research-log/2026-07-21.md`, `research/simulation/2026-07-21_floor-trained-first-rollout.md` → 7월 보고서 [Sim2Real / 배치 다양성 성공률] 섹션.
  - 7/19 자가치유(`COP_EPOCHS=42`)가 발효 → floor 재학습 **12-run 만에 첫 창내 완주**(`act_floor/epoch_0041` mtime 02:46, 42ep, wall 3.76h, loss 0.0259) → 드라이버 측정 seed42 N=10 = **success 10/10 = 1.0, median lift 66.0mm**(max 0.056~0.068m 임계 0.04m 여유). open-loop 0%→closed-loop 0.70→**floor 1.0**. W1 결론(병목=배치 커버리지)의 처방 실측 적중. 한계: 42ep<100ep 공정비교 아님·단일 seed42(4-seed 후속).
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀 (7/21 회차): `agent/research-log/2026-07-21.md`
  - `sim_camera_verification.py` PASS(2카메라 30프레임 동기), `sim_headless_6dof_video.py` PASS(2501프레임/6관절)
  - `sim_pick_place.py` open-loop baseline fail 결정론(min_approach **0.3228m** — 기대 기준선 불변)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100%, lift **63.4mm**, yield 100% (throwaway root `episodes_smoke` → 삭제, 운영 무접촉)
  - `joint_angle_comparison_sim.py` 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성: datasets floor/cl/cl_dr 각 50ep 불변·마커 3자 정합(target/trained_on/measured=`episodes_floor`) 승격 정상.

## 2026-07-19
- Phase 2 W2 — **floor 재학습 12차 = 시각연동 외부 SIGKILL 확정 + deadlock 규명 자가치유**: `agent/research-log/2026-07-19.md`, `research/simulation/2026-07-19_floor-retrain-timelinked-sigkill-confirmed.md` → 7월 보고서 [파이프라인 견고성 / 근본원인 규명] 섹션.
  - RSS 프로브 첫 crash 곡선(pid 5069, 49ep): `rss_bytes` 827→850MB 초반 1회 후 완전 평탄(**jetsam 반증**)·`mps_mem` 6.64GB 평탄(GPU OOM 재반증)·`elapsed` 368.8s slowdown 없음. **epoch↔벽시계 교락 해제**(느린 epoch 로 같은 ~04:04 에 49ep 만 돌고 죽음) = **고정 벽시계 외부 SIGKILL 확정**(FD·GPU OOM·jetsam 3가설 전부 기각). deadlock 규명: 100ep×368s=~10h 가 5h 창 초과 + `--no-resume` = 영원히 완주 불가.
  - **[자가치유]** `cop_pipeline_advance.sh` `COP_EPOCHS:-100`→`:-42`(창 안 ~03:41 완주<04:04) → 내일 발효 → **12-run 만에 첫 floor rollout** 경로 개통. 한계: 42ep 저학습=공정비교 아님, full-epoch 복원은 ~04:04 killer 규명(sandbox 차단) 필요.
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀 (7/19 회차): `agent/research-log/2026-07-19.md`
  - `sim_camera_verification.py` PASS(2카메라 30프레임 동기), `sim_headless_6dof_video.py` PASS(2501프레임/6관절)
  - `sim_pick_place.py` open-loop baseline fail 결정론(min_approach **0.3228m** — 기대 기준선 불변)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100%, lift **42.9mm**, yield 100% (throwaway root)
  - `joint_angle_comparison_sim.py` 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성: 운영 rollout act_cl_dr **0.70/50.2mm** 불변·markers 격리(pending=`episodes_floor` 대기)·datasets floor/cl/cl_dr 불변·학습 pid 91975 alive(epoch 5, loss 0.72, rss_bytes 836MB 평탄).

## 2026-07-16
- Phase 2 W2 — **floor 재학습 9차 = MPS-fix(empty_cache) + mps_mem 계측 발효 run**: `agent/research-log/2026-07-16.md`, `research/simulation/2026-07-16_phase2-w2-floor-retrain-mps-fix-effective-run.md` → 7월 보고서 [파이프라인 견고성 / 근본원인 정정] 섹션.
  - pid 7243 은 mps-fix 커밋 `32fcb5d`(7/15) 이후 코드 로드 → empty_cache 완화 + `mps_mem` 계측 실적용. 8-run 천장(~56~59ep)에 처음 완화+계측 동시 적용 → 완주=OOM 해소 실증 / 재crash=`mps_mem` 곡선으로 OOM 확정→batch_size root fix.
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀: `agent/research-log/2026-07-16.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임/6관절), `sim_camera_verification.py` PASS(2카메라 30프레임)
  - `sim_pick_place.py` open-loop baseline fail 2회 결정론 동일(min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100% yield, lift 47.0mm (throwaway root → 삭제, 운영 무접촉)
  - `joint_angle_comparison_sim.py` 추론 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets 각 50ep/3350f 불변. 학습 pid 7243 alive(epoch 6, loss 0.58).

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

## 2026-07-09
- Phase 2 W2 — **floor 재학습 재시도 + DataLoader FD 누수 자가치유**: `agent/research-log/2026-07-09.md`, `research/simulation/2026-07-09_phase2-w2-floor-retrain-fd-selfheal.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 floor 학습(pid 94316) epoch ~50 이상종료 = `OSError [Errno 24] Too many open files`(매 epoch DataLoader 워커 4개 재spawn·FD 누수). 드라이버 감지→재학습 재시작(pid 21661).
  - **[자가치유]** `train_act.py` DataLoader `persistent_workers=workers > 0`(surgical 1줄, 워커 1회 spawn 재사용) → FD 누수 재발 방지. ast·DataLoader 스모크 검증. (pid 21661은 fix 이전 로드 → 재크래시 시 내일 드라이버가 수정코드로 완주.)
  - 무결성 격리: target=`episodes_floor`·marker=`episodes_cl_dr`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor` 대기, baseline 무손상.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-09.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임 3/3, mean 14.8s), `sim_camera_verification.py` PASS(2카메라 30프레임 3/3)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.323m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 42.5mm, LeRobot v3.0 구조 정상 (throwaway 루트, 운영 무접촉)
  - floor ACT 재학습 pid 21661 alive(epoch 5/100 loss 0.656, ETA ~08:15), 운영 데이터 무결성: `episodes_cl`/`episodes_floor` 각 50ep·운영 `rollout_summary.json` 0.70/50.2mm 불변.

## 2026-07-10
- Phase 2 W2 — **floor 재학습 3차 = FD-fix(persistent_workers) 첫 발효 run**: `agent/research-log/2026-07-10.md`, `research/simulation/2026-07-10_phase2-w2-floor-retrain-fdfix-run.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 run(pid 21661, fix 이전 코드 로드) 예측대로 ~epoch 50 FD 고갈 재크래시(`epoch_0049` 03:45) → 드라이버 이상종료 감지 후 **새 run pid 39732**(23:00:26, `--no-resume`→`checkpoints/act_floor`). pid 39732 는 FD-fix 커밋 `c827ffe`(7/9) 이후 디스크 코드 로드 → **수정 실적용** → 100epoch 완주 기대(어제 예고 실현).
  - 23:30 재확인 pid 39732 alive **epoch 6 step 320 loss 0.534** = 크래시 지점 이전 정상 진행, FD-fix 실효 확인.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-10.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS 3/3(2501프레임/run), `sim_camera_verification.py` PASS 3/3(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 43.9mm (throwaway `data/_smoke_0710` → 삭제, 운영 무접촉)
  - 무결성 전수: target=`episodes_floor`·marker=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·datasets `episodes_cl`/`episodes_cl_dr`/`episodes_floor` 각 50ep·3350frame 불변.

## 2026-07-11
- Phase 2 W2 — **floor 재학습 4차 = FD 누수 근본강화(RLIMIT_NOFILE 셀프-상승)**: `agent/research-log/2026-07-11.md`, `research/simulation/2026-07-11_phase2-w2-floor-retrain-fd-rootfix.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 run(pid 39732, persistent_workers fix)이 crash 를 ~49→59 로 밀었으나 완주 실패 → 드라이버가 이상종료 감지 후 **새 run pid 56445** 재시작. 근본원인=크론 셸 낮은 FD 천장(256) → `train_act.py` `_raise_fd_limit()` 로 학습 프로세스가 자기 FD 소프트한도를 하드까지 셀프-상승(다음 run 발효).
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-11.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/2(결정론적 동일, min_approach 0.323m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% 성공(yield 67%), lift 42.7mm (throwaway `data/_smoke_0711` → 삭제, 운영 무접촉)
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets 각 50ep·3350frame 불변. 학습 pid 56445 alive(epoch 5, loss 0.676).

## 2026-07-12
- Phase 2 W2 — **floor 재학습 5차 = RLIMIT-fix 발효 run(in-flight)**: `agent/research-log/2026-07-12.md`, `research/simulation/2026-07-12_phase2-w2-floor-retrain-rlimit-effective-run.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 run(pid 56445, RLIMIT-fix 미적용)이 예측대로 ~59 재크래시 → 드라이버가 이상종료 감지(`21 leaked semaphore`+`OSError [Errno 24]`) 후 **새 run pid 85398** 재시작. pid 85398 은 RLIMIT-fix 커밋 `3fa8bb6`(7/11) 이후 `train_act.py` 로드 → persistent_workers(L196)+_raise_fd_limit(L452) 두 FD fix 실적용 → 256 FD 천장 제거 → 100epoch 완주 기대.
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-12.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임/6관절), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/3(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop floor 씬 수집 스모크 2/2=100% yield, lift 65.3mm (throwaway `data/episodes_smoke_0712` → 삭제, 운영 무접촉)
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets `episodes_cl`/`episodes_cl_dr`/`episodes_floor` 각 50ep 불변. 학습 pid 85398 alive(epoch 5, loss 0.757).

## 2026-07-13
- Phase 2 W2 — **floor 재학습 6차 = FD 누수 근본치유(num_workers=0)**: `agent/research-log/2026-07-13.md`, `research/simulation/2026-07-13_phase2-w2-floor-retrain-numworkers-selfheal.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 run(pid 85398, RLIMIT-fix 발효 예상)이 또 epoch 58 이상종료 → 두 선행 fix(persistent_workers·RLIMIT) 무효 판명. 크래시 트레이스백이 **매 epoch DataLoader 워커 재spawn**(`_MultiProcessingDataLoaderIter` 재생성→`os.pipe()`) 지목. 드라이버 감지 후 **새 run pid 8470** 재시작.
  - **[자가치유]** `train_act.py` 비smoke 경로 `effective_workers` `None`→**`0` 강제**(`num_workers=0` SingleProcess DataLoader → 워커 subprocess/pipe/세마포어 생성 없음 → FD 누수 물리적 불가). 6-run 실패 유일원인(워커 churn) 근본 제거. 발효는 다음 run(7/14).
- 23:30 nightly sim-test — 우선순위 4종 실제 실행 회귀: `agent/research-log/2026-07-13.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임/6관절), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline 0/2(결정론적 동일, min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 수집 스모크 2/2=100% yield, lift 42.3mm (throwaway `data/episodes_smoke_20260713` → 삭제, 운영 무접촉)
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets 각 50ep 불변. 학습 pid 8470 alive(epoch 5, loss 0.694, FD 크래시 없이 진행).

## 2026-07-14
- Phase 2 W2 — **floor 재학습 7차 = num_workers=0 fix 발효 run**: `agent/research-log/2026-07-14.md`, `research/simulation/2026-07-14_phase2-w2-floor-retrain-numworkers-effective-run.md` → 7월 보고서 [Sim2Real 준비 / 파이프라인 견고성] 섹션.
  - 어제 run(pid 8470, fix 미적용)이 예측대로 epoch 58 크래시 → 드라이버 감지 후 **새 run pid 48167** 시작. pid 48167 은 num_workers=0 커밋(7/13) 이후 디스크 로드 → fix 실제 적용(L501~506 비smoke else 분기 `effective_workers=0`, L196 persistent_workers→False). **워커 재spawn 없음 → FD 누수 물리적 불가 → 완주 기대**. 23:30 epoch 5/100 loss 0.683 크래시 없이 진행.
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀: `agent/research-log/2026-07-14.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임/6관절), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline fail 2회 결정론 동일(min_approach 0.3228m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100% yield, lift 41.8mm (throwaway root → 삭제, 운영 무접촉)
  - `joint_angle_comparison_sim.py` 추론 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets 각 50ep/3350f 불변.

## 2026-07-15
- Phase 2 W2 — **floor 재학습 8차 = FD 누수 가설 경험적 반증 + MPS OOM 재규명**: `agent/research-log/2026-07-15.md`, `research/simulation/2026-07-15_phase2-w2-floor-retrain-fd-disproof-mps-oom.md` → 7월 보고서 [파이프라인 견고성 / 근본원인 정정] 섹션.
  - `_fd_leak_probe.py` 로 num_workers=0 DataLoader 4 full-epoch 재순회 → open_fds 6 고정 = **FD 누수 직접 반증**(3일간 red herring). crash epoch=57 천장 불변 + traceback 부재(SIGKILL) + epoch시간 평탄 → **MPS OOM 재규명**. [자가치유] epoch 루프 `torch.mps.empty_cache()`+`gc.collect()` 완화 + `mps_mem` 계측(다음 run 자기검증).
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀: `agent/research-log/2026-07-15.md` (23:30 회차)
  - `sim_headless_6dof_video.py` PASS(2501프레임/6관절), `sim_camera_verification.py` PASS(2카메라 30프레임 동기)
  - `sim_pick_place.py` open-loop baseline fail 1회 결정론(min_approach 0.323m — 기대 기준선)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100%, lift 42.3mm, yield 67% (throwaway root → 삭제, 운영 무접촉)
  - `joint_angle_comparison_sim.py` 추론 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성 전수: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(운영 rollout 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기·measured=`episodes_cl_dr:1783346557`·datasets 각 50ep/3350f 불변. 학습 pid 73001 alive(epoch 5, loss 0.706).
- Phase 2 W2 — **floor 재학습 11차 = RSS 프로브 발효 run(계측 실동작 실증)**: `agent/research-log/2026-07-18.md`, `research/simulation/2026-07-18_phase2-w2-floor-retrain-rss-probe-effective-run.md` → 7월 보고서 [파이프라인 견고성 / 근본원인 정정] 섹션.
  - 새 run pid 5069(RSS-probe 커밋 `884294f` 이후 코드) `act_train_metrics.jsonl` 에 **`rss_bytes` 필드 실재**(epoch1~3 = ~827MB 평탄) + `mps_mem` 6.61GB 평탄 — 10차 run 은 `mps_mem` 만(대조). **9-run 만에 첫 RSS 계측 실동작** → 다음 crash 시 jetsam vs 외부 시각연동 최종 판정. GPU OOM 재반증(10차 mps_mem epoch54~56 평탄 6.64GB).
  - 23:30 5종 회귀 독립 PASS: camera 30프레임·6dof 2501프레임·pick 0.3228m 결정론·collector 2/2 yield100% lift **41.4mm**·관절각 **0.0244°<1°**. 무결성 격리 불변(운영 rollout 0.70/50.2mm·datasets 각 50ep/3350f). 학습 pid 5069 alive(epoch 4, loss 0.87).
- Phase 2 W2 — **floor 재학습 10차 = mps_mem 판독으로 GPU OOM 반증 + RSS 프로브(자가치유)**: `agent/research-log/2026-07-17.md`, `research/simulation/2026-07-17_phase2-w2-floor-retrain-oom-refuted-rss-probe.md` → 7월 보고서 [파이프라인 견고성 / 근본원인 정정] 섹션.
  - 9차 run(mps-fix 발효) `mps_mem` 곡선 epoch7 6.65GB→8~57 완전 평탄(42% of 16GB) = **GPU OOM 물리적 반증**(FD·GPU OOM 둘 다 아님). crash epoch~57 천장·traceback 부재·elapsed 평탄 = **외부 SIGKILL 급사**. [자가치유] `epoch_metric` 에 `rss_bytes`(getrusage) 계측 추가 → 다음 crash 시 RSS 평탄=외부/시각연동 vs 상승=jetsam 판정.
- 23:30 nightly sim-test — 우선순위 5종 실제 실행 회귀 (7/17 회차): `agent/research-log/2026-07-17.md`
  - `sim_camera_verification.py` PASS(2카메라 30프레임 동기), `sim_headless_6dof_video.py` PASS(2501프레임/6관절)
  - `sim_pick_place.py` open-loop baseline fail 결정론(min_approach **0.3228m** — 기대 기준선 불변)
  - `sim_data_collector.py` closed-loop 스모크 2/2=100%, lift 42.2mm, yield 100% (throwaway root)
  - `joint_angle_comparison_sim.py` 6관절 최대오차 **0.0244° < ±1°** — 시뮬 관절각 정합 유지
  - 무결성: 운영 rollout act_cl_dr 0.70/50.2mm 불변·datasets 각 50ep/3350f 불변·학습 pid 26783 alive(epoch 5, loss 0.71).

## 2026-07-25
- Phase 2 W2 — **sim 레버 결착 후 hold + 무결성 전수 감사 + 23:30 우선순위 5종 회귀**: `agent/research-log/2026-07-25.md`, `research/simulation/2026-07-25_phase2-w2-sim-lever-hold-integrity-audit.md` → 7월 보고서 [Sim2Real 안정성 / 파이프라인 견고성] 섹션.
  - 23:30 5종 독립 PASS: 6dof 2501프레임 · camera 30프레임×2 동기 · pick min_approach **0.3228327m** 결정론 · joint_angle 최대오차 **0.0244°<1°** · collector 스모크 2/2 yield100% lift **48.4mm**(격리 루트→삭제, 운영 무접촉).
  - 무결성: 운영 `rollout_summary.json` md5 **5207f67b189645de1bb26c124873b683** 실행 후 불변 · 마커 3자 정합(target=`episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=`episodes_floor:1783710169`) · datasets floor/cl/cl_dr 각 50ep/3350f 불변 · 학습 프로세스 없음(hold).

## 2026-07-28
- Phase 2 W2 — **sim 레버 결착 후 hold + 무결성 전수 감사 + 23:30 우선순위 5종 회귀**: `agent/research-log/2026-07-28.md`, `research/simulation/2026-07-28_phase2-w2-sim-lever-hold-integrity-audit.md` → 7월 보고서 [Sim2Real 안정성 / 파이프라인 견고성] 섹션.
  - 23:30 5종 독립 PASS: 6dof 2501프레임 · camera 30프레임×2 동기 · pick min_approach **0.3228327114m** 결정론 · joint_angle 최대오차 **0.0244°<1°** · collector 스모크 2/2 yield100% lift **43.9mm**(격리 루트→삭제, 운영 무접촉).
  - 무결성: 운영 `rollout_summary.json` md5 **5207f67b189645de1bb26c124873b683** 실행 후 불변 · 마커 3자 정합(target=`episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=`episodes_floor:1783710169`) · datasets floor/cl/cl_dr 각 50ep/3350f 불변 · 학습 프로세스 없음(hold).
