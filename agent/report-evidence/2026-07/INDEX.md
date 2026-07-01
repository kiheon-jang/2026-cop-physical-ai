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
