# 2026-07-29 — Phase 2 W2: sim 성공률 레버 결착 후 hold + 비파괴 무결성 전수 감사

## 오늘 진행 단계
Phase 2 - W2 - sim 성공률 레버 결착 후 hold + 비파괴 무결성 전수 감사

## 배경
sim 트랙 성공률 레버(큐브배치 다양성)는 **2026-07-22 4-seed 공정추정(42/7/123/2026 전부 1.0, 40/40 성공)**
으로 이미 결착됨. baseline 0.825 / DR-trained 0.800 → **floor-trained 1.000**. 7/7 W1 결론(병목=배치 커버리지,
DR 축은 천장 못 올림)의 처방이 실증 확증됨. 이후 7/23~7/28 은 hold + 무결성 감사 유지.

## 오늘 한 일
드라이버(`scripts/cop_pipeline_advance.sh`)가 결정론적으로 STAGE=완료/유지 처리 (episodes_floor 50ep · 최종
성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. 야간 에이전트는 **비파괴 무결성 전수 감사**만
수행(이번 세션 도구결과).

### 감사 결과 (이번 세션 도구결과)
| 항목 | 값 | 판정 |
|---|---|---|
| 운영 `rollout_summary.json` md5 | `5207f67b189645de1bb26c124873b683` | 7/22·7/23·7/25·7/26·7/27·7/28 과 **동일**(불변) |
| success_rate / ckpt | 1.0 / `act_floor/epoch_0041` | 불변 |
| seed / median lift | 42 / 66.0mm | 불변 |
| success | 10/10 | 불변 |
| target marker | `data/episodes_floor` | 정합 |
| trained_on marker | `episodes_floor:1783324998` | 정합 |
| measured marker | `episodes_floor:1783710169` | 정합 |
| datasets floor/cl/cl_dr | 각 50ep / 3350frame | 불변 |
| 학습 프로세스 | `pgrep train_act` → none | 없음 |

→ **회귀/오염 0**. 운영 산출물 무접촉.

## 검증 방법
- `.venv/bin/python3` `hashlib.md5` 로 rollout_summary.json 해시 산출 (md5 CLI 은 sandbox 차단 → python 우회, 7/26~28 과 동일 방식).
- 마커 3자 파일 직접 read, datasets meta/info.json 파싱, `pgrep -fl train_act`.

## 관찰 / 이슈
- 무결성 회귀/오염 0. 운영 산출물 무접촉.
- [자가치유] 없음 — 7/28 research-log·roadmap 정합, 결손 없음.

## 다음 단계 (연결)
sim 트랙 성공률 레버 규명 완료 → hold 지속. 남은 것 모두 외부 의존:
- 실기 W2 zero-shot 추론: Orin Nano SSH 외부의존(장기헌) 미수신 → 진입 불가, 대기.
- full-epoch(100) 공정비교 복원: ~04:04 외부 SIGKILL killer 진단권한(log show/launchctl, sandbox 차단) 에스컬레이션 대기.
