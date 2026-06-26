# 2026년 6월 월간 보고서 증거 후보

## 2026-06-02
- 시뮬 테스트 결과 요약: `agent/research-log/2026-06-02.md` 참조
- `sim_data_collector.py` 에피소드 수집 결과 (200 에피소드): `agent/research-log/2026-06-02.md` 참조

## 2026-06-03
- `sim_data_collector.py` 실행 결과 메트릭: `agent/research-log/2026-06-03.md` 참조
- `sim_headless_6dof_video.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/sim_6dof_animation.mp4`
- `sim_camera_verification.py` 이미지: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/overhead_frame_0000.png`, `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/gripper_frame_0000.png`
- `sim_pick_place.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/pick_place_demo.mp4`

## 2026-06-04
- 시뮬레이션 스크립트 실행 성공률 (100%): `agent/research-log/2026-06-04.md` 참조
- `sim_headless_6dof_video.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/sim_6dof_animation.mp4`
- `sim_camera_verification.py` 이미지: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/camera_top_frame_0.png`
- `sim_pick_place.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/pick_place_demo.mp4`
- `sim_data_collector.py` 데이터셋 메타정보: `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes/info.json`
## 2026-06-06
- `sim_headless_6dof_video.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/sim_6dof_animation.mp4`
- `sim_camera_verification.py` 이미지: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/top_view_frame_0.png`, `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/gripper_view_frame_0.png`
- `sim_pick_place.py` 비디오: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/pick_place_demo.mp4`
- `sim_data_collector.py` 데이터셋 메타정보: `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes/meta/info.json`
- `sim_data_collector.py` 데이터셋 파일: `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes/data/chunk-000/file-000.parquet`

## 2026-06-07
- `sim_pick_place.py` 성공/실패 JSON stdout 보고 추가 (`research/simulation/2026-06-07_pick-place-success-reporting.md`)
- 데이터셋 현황 확인 (filesystem 기반): `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes/meta/info.json` (200 ep / 12400 frames / 30fps) — Phase 1 W1-2 합성 완료 상태
- 23:30 nightly sim-test: 런타임 실행 sandbox 차단으로 메트릭 미수집 (`agent/research-log/2026-06-07.md` 자가치유 기록)

## 2026-06-08
- Phase 1 W3 사전 작업: `scripts/train_act.py::load_dataset()` 플레이스홀더 → 실제 구현 교체 (`research/simulation/2026-06-08_train-act-load-dataset.md`)
- 23:30 nightly sim-test (2회차): `.venv/bin/python3` 및 Obsidian `cp` sandbox 차단 — 런타임 메트릭 미수집. `git` 명령은 동작 확인 (1차 기록 정정). 파일시스템 증거: `data/episodes/meta/info.json` 200 ep / 12400 frames 유지 (`agent/research-log/2026-06-08.md`)

## 2026-06-09
- Phase 1 W3 사전 작업: `scripts/train_act.py::build_model()` 플레이스홀더 → 실제 구현 + lerobot import 경로 수정 (`research/simulation/2026-06-09_train-act-build-model.md`) → 6월 보고서 [2.사전학습] 섹션 후보.
- 23:30 nightly sim-test (3회차): `.venv/bin/python3` sandbox 차단 지속 — 런타임 메트릭 미수집. 파일시스템 증거: `data/episodes/meta/info.json` 200 ep / 12400 frames 유지 (`agent/research-log/2026-06-09.md`)

## 2026-06-10
- Phase 1 W3 사전 작업: `scripts/train_act.py::train()` 루프 placeholder → 본 구현 + `_save_checkpoint()` + `argparse`(`--smoke`/`--epochs`) (`research/simulation/2026-06-10_train-act-train-loop.md`) → 6월 보고서 [2.사전학습] 섹션 W3 진입 사전 준비 증거.
- 23:30 nightly sim-test (4회차): `.venv/bin/python3` sandbox 차단 지속 (4일 연속) — 런타임 메트릭 미수집. 파일시스템 증거: `data/episodes/meta/info.json` 200 ep / 12400 frames / so101 유지 (`agent/research-log/2026-06-10.md`)

## 2026-06-11
- Phase 1 W3 사전 작업: `scripts/train_act.py` smoke 경로 점검 — 경로 정정 + `resolve_device()` + `--device {cpu,cuda,mps}` + `logs/act_train_metrics.jsonl` JSONL append + DataLoader pin_memory 조건부 (`research/simulation/2026-06-11_train-act-smoke-path.md`) → 6월 보고서 [2.사전학습] 섹션 W3 진입 사전 준비 증거.
- 23:30 nightly sim-test (5회차): `.venv/bin/python3` sandbox 차단 지속 (5일 연속) — 런타임 메트릭 미수집. 파일시스템 증거: `data/episodes/meta/info.json` 200 ep / 12400 frames / so101 유지 (`agent/research-log/2026-06-11.md`)

## 2026-06-14
- Phase 1 W3 사전 준비 D4: `scripts/check_act_train.sh` 신규 — ACT 학습 진행률 결정론적 status 출력 (pid 살아있음 / ckpt 진행률 / 로그 신선도 / 표준 tail 블록 / exit code 0·1·2·3 의미론). `start_act_train.sh` 의 짝. 6월 보고서 [2.사전학습] W3 일일 운영 절차 증거 (`research/simulation/2026-06-14_check-act-train-status.md`).
- 23:30 nightly sim-test (8회차): `.venv/bin/python3` 및 `bash` sandbox 차단 지속 (8일 연속) — 런타임 메트릭 미수집. 23:00 산출물(check_act_train.sh + 동일 일자 doc) 파일시스템 존재 확인 (`agent/research-log/2026-06-14.md`)
- 23:30 nightly sim-test (9회차, 4회차 블록): `.venv/bin/python3` / `bash scripts/check_act_train.sh` sandbox 차단 지속 (9일 연속) — 런타임 메트릭 미수집. `logs/` 부재로 학습 미시작 상태 간접 확인 (`agent/research-log/2026-06-14.md` 4회차 블록)

## 2026-06-15
- Phase 1 W3 D1: ACT smoke + nohup 학습 시작 시도 — `chmod +x` / `.venv/bin/python3 scripts/train_act.py --smoke` / `bash scripts/check_act_train.sh` 본 회차 모두 sandbox 거절 (10일 연속). 정적 점검 (3축 글로브 패턴 정합) 통과만 (`research/simulation/2026-06-15_act-w3-d1-smoke-attempt.md`). PHASE_ROADMAP W3 첫 두 항목 `[ ]` 유지. 사용자 수동 절차 통과 시점에 익일 nightly 가 `check_act_train.sh` status 블록 capture 예정 (`agent/research-log/2026-06-15.md`)

## 2026-06-16
- Phase 1 W3 D2: ACT 학습 status 점검 — `logs/`/`checkpoints/` 미존재, `start_act_train.sh`/`check_act_train.sh` 실행비트 미부착 정적 확인. `chmod` / `.venv/bin/python3` / Obsidian `cp` sandbox 거절 (15일+1 연속). 사용자 수동 절차 6/15 기준 미시행 그대로 (`research/simulation/2026-06-16_act-w3-d2-status-check.md`). 23:30 nightly sim-test (11회차): 동일 sandbox 패턴, 23:00 회차 정적 점검 결과가 본 일자 최종 상태 (`agent/research-log/2026-06-16.md`)

## 2026-06-19
- Phase 1 W3 D5: ACT 학습 status 점검 — `logs/`/`checkpoints/` 미존재 그대로, scripts/ 6/14 이후 변경 없음. 사용자 수동 절차 미시행 (`research/simulation/2026-06-19_act-w3-d5-status-check.md`). 23:30 nightly sim-test (13회차): 우선순위 시뮬 4종 실행 `.venv/bin/python3` sandbox 거절 19일 연속 — 런타임 메트릭 0건. 파일시스템 증거 `data/episodes/meta/info.json` 200 ep / 12400 frames / so101 유지 (`agent/research-log/2026-06-19.md`)

## 2026-06-21
- Phase 1 W3 D7 (마지막일): ACT 학습 진행 확인 — sandbox 차단 해소(commit `6e5f7d5`) + 런타임 버그 3건 수정(commit `98be446`) 후 학습 가동 중. PID 40835 alive, epoch 28→29/100, loss 0.0032 단조 감소. 체크포인트 `checkpoints/act/epoch_0009/`, `epoch_0019/` 자동 저장. 완료 예상 6/22 22~23시 (`research/simulation/2026-06-21_act-w3-d7-training-progress.md`). → 6월 보고서 [2.사전학습] W3 ACT 학습 진행 증거.
- 23:30 nightly sim-test (16회차, v3.2): sandbox 해소 후 첫 정상 회차. 우선순위 3종 정상 실행 (sim_camera_verification 3/3, sim_headless_6dof_video 2/2, sim_pick_place 3/3 스크립트 실행 / 0/3 pick 목표 — 미학습 결정적 데모로 known). sim_data_collector 학습 CPU 경합 회피로 skip. 산출 비디오 갱신: `research/simulation/video/sim_6dof_animation.mp4`, `pick_place_demo.mp4` (`agent/research-log/2026-06-21.md` 23:30 회차 블록).

## 2026-06-22
- Phase 1 W4 D1 (학습 모니터링): ACT 학습 PID 40835 alive, epoch 34/100 진행 (loss 0.00272 단조 감소 유지). 평균 epoch 소요 ~20.9분 → 완료 예상 6/23 00~01시. 체크포인트 `epoch_{0009,0019,0029}/` 정상 저장 (`research/simulation/2026-06-22_act-w4-d1-training-monitor.md`) → 6월 보고서 [2.사전학습] W3 학습 진행 증거.
- 23:30 nightly sim-test (17회차, v3.2): 우선순위 3종 회귀 정상 (sim_camera_verification 5/5 mean 1.01s, sim_headless_6dof_video 5/5 mean 17.79s, sim_pick_place 스크립트 5/5 / 태스크 0/5 known). 학습 가동 중 병행 — CPU 경합 영향 없음. sim_data_collector 6/23 학습 완료 후 진입 (`agent/research-log/2026-06-22.md` 23:30 회차 블록).
- 23:00 회차 (v3.2): **ACT 100 epoch 학습 완료 확정** (PID 40835 종료, 32.7h, final loss 0.001202 단조 감소). `models/act_phase1.pt` 320MB 로컬 보존 (gitignored), `models/act_phase1.config.json` 커밋. PHASE_ROADMAP W3 4항목 모두 `[v]` (`research/simulation/2026-06-22_act-training-complete.md`) → 6월 보고서 [2.사전학습] **학습 완료** 핵심 증거.
- 23:30 회차 (학습 종료 후 회귀): 학습 완료 직후 priority 3종 단독 가동 회귀 통과 (sim_camera_verification 5/5, sim_headless_6dof_video 5/5, sim_pick_place 스크립트 5/5 / 태스크 0/5 결정성 동일 수치 5회 일치). sim_data_collector 보류 (W4 grasp 정상화 작업 영역, 새 expert 합의 전 수집 무의미) (`agent/research-log/2026-06-22.md` 학습 종료 후 회귀 블록).

## 2026-06-24
- Phase 1 W4: closed-loop 자동수집 1사이클 진행(수집✓ 50ep/3350frame → ACT 재학습 epoch 64→69/100 진행 → 측정대기). 결정론적 드라이버 `cop_pipeline_advance.sh` 가 전진 (`research/simulation/2026-06-24_closed-loop-cycle1-progress.md`) → 6월 보고서 [2.사전학습] closed-loop 핵심 증거.
- 23:30 nightly sim-test (v3.2): headless 우선 3종 스모크 정상 — sim_headless_6dof_video(2501 frame 6관절 비디오), sim_camera_verification(듀얼카메라 30 frame), sim_pick_place(스크립트 정상 / open-loop grasp 0%·32cm 미달 = known 결함). sim_data_collector 는 활성 파이프라인 드라이버 소유·학습 중 → 의도적 skip. 메모리 83.7%/2.8GB가용 (`agent/research-log/2026-06-24.md` 23:30 회차 블록).
- open-loop vs closed-loop grasp 대비: `sim_pick_place.py` 0%(32cm) ↔ closed-loop 재학습(rollout 측정 학습완료 후) → 6월 보고서 [2.사전학습] open/closed-loop 대비 증거.

## 2026-06-25
- Phase 1 W4: **closed-loop 자동수집 1사이클 완주** — 수집 50/50(yield 91%, 3350 frame) → ACT 100 epoch(final loss 0.004564) → rollout 10중 7성공 **70%**, median lift 43.7mm. open-loop 0% → closed-loop 70% end-to-end 입증. PHASE_ROADMAP L162 `[v]` (`research/simulation/2026-06-25_closed-loop-cycle1-complete.md`) → 6월 보고서 [2.사전학습] **핵심 증거**.
- 23:30 nightly sim-test (v3.2): 우선순위 4종 실제 실행 회귀 통과 — sim_headless_6dof_video 2/2(2501 frame, ~9.3s), sim_camera_verification 3/3(듀얼카메라 60 img, ~0.6s), sim_pick_place 2/2 스크립트(open-loop grasp 0%·32cm 미달 = known), sim_data_collector 스모크 2/2(yield 100%, lift 43.5mm, `/tmp` 격리). 디스크 검증: `episodes_cl` 50ep/3350frame, `rollout_summary.json` 70%/43.7mm 정합. 환경 mujoco 3.8.0/.venv (`agent/research-log/2026-06-25.md` 23:30 회차 블록).
- closed-loop rollout 70%(7/10) vs open-loop `sim_pick_place.py` 0% 실측 대조 → 6월 보고서 [2.사전학습] open/closed-loop 대비 핵심 증거.
- sim 스크립트 회귀 통과(6dof/camera/collector 100% 성공) → 6월 보고서 [2.시뮬환경] 환경 안정성 근거.

## 2026-06-26
- Phase 1 W4: closed-loop 1사이클 **완료/유지** — 드라이버 STAGE=완료/유지(데이터 50ep, 성공률 0.70/목표 0.90). 마커 정합 확인, 재학습·재측정 없이 상태 유지. 디스크 검증: `episodes_cl` 50ep/3350frame, `epoch_0099` mtime 6/25 02:17, `rollout_summary.json` 70%/43.7mm 정합 (`research/simulation/2026-06-26_pipeline-hold-cycle1-70pct.md`) → 6월 보고서 [2.사전학습] 1사이클 결과 유지 증거.
- 23:30 nightly sim-test (v3.2): 우선순위 4종 실제 실행 회귀 통과 — sim_headless_6dof_video 3/3(2501 frame, 9.3~10.0s), sim_camera_verification 3/3(듀얼카메라 30 frame, ~0.6s), sim_pick_place 3/3 스크립트(open-loop grasp 0%·32cm 미달 = known 레거시), sim_data_collector closed-loop 스모크 3/3(yield 100%, lift 42.1mm, `/tmp` 격리). 환경 mujoco 3.8.0/.venv (`agent/research-log/2026-06-26.md` 우선순위 스크립트 직접 실행 블록) → 6월 보고서 [2.시뮬환경] 환경 안정성 근거.
- closed-loop rollout 70%(7/10) vs open-loop `sim_pick_place.py` 0%(32cm) 대조 유지 → 6월 보고서 [2.사전학습] open/closed-loop 대비 증거.
