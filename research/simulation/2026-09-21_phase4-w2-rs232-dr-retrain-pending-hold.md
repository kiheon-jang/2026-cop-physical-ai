# RS232 DR 재학습 트리거 대기 — 무결성 hold (2026-09-21)

## 오늘 단계
Phase 4 - W2 - **RS232 DR 합성 + 재학습** (로드맵 866행)의 **재학습 절반 트리거 대기 hold**.
드라이버 STAGE=완료/유지 (`episodes_rs232` 100ep · 성공률 0.600, 목표 0.50 충족) — 재실행 없음.

## 상황
- DR 합성 절반은 9/20 완주 확인됨(`data/episodes_rs232_dr` 100ep/15,337f).
- 재학습 절반은 **드라이버 담당**. 새 사이클 조건(`cop_dataset_target`→`episodes_rs232_dr` 전환 / 마커 삭제)이
  미세팅 → 드라이버는 nominal 타겟 유지(STAGE=완료/유지). 야간 에이전트는 하드룰상 학습/측정을 직접 실행하지 않으므로
  준비 완료만 표면화하고 대기. **블로커 아님** — 트리거 결손일 뿐.
- 오늘 로드맵 항목의 실행 가능한 시뮬 구현 작업 없음(재학습=드라이버). 대신 무결성 전수 감사 + RS232 트윈 렌더 헬스로
  비회귀 확인.

## 무결성 전수 감사 (nominal baseline 불변)
| 항목 | 값 | 상태 |
|---|---|---|
| target 마커 | `data/episodes_rs232` (`.next`/`.pending` 없음) | 불변 |
| trained_on | `episodes_rs232:1789546321` (9/18) | 불변 |
| measured | `episodes_rs232:1789666953` (9/18) | 불변 |
| `rollout_summary_rs232.json` | seed42 0.600, mtime Sep 18 23:02 | 불변 |
| `episodes_rs232` | 100ep / 16,093f | 불변 |
| `episodes_rs232_dr` | 100ep / 15,337f / fps30 | 불변 |
| 학습 프로세스 | 없음 | — |
| `.gitignore` | `data/episodes_rs232_dr/` 포함(9/20) | 유지 |

→ 회귀/오염 0. nominal baseline(부분성공/완전분리 0.600) 무손상.

## RS232 트윈 렌더 헬스 (비회귀)
`sim_rs232_unplug.py` self-check:
- **기본 7/7 PASS** — 로드 OK, 보유력 7.2N(이탈 시작 7.31N, 규격 대역 1.76~30.1N), 물리 파지-당김 핀치 FULL 21/21 ·
  jaw 열림 대조군 0/21, 렌더 top/closeup 640×480 OK. (PARTIAL 2.95mm, FULL 5.9mm)
- **실기 정합 [8][9][11] PASS** — 관절 한계 = 스펙 6축, base 충돌 활성, HOME 중력 3초 안정(|qvel| max 5.1e-14 rad/s).

## 검증 방법
- 마커/데이터셋 info.json 직접 파싱, `rollout_summary_rs232.json` mtime 확인(Sep 18 불변 = 재측정 없음).
- `.venv/bin/python3 samples/training/sim_rs232_unplug.py` (mujoco 3.8.0).

## 다음 단계
- 로드맵 866 재학습 절반: 드라이버 새 사이클 조건(`cop_dataset_target`→`episodes_rs232_dr` 전환 / 마커 삭제) 세팅 시
  드라이버가 DR 42epoch 재학습 → DR-trained 4-seed 측정 → nominal 0.600 공정 비교.
- DP 비교(878)·실기 검증(876)은 후속 phase/외부 의존 보류.
