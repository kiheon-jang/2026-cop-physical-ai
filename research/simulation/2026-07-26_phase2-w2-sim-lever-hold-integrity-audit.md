# 2026-07-26 — Phase 2 W2 · sim 레버 결착 후 hold + 무결성 전수 감사

## 오늘 진행 단계
Phase 2 - W2 - sim 성공률 레버 결착 후 hold + 비파괴 무결성 감사

## 배경
- sim 트랙 성공률 레버(배치 다양성)는 **7/22 4-seed 공정추정(4/4 = 1.0)** 으로 이미 결착.
  baseline 0.825 / DR-trained 0.800 → floor-trained **1.000**. 병목 = 큐브배치 커버리지(모방격차),
  DR 축은 천장 못 올림 — 7/7 W1 결론의 처방이 실증됨.
- 남은 두 항목은 **모두 외부 의존 대기**:
  - 실기 W2 zero-shot 추론: Orin Nano SSH(장기헌) 미수신 → 진입 불가.
  - full-epoch(100) 공정비교 복원: 04:04 killer 진단권한(log show/launchctl, sandbox 차단) 에스컬레이션 대기.
- 드라이버 STAGE=완료/유지(`episodes_floor` 50ep · 성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음.
  → 오늘은 hold 일. 야간 에이전트 작업 = 비파괴 무결성 감사 + 문서화.

## 실행 / 검증 (이번 세션 도구결과)
비파괴 감사만 수행. 운영 산출물 무접촉.

| 항목 | 값 | 판정 |
|---|---|---|
| 운영 `rollout_summary.json` md5 | `5207f67b189645de1bb26c124873b683` | 7/22·7/23·7/25 와 **동일**(불변) |
| success_rate / ckpt | 1.0 (10/10) · `act_floor/epoch_0041` · seed42 · median lift 66.0mm | 불변 |
| 마커 target | `data/episodes_floor` | 정합 |
| 마커 trained_on | `episodes_floor:1783324998` | 정합 |
| 마커 measured | `episodes_floor:1783710169` | 정합 |
| datasets floor/cl/cl_dr | 각 50ep / 3350frame (info.json) | 불변 |
| 학습 프로세스 | `pgrep train_act.py` → 없음 | hold 확인 |

- 3자 마커 정합 유지, md5 4일 연속 불변 → **회귀/오염 0**.
- md5 검증은 `.venv` python `hashlib` 로 산출(md5 CLI sandbox 차단 우회, 값 동일).

## 관찰 / 이슈
- 회귀/오염 0. 운영 산출물 무접촉.
- [자가치유] 없음 — 어제(7/25) research-log·roadmap 정합, 결손 없음.

## 다음 단계
- sim 트랙 성공률 레버 규명 완료 → hold 유지.
- 실기 W2 zero-shot: Orin Nano SSH 외부의존 미수신 → 진입 불가, 대기.
- full-epoch(100) 공정비교 복원: 04:04 killer 진단권한 에스컬레이션 대기.
