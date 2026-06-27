# closed-loop 자동수집 1사이클 — 완료/유지 검증 (2026-06-28 일요일)

> Phase 1 · W4 (6/22~6/30 범위). 야간 전진은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.
> 01:00 드라이버 출력: **STAGE=완료/유지 · 데이터 50ep · 최종 성공률 0.7 (목표 0.90)**.
> 본 회차 = STAGE 결과 검증·문서화·보고 + sim 환경 무결성 재확인. **파이프라인 재실행 없음.**

## 무엇을 했나

드라이버가 마커 정합으로 STAGE=완료/유지를 출력한 상태를, 디스크 산출물 대조로 독립 검증했다.
새 수집/학습/측정은 트리거하지 않았다(설계대로 드라이버 담당).

### 마커 정합 (재학습/재측정 불필요 근거)
- `logs/cop_trained_on.marker` = `1782287560` (mtime 6/24 17:12)
- `logs/cop_measured.marker`  = `1782134830` (mtime 6/25 23:00)
- 두 마커가 현 체크포인트/측정 산출물과 정합 → 드라이버가 재실행 없이 유지 출력.

## 어떻게 검증했나

| 산출물 | 검증값 | 상태 |
|---|---|---|
| `data/episodes_cl` | 50 ep / 3350 frame / robot=so101 (info.json) | ✓ |
| `checkpoints/act/epoch_0099/model.safetensors` | mtime 6/25 02:17, 336MB (closed-loop 신선) | ✓ |
| `research/simulation/inference_progress/rollout_summary.json` | 10 rollout 중 **7 성공 = 0.70**, median lift **43.7mm**, threshold 40mm | ✓ |
| 실패 케이스 | rollout 2/5/8 (max_lift 3.7~6.9mm — 들어올림 실패) | ✓ 일관 |
| `.venv` mujoco | **3.8.0** import (Apple Silicon ARM64) | ✓ |
| `SO-ARM100/Simulation/SO101/scene_grasp_pads.xml` | 존재 | ✓ |
| git 서브모듈 | 없음 → main repo 직접 커밋 안전 | ✓ |

rollout_summary 세부: 성공 7건 max_lift 0.0437~0.0456m, 실패 3건 0.0037~0.0069m → **이분 분포**(잡으면 ~44mm 들어올림, 놓치면 거의 0). 모방격차가 "간헐적 그립 실패" 형태로 나타남을 재확인.

## 관찰 / 이슈

- **홀딩 상태가 정상 동작**: 마커가 현 체크포인트와 일치 → 드라이버 STAGE=완료/유지. 신규 사이클은 드라이버의 마커 리셋 / `COP_TARGET_EP` 상향 시에만 트리거. 본 회차 수동 트리거 안 함.
- **성공률 간극(70% < 90%)**: ACT 모방격차 + sim 데이터 50ep 한계. 90%+ 는 Sim2Real(7월 Phase 2) 진입 조건 → 데이터 증대(50→200ep)/씬 다양화가 자연스러운 후속.
- **[자가치유] 없음** — 드라이버 STAGE 정상, 산출물·마커 정합, 운영 데이터셋 무손상, 에러 없음, git clean.

## 다음 단계로의 연결

- Phase 1 W4 dated 항목 사실상 종료. 남은 것 = PHASE_ROADMAP L168 "학습 모델 Orin Nano 배포" → 외부 의존(장기헌 SSH, external-dependencies 우선순위2) 미수신으로 이연. `[ ]` 유지.
- 7월 Phase 2(Sim2Real) 진입 전 sim 성공률 70%→90%+ 향상은 드라이버가 마커 리셋/타깃 상향 시 자동 전진.
