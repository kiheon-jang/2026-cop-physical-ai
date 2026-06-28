# closed-loop 자동수집 1사이클 — 완료/유지 검증 (2026-06-29 월)

> Phase 1 - W4 - closed-loop 자동수집 1사이클 완료/유지 (PHASE_ROADMAP L162, 6/22~6/30 범위).
> 야간 전진은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.
> 01:00 출력: **STAGE=완료/유지  데이터 50ep · 최종 성공률=0.7 (목표 0.90)**.
> 본 회차 = STAGE 결과 검증·문서화·보고 (파이프라인 수집/학습/측정 재실행 없음).

## 무엇을 했나

드라이버가 마커 정합을 확인하고 재학습/재측정 없이 사이클을 **유지**(설계대로). 본 에이전트는
산출물·마커·환경을 디스크에서 재검증만 수행하고 재실행하지 않았다.

## 어떻게 검증했나 (디스크 재검증, 재실행 아님)

- **마커 정합** (드라이버 holding 판정 근거):
  - `logs/cop_trained_on.marker` = mtime 6/24 17:12
  - `logs/cop_measured.marker` = mtime 6/25 23:00
  - → 현 체크포인트(epoch_0099, 6/25 02:17)와 정합 → 재학습/재측정 트리거 없음.
- **산출물**:
  - `data/episodes_cl`: total_episodes=50, total_frames=3350, robot_type=so101 ✓
  - `checkpoints/act/epoch_0099/model.safetensors`: 335,947,896 B (~336MB), mtime 6/25 02:17 (closed-loop 신선) ✓
  - `research/simulation/inference_progress/rollout_summary.json`:
    rollouts=10, success=7, **success_rate=0.70**, median_lift_mm=**43.7**, threshold 40mm, device=cpu ✓
    - 실패 3건 = rollout 2/5/8 (max_lift 3.7~6.9mm) / 성공 7건 (43.7~45.2mm) → ~44mm vs ~0mm 이분 분포.
- **환경 무결성**: git status clean, 서브모듈 없음 → main repo 직접 커밋 안전.

## 관찰

- holding 상태 정상: 마커 = 현 체크포인트 일치 → 신규 사이클은 드라이버의 마커 리셋 또는
  `COP_TARGET_EP` 상향 시에만 트리거. 본 회차 수동 트리거하지 않음.
- 성공률 간극(70% < 90%): ACT 모방격차 + sim 50ep 데이터 한계. 90%+ 는 Sim2Real 진입 조건이라
  데이터 증대(50→200ep)/씬 다양화가 자연스러운 후속.
- 6/27·6/28 기록과 동일 패턴 — 회귀 없음.

## 다음 단계 연결

- Phase 1 W4 dated 항목 사실상 종료. 남은 것 = PHASE_ROADMAP L168 "학습 모델 Orin Nano 배포"
  → 외부 의존(장기헌 SSH, external-dependencies 우선순위2) 미수신으로 이연. `[ ]` 유지.
- 7월 Phase 2(Sim2Real) 진입 전 sim 성공률 70%→90%+ 향상(데이터 증대/씬 다양화)은 드라이버가
  마커 리셋/타깃 상향 시 자동 전진.
