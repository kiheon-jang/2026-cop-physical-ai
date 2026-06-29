# closed-loop 자동수집 1사이클 — 완료/유지 (W4 마지막 날) — 2026-06-30

## 단계
Phase 1 - W4 - **closed-loop 자동수집 1사이클 완료/유지** (PHASE_ROADMAP L162, 범위 6/22~6/30).
오늘 = W4 dated 범위의 **마지막 날**. 야간 전진은 결정론적 드라이버 `scripts/cop_pipeline_advance.sh` 가 처리.

## 드라이버 출력 (2026-06-30 01:00, 재실행 금지)
```
STAGE=완료/유지  데이터 50ep · 최종 성공률=0.7 (목표 0.90)
한 사이클 완료. 성공률 미달이면 COP_TARGET_EP 상향 또는 데이터 재수집(마커 삭제)으로 다음 사이클 트리거.
```
본 회차 = STAGE 결과 검증·문서화·보고 (파이프라인 재실행 없음).

## 디스크 재검증 (read-only)
- **마커 정합** — 재학습/재측정 없이 유지 (설계대로):
  - `logs/cop_trained_on.marker` mtime **6/24 17:12**
  - `logs/cop_measured.marker` mtime **6/25 23:00**
  - → 현 체크포인트(epoch_0099, mtime 6/25 02:17)와 정합 → STAGE=완료/유지 정당.
- **산출물**:
  - `data/episodes_cl`: total_episodes=**50**, total_frames=**3350**, robot_type=**so101** ✓
  - `checkpoints/act/epoch_0099/model.safetensors`: **335.9MB**, mtime 6/25 02:17 (closed-loop 신선) ✓
  - `research/simulation/inference_progress/rollout_summary.json` (mtime 6/25 23:00):
    10 rollout 중 **7 성공 = 0.70**, median lift **43.7mm**, threshold 40mm, device=cpu ✓
    - 성공 7건: max_lift 43.7~45.6mm / 실패 3건(rollout 2/5/8): 3.7~6.9mm → **이분(bimodal) 분포** 유지.
- **환경 무결성**: `git status` clean, 서브모듈 없음 → main repo 직접 커밋 안전.

## 검증
- 드라이버 STAGE 정상 종료, 마커·산출물·체크포인트 3자 정합. 6/27·6/28·6/29 기록과 동일 패턴 → **회귀 없음**.
- [자가치유] 해당 없음 — 에러·불일치·데이터 손상 없음.

## 다음 단계 연결
- W4 dated 항목(6/22~6/30) **사실상 종료**. closed-loop 1사이클은 L162~167 이미 `[v]`.
- 남은 W4 `[ ]` = L168 "학습 모델 Orin Nano 배포" → 외부 의존(장기헌 SSH 정보, external-dependencies 우선순위2) 미수신으로 **이연, `[ ]` 유지**.
- **7월 Phase 2(Sim2Real)** 진입. 진입 전 sim 성공률 70%→90%+ 향상은 드라이버가 마커 리셋 / `COP_TARGET_EP` 상향 시 자동 전진(데이터 50→200ep 증대·씬 다양화 여지).
</content>
</invoke>
