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
