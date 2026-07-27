# 2026-07-27 — Phase 2 W2: sim 성공률 레버 결착 후 hold + 비파괴 무결성 전수 감사

## 오늘 진행 단계
Phase 2 - W2 - sim 성공률 레버 결착 후 hold + 비파괴 무결성 전수 감사

## 배경
sim 트랙 성공률 레버(큐브 배치 다양성)는 7/22 4-seed 공정추정(42/7/123/2026 전부 1.0, 40/40 rollout 성공)으로 이미 결착됨. baseline 0.825 / DR-trained 0.800 → floor-trained **1.000**. 7/7 W1 결론(병목=배치 커버리지, DR 축은 sim 천장 못 올림)의 처방이 실증됨. 이후 남은 두 항목은 모두 외부 의존 대기 상태 → 오늘도 hold.

## 무엇을 했나
드라이버(`cop_pipeline_advance.sh`)가 STAGE=완료/유지 보고(`episodes_floor` 50ep · 최종 성공률 1.0, 새 사이클 미트리거). 수집/학습/측정 재실행 없음. 야간 에이전트는 **비파괴 무결성 전수 감사**만 수행.

## 어떻게 검증했나 (이번 세션 도구결과)
- 운영 `research/simulation/inference_progress/rollout_summary.json`
  - md5 = `5207f67b189645de1bb26c124873b683` — 7/22·7/23·7/25·7/26 값과 **동일**(불변)
  - success_rate 1.0 · checkpoint `checkpoints/act_floor/epoch_0041` · seed 42 · median_lift 66.0mm
- 마커 3자 정합:
  - target `logs/cop_dataset_target` = `data/episodes_floor`
  - trained_on `logs/cop_trained_on.marker` = `episodes_floor:1783324998`
  - measured `logs/cop_measured.marker` = `episodes_floor:1783710169`
- datasets 불변: episodes_floor / episodes_cl / episodes_cl_dr 각 50ep · 3350frame (info.json)
- 학습 프로세스 없음 (`pgrep -fl train_act.py` → none)
- → **회귀/오염 0**

## 관찰 / 이슈
- 무결성 회귀/오염 0. 운영 산출물 무접촉.
- md5 CLI 는 sandbox 차단 → `.venv` python `hashlib` 로 동일 값 우회 산출.
- [자가치유] 없음 — 7/26 research-log·roadmap 정합, 결손 없음.

## 다음 단계 연결
sim 트랙 성공률 레버 규명 완료 → hold 지속. 남은 것 모두 외부 의존:
- 실기 W2 zero-shot 추론: Orin Nano SSH 외부의존(장기헌) 미수신 → 진입 불가, 대기.
- full-epoch(100) 공정비교 복원: 04:04 killer 진단권한(log show/launchctl, sandbox 차단) 에스컬레이션 대기.
