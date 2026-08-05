# 2026년 8월 월간 보고서 증거 후보

> 8월 보고서 매핑: Phase 2 (Sim2Real) hold 지속 + Phase 3(PCB) 진입 검토.

## 2026-08-01
- Phase 2 W2 — **sim 레버 결착 후 hold + 무결성 전수 감사 + 23:30 우선순위 5종 회귀**: `agent/research-log/2026-08-01.md`, `research/simulation/2026-08-01_phase2-w2-sim-lever-hold-integrity-audit.md` → 8월 보고서 [Sim2Real 안정성 / 파이프라인 견고성] 섹션.
  - 23:30 5종 독립 PASS: 6dof 2501프레임 · camera 30프레임×2 · pick min_approach **0.3228327114m** 결정론 · joint_angle 최대오차 **0.0244°<1°** · collector 2/2 yield100% lift **43.4/41.9mm**(격리 루트, 운영 무접촉).
  - 무결성: 운영 `rollout_summary.json` md5 **5207f67b189645de1bb26c124873b683** 실행 후 불변(7/22~7/31 동일) · 마커 3자 정합(target=`episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=`episodes_floor:1783710169`) · datasets floor/cl/cl_dr 각 50ep/3350f 불변 · 학습 프로세스 없음(hold).

## 2026-08-04
- Phase 2 W2 — **sim 레버 결착 후 hold + 우선순위 5종 회귀 재실행 PASS + 무결성 전수 감사**: `agent/research-log/2026-08-04.md`, `research/simulation/2026-08-04_phase2-w2-sim-lever-hold-integrity-audit.md` → 8월 보고서 [Sim2Real 안정성 / 재현성] 섹션.
  - 5종 재실행 PASS: 6dof 2501프레임 · camera 30프레임×2 · pick min_approach **0.3228327114m** 결정론 · joint_angle 최대오차 **0.0244°<1°** · collector 2/2 yield100% lift **42.6mm**(격리 루트 `/tmp`, 운영 무접촉).
  - 무결성: md5 **5207f67b189645de1bb26c124873b683** 불변(sr 1.0, ckpt `act_floor/epoch_0041`) · 마커 3자 정합 불변 · datasets 50ep/3350f 불변 · 학습 프로세스 없음.

## 2026-08-05
- Phase 3 W2 — **S1 합성 결착 + W3 ACT 학습 조기 착수(in-flight) + 우선순위 6종 회귀**: `agent/research-log/2026-08-05.md`, `research/simulation/2026-08-05_phase3-w2-s1-synth-hold-w3-enabler.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB] 섹션.
  - **W3 S1 ACT 학습 in-flight**(PID 65874, `--epochs 30`, dataset `episodes_s1` → ckpt `act_s1_sim`, **top+closeup 2카메라**): epoch0 완주 l1 **0.063**, epoch1 loss 1.36 정상 수렴 → W3 인에이블러(`COP_CAMERA_KEYS`/`COP_DATASET_REPO_ID`) 2카메라 학습 경험적 확증.
  - **S1 데이터셋**: `episodes_s1` **100ep/7,231frame** · v3.0 · 30fps · top+closeup · LED latch 자동라벨.
  - 6종 회귀 PASS: 6dof 2501프레임 · camera 30프레임×2 · pick min_approach **0.3228327114m** 결정론 · joint_angle 최대오차 **0.0244°<1°** · collector 2/2 yield100% lift 42.1mm · **sim_pcb_reset(S1 트윈) 4/4 PASS**.
  - 무결성: 운영 `rollout_summary.json` md5 **5207f67b189645de1bb26c124873b683** 불변(7/22~8/04 동일, sr 1.0 act_floor/epoch_0041) · Phase 2 산출물 회귀/오염 0.
