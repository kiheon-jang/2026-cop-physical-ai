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

## 2026-08-06
- Phase 3 W3 — **S1 리셋버튼 ACT 학습 완주 + 4-seed LED-latch 롤아웃 = 성공률 0.925**(W3 dated 8/19~8/25 조기 완주): `agent/research-log/2026-08-06.md`, `research/simulation/2026-08-06_phase3-w3-s1-act-rollout.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1)] **핵심 성과** 섹션.
  - **S1 ACT 학습**: PID 65874, `--epochs 30`, dataset `episodes_s1`(100ep/7,231f, top+closeup 2카메라) → ckpt `act_s1_sim/epoch_0029`, wall **38,065s(~10.6h)**, loss **0.0133**. **04:04 killer 관통**(`start_new_session` 분리, epoch_0019 06:11·epoch_0029 09:37 생존).
  - **4-seed 롤아웃**(N=10, LED latch 자동채점): seed42 **0.90** · seed7 0.90 · seed123 **1.00** · seed2026 0.90 → **평균 0.925**(37/40), median press 2.1~3.7mm(임계 1.5mm 위). Phase 3 완료 기준 0.70 초과. 산출물 `research/simulation/inference_progress/rollout_summary_s1[_seed*].json` 4종 실측 교차검증 일치.
  - 23:30 sim-test: sim_pcb_reset 4/4 PASS · 6dof 3회 2501프레임 · camera 30프레임×2 · pick(open-loop 알려진 0%, 참고).

## 2026-08-07
- Phase 3 W3 — **S1 4-seed 재측정 재현성 확인(0.925) + W4 hold + 23:30 헬스체크 3종 PASS**: `agent/research-log/2026-08-07.md`, `research/simulation/2026-08-07_phase3-w3-s1-remeasure-reproducibility-hold.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1) 재현성] 섹션.
  - **S1 재측정**(드라이버 STAGE=측정, 23:01~23:03, N=10 LED-latch): seed42/7/123/2026 = 0.90/0.90/1.00/0.90 → **평균 0.925(37/40)**, 8/6 최초 측정과 완전 동일 = **결정론적 재현**. ckpt 승격 복제 `epoch_0029_measured_0.925.bak`.
  - 23:30 sim-test 헬스체크: 6dof 2501프레임 9.9s · camera 30프레임×2 0.7s · pick min_approach **0.3228327114m** 결정론(open-loop 알려진 0%, 회귀 아님). MuJoCo 3.8.0 로드·step·렌더 전부 정상, 회귀 0.

## 2026-08-09
- Phase 3 W3 — **S1 hold 유지 + 무결성 감사 재확인(0.925 불변) + 23:30 렌더 헬스체크 3종 PASS**: `agent/research-log/2026-08-09.md`, `research/simulation/2026-08-09_phase3-w3-s1-hold-integrity-audit.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1) 안정성] 섹션.
  - **무결성(비파괴)**: 운영 `rollout_summary_s1.json` md5 **fbeef25775e5846ba2e3ce887afd1929** 8/8 대비 불변 · `cop_dataset_target`=`data/episodes_s1` · train_act proc 없음 · 마커 3자 정합 → 회귀/오염 0. 4-seed 0.925(37/40) 유지.
  - 23:30 sim-test 헬스체크: 6dof 2501프레임 · camera 30프레임×2(top 640×480+gripper 320×240) · pick min_approach **0.3228327114m**(open-loop 레거시 알려진 0%, 회귀 아님). MuJoCo 3.8.0 렌더 파이프라인 크래시 0. sim_data_collector SKIP(hold 오염 방지).

## 2026-08-10
- Phase 3 W3 — **S1 hold 유지 + 무결성 감사 재확인(0.925 불변) + 23:30 렌더 헬스체크 3종 PASS**: `agent/research-log/2026-08-10.md`, `research/simulation/2026-08-10_phase3-w3-s1-hold-integrity-audit.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1) 안정성] 섹션.
  - **무결성(비파괴)**: 운영 `rollout_summary_s1.json` md5 **fbeef25775e5846ba2e3ce887afd1929** 8/8·8/9 대비 불변 · `cop_dataset_target`=`data/episodes_s1` · train_act proc 없음 · 마커 3자 정합 → 회귀/오염 0. 4-seed 0.925(37/40) 유지.
  - 23:30 sim-test 헬스체크: 6dof 2501프레임 · camera 30프레임×2(top 640×480+gripper 320×240) · pick min_approach **0.3228327114m**(open-loop 레거시 알려진 0%, 회귀 아님). MuJoCo 3.8.0 렌더 파이프라인 크래시 0. sim_data_collector SKIP(hold 오염 방지).

## 2026-08-12
- Phase 3 W3 — **S1 hold 유지 + 무결성 감사 재확인(0.925 불변) + 23:30 렌더 헬스체크 3종 PASS**: `agent/research-log/2026-08-12.md`, `research/simulation/2026-08-12_phase3-w3-s1-hold-integrity-audit.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1) 안정성] 섹션.
  - **무결성(비파괴)**: 운영 `rollout_summary_s1.json` md5 **fbeef25775e5846ba2e3ce887afd1929** 8/8~8/11 대비 불변 · `cop_dataset_target`=`data/episodes_s1` · train_act proc 없음 · 마커 3자 정합 → 회귀/오염 0. 4-seed 0.925(37/40) 유지.
  - 23:30 sim-test 헬스체크: 6dof 2501프레임 · camera 30프레임×2 동기 · pick min_approach **0.3228327114m**(open-loop 레거시 알려진 0%, 회귀 아님). MuJoCo 3.8.0 렌더 파이프라인 크래시 0. sim_data_collector SKIP(hold 오염 방지).

## 2026-08-13
- Phase 3 W3 — **S1 hold 유지 + 무결성 감사 재확인(0.925 불변) + 23:30 렌더 헬스체크 3종 PASS**: `agent/research-log/2026-08-13.md`, `research/simulation/2026-08-13_phase3-w3-s1-hold-integrity-audit.md` → 8월 보고서 [ACT 학습 / Phase 3 PCB(S1) 안정성] 섹션.
  - **무결성(비파괴)**: 운영 `rollout_summary_s1.json` md5 **fbeef25775e5846ba2e3ce887afd1929** 8/8~8/12 대비 불변 · `cop_dataset_target`=`data/episodes_s1` · train_act proc 없음 · 마커 3자 정합 → 회귀/오염 0. 4-seed 0.925(37/40) 유지.
  - 23:30 sim-test 헬스체크: 6dof 2501프레임(3/3, wall 9.5~10.2s) · camera 30프레임×2 동기(2/2) · pick min_approach **0.3228327114m**(open-loop 레거시 결정론적 실패, 회귀 아님). MuJoCo 3.8.0 렌더 파이프라인 크래시 0. sim_data_collector SKIP(hold 오염 방지).
