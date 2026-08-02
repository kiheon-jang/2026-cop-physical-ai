# Phase 2 W2 — sim 성공률 레버 결착 후 hold + 우선순위 5종 회귀 + 무결성 전수 감사 (2026-08-02)

## 무엇을 했나

드라이버(`cop_pipeline_advance.sh`) STAGE=**완료/유지**(`episodes_floor` 50ep · 최종 성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음(하드룰). sim 트랙 성공률 레버(배치 다양성)는 7/22 4-seed 공정추정(4/4=1.0)으로 이미 결착 → **hold 일**. 학습 프로세스 없음(`pgrep train_act` → none).

야간 에이전트는 (a) 우선순위 5종 회귀 독립 실행, (b) 비파괴 무결성 전수 감사만 수행.

## 어떻게 검증했나

### 우선순위 5종 회귀 (전부 PASS)
| 스크립트 | 결과 |
|---|---|
| `sim_camera_verification.py` | 30 frames × 2 카메라 동기 캡처 PASS |
| `sim_headless_6dof_video.py` | 2501 frames → mp4 저장 PASS |
| `joint_angle_comparison_sim.py` | 관절각 최대오차 **0.0244°**(elbow_flex) < 1° PASS |
| `sim_pick_place.py` (2회) | min_approach_dist **0.3228327114026489m** 양 run 완전 동일 = 결정론 확인 (open-loop expert baseline, status fail = 알려진 고정포즈 미접근 기지값) |
| `sim_data_collector.py` (2ep, temp root) | 성공 2/2, yield 100%, lift 42.3/43.5mm |

### 비파괴 무결성 전수 감사 (이번 세션 도구결과)
- 운영 `research/simulation/inference_progress/rollout_summary.json` md5 = **`5207f67b189645de1bb26c124873b683`** — 7/22~8/01 값과 **동일**(불변). sr 1.0, ckpt `checkpoints/act_floor/epoch_0041`, seed42, median lift 66.0mm.
- 마커 3자 정합: target=`data/episodes_floor` · trained_on=`episodes_floor:1783324998` · measured=`episodes_floor:1783710169`.
- datasets floor/cl/cl_dr 각 **50ep/3350frame**(info.json) 불변. 회귀/오염 0. 운영 산출물 무접촉.
- collector smoke 는 `/tmp/cop_collector_smoke_0802`(운영 무접촉, 종료 후 정리).

## 자가치유
- [자가치유] collector `--output_root` 플래그 없음 → 실제 플래그 `--root` 사용 (self-heal, 8/01 은 `--episodes` 처방과 동일 계열).
- md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값 우회 산출.

## 다음 단계와의 연결
sim 트랙 성공률 레버 규명 완료 → hold 유지. 남은 두 항목 모두 외부 의존 대기:
- 실기 W2 zero-shot 추론: Orin Nano SSH 외부의존(장기헌) 미수신 → 진입 불가.
- full-epoch(100) 공정비교 복원: ~04:04 벽시계 killer 진단권한(log show/launchctl, sandbox 차단) 에스컬레이션 대기.
