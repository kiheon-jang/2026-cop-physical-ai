# 2026-06-29 — closed-loop 자동수집 1사이클 완료/유지 검증

> Phase 1 - W4 - closed-loop 자동수집 1사이클 완료/유지 (PHASE_ROADMAP L162, 범위 6/22~6/30)
> 야간 전진은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.
> **STAGE=완료/유지** (데이터 50ep · 최종 성공률 0.7 · 목표 0.90).
> 본 회차 = STAGE 결과 검증·문서화·보고 (파이프라인 재실행 없음).

## 무엇을 했나

드라이버 출력 `STAGE=완료/유지` 를 받아, 산출물·마커·환경 무결성을 재확인하고 문서화했다.
파이프라인(수집/학습/측정)은 **재실행하지 않았다** (드라이버 담당).

## 어떻게 검증했나

### 1. 마커 정합 (재학습/재측정 불필요 확인)
- `logs/cop_trained_on.marker` — mtime 6/24 17:12
- `logs/cop_measured.marker` — mtime 6/25 23:00
- → 현 체크포인트(epoch_0099)와 정합 → 드라이버가 재학습·재측정 없이 유지 (설계대로)

### 2. 산출물 디스크 검증
- `data/episodes_cl`: **50 ep / 3350 frame / robot=so101** ✓ (`meta/info.json`)
- `checkpoints/act/epoch_0099/model.safetensors`: **mtime 6/25 02:17, 336MB** (closed-loop 신선) ✓
- `research/simulation/inference_progress/rollout_summary.json`:
  - **10 rollout 중 7 성공 = 0.70**, median lift **43.7mm**, threshold 40mm ✓
  - 성공 7건: max_lift 43.7~45.6mm / 실패 3건(rollout 2/5/8): 3.7~6.9mm → **이분 분포**(간헐적 그립 실패형 모방격차)
  - device=cpu, wall 13.6s

### 3. 환경 무결성 (재학습 아님)
- `.venv/bin/python3` → mujoco **3.8.0** import ✓ (Apple Silicon ARM64)
- `SO-ARM100/Simulation/SO101/scene_grasp_pads.xml` 존재 ✓
- git 서브모듈 없음 → main repo 직접 커밋 안전 ✓
- git status: `2026-06-29.html` 일일 리포트(미추적)만 존재, 워킹트리 그 외 clean

## 관찰 / 이슈

- **홀딩 상태가 정상 동작**: 마커가 현 체크포인트와 일치 → STAGE=완료/유지. 신규 사이클은 드라이버의 마커 리셋 / `COP_TARGET_EP` 상향 시에만 트리거 → 본 회차 수동 트리거 안 함.
- **성공률 간극(70% < 90%)**: ACT 모방격차 + sim 데이터 50ep 한계. 90%+ 는 Sim2Real 진입 조건이라 데이터 증대(50→200ep)/씬 다양화가 자연스러운 후속.
- **자가치유 없음** — 드라이버 STAGE 정상, 산출물·마커 정합, 운영 데이터셋 무손상, 에러 없음.

## 다음 단계와의 연결

- Phase 1 W4 dated 항목(6/22~6/30) 사실상 종료. 남은 것 = PHASE_ROADMAP L168 "학습 모델 Orin Nano 배포" → 외부 의존(장기헌 SSH, external-dependencies 우선순위2) 미수신으로 이연. `[ ]` 유지.
- 7월 Phase 2(Sim2Real) 진입 전 sim 성공률 70%→90%+ 향상(데이터 증대/씬 다양화) — 다음 사이클은 드라이버가 마커 리셋/타깃 상향 시 자동 전진.
