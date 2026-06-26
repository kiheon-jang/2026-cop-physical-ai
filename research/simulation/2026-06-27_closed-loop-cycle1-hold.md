# closed-loop 자동수집 1사이클 — 완료/유지 회차 (2026-06-27)

> Phase 1 · W4 (6/22~6/30). 야간 전진은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.
> 01:00 드라이버 출력 = **STAGE=완료/유지 · 데이터 50ep · 최종 성공률=0.7 (목표 0.90)**.
> 본 회차 역할: STAGE 결과 검증·문서화·보고 + sim 환경 무결성 재확인. **파이프라인 재실행 없음**(드라이버 담당).

## 한 일

1사이클(수집→학습→측정)은 6/25 23:00 완주됨. 오늘은 마커·산출물 정합을 재확인하여 드라이버가 왜 재학습/재측정 없이 **완료/유지**를 출력했는지 검증했다.

### 드라이버 상태 근거 (마커)
- `logs/cop_trained_on.marker` = `1782287560`
- `logs/cop_measured.marker` = `1782134830`
- 두 마커(학습 대상 모델 서명 / 측정 대상 모델 서명)가 현재 체크포인트와 정합 → 드라이버가 "재실행 불필요" 판정 → STAGE=완료/유지. 신규 사이클은 드라이버가 마커 리셋 또는 `COP_TARGET_EP` 상향 시에만 트리거(설계대로).

### 산출물 디스크 검증
- `data/episodes_cl`: **50 ep / 3350 frame / robot=so101** (meta/info.json) ✓
- `checkpoints/act/epoch_0099/model.safetensors`: mtime **6/25 02:17**, 335,947,896 B (closed-loop 학습 신선) ✓
- `research/simulation/inference_progress/rollout_summary.json`:
  - rollouts 10 / success **7** / **success_rate 0.70**
  - median_lift **43.7mm**, lift_threshold 40mm, device cpu, wall 13.6s
  - 실패 3건 = rollout 2/5/8, max_lift 3.7~6.9mm (그립 미형성). 성공 7건은 43.7~45.6mm 안정.

### 환경 무결성 재확인 (재학습 아님)
- `.venv/bin/python3` → **mujoco 3.8.0** import ✓ (Apple Silicon)
- `SO-ARM100/Simulation/SO101/scene_grasp_pads.xml` 존재 ✓
- git 서브모듈 없음 → main repo 직접 커밋 안전 ✓

## 어떻게 검증했나
- 메트릭 출처 = 드라이버가 6/25 생성한 `rollout_summary.json` + `cop_rollout.log` (10/10 rollout 라인 일치).
- 본 회차는 측정기를 다시 돌리지 않고 디스크 산출물·마커만 대조 → 결정론적 일치 확인.

## 다음 단계로의 연결
- Phase 1 W4 dated 항목은 사실상 종료. 남은 단 하나 = PHASE_ROADMAP L168 **"학습 모델 Orin Nano 배포"** → 외부 의존(장기헌 SSH 접속 정보, external-dependencies 우선순위2) 미수신으로 이연. `[ ]` 유지.
- 7월 Phase 2(Sim2Real) 진입 전 sim 성공률 70%→90%+ 향상 여지: 데이터 증대(50→200ep) / 씬 다양화. 다음 사이클은 드라이버가 마커 리셋·타깃 상향 시 자동 전진.

## 자가치유
- 없음 — 드라이버 STAGE 정상, 마커·산출물 전부 존재·정합, 환경 스모크 통과, 에러 없음.
