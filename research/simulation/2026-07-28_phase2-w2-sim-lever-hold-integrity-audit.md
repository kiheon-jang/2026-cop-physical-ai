# 2026-07-28 — Phase 2 W2: sim 레버 결착 후 hold + 무결성 전수 감사

## 오늘 진행 단계
Phase 2 - W2 - sim 성공률 레버 결착 후 hold + 비파괴 무결성 전수 감사

## 배경
- sim 트랙 성공률 레버(배치 다양성)는 **2026-07-22 4-seed 공정추정(4/4 = 1.0)** 으로 이미 결착.
  - baseline 0.825 / DR-trained 0.800 → floor-trained **1.000** (40/40 rollout 성공, 실패 배치 0).
- 이후 남은 두 항목은 모두 외부 의존 대기(아래 "다음 단계") → 야간 sim 트랙은 hold.
- 오늘 드라이버 STAGE = **완료/유지** (`episodes_floor` 50ep · 성공률 1.0, 새 사이클 미트리거).
  수집/학습/측정 재실행 없음.

## 실행 — 비파괴 무결성 전수 감사 (이번 세션 도구결과)

| 항목 | 값 | 판정 |
|---|---|---|
| 운영 `rollout_summary.json` md5 | `5207f67b189645de1bb26c124873b683` | 7/22·7/23·7/25·7/26·7/27 과 **동일**(불변) |
| success_rate | 1.0 | 불변 |
| checkpoint | `checkpoints/act_floor/epoch_0041` | 불변 |
| seed / median lift | 42 / 66.0mm | 불변 |
| target 마커 | `data/episodes_floor` | 정합 |
| trained_on 마커 | `episodes_floor:1783324998` | 정합 |
| measured 마커 | `episodes_floor:1783710169` | 정합 |
| datasets floor/cl/cl_dr | 각 50ep / 3350frame (info.json) | 불변 |
| 학습 프로세스 | `pgrep train_act` → none | 없음 |

→ **회귀/오염 0.** 운영 산출물 무접촉.

## 관찰 / 이슈
- 무결성 회귀/오염 0. 마커 3자 정합.
- md5 CLI 는 sandbox 차단 → `.venv` python `hashlib` 로 동일 값 우회 산출.
- [자가치유] 없음 — 7/27 research-log · roadmap 정합, 결손 없음.

## 다음 단계 (둘 다 외부 의존 대기)
- 실기 W2 zero-shot 추론: Orin Nano SSH 외부의존(장기헌) 미수신 → 진입 불가, 대기.
- full-epoch(100) 공정비교 복원: 04:04 killer 진단권한(log show/launchctl, sandbox 차단) 에스컬레이션 대기.

## 다음 단계와의 연결
- sim 성공률 레버 규명이 완료된 상태에서, 매일 감사는 운영 산출물(`rollout_summary.json` 1.0 / md5 불변)이
  외부 의존 해소 시점까지 무손상으로 보존됨을 보증한다. Orin SSH 수신 즉시 이 floor-trained 모델
  (`act_floor/epoch_0041`, sim 1.0)이 zero-shot 실기 격차 측정의 기준선으로 바로 투입된다.
