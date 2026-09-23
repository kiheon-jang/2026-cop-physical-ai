# Phase 4 W2 — RS232 DR 재학습 트리거 대기 hold (4일째) + 무결성 감사

**날짜**: 2026-09-23 (수)
**단계**: Phase 4 - W2 - RS232 DR 합성 + 재학습 (PHASE_ROADMAP 866행)
**상태**: DR 합성 완료(9/20), 재학습 절반은 드라이버 담당 — 트리거 조건 미세팅으로 hold 4일째(9/20~23)

## 무엇을 했나
드라이버가 이미 결정론적으로 파이프라인을 전진(STAGE=완료/유지, `episodes_rs232` 100ep · 성공률 0.600, 목표 0.50).
야간 에이전트 역할 = 문서화 + 무결성 감사 + RS232 트윈 렌더 헬스. 재학습(수집/학습/측정) 재실행 없음.

RS232 DR 재학습(로드맵 866의 남은 절반)은 드라이버 새 사이클 조건이 필요:
`cop_dataset_target`→`episodes_rs232_dr` 전환 또는 마커 삭제. 이 조건은 미세팅 상태 →
nominal 타겟(`episodes_rs232`) 유지 → 재학습 미트리거. 하드룰상 야간 에이전트는 직접
실행하지 않음 → **준비 완료 표면화만**(블로커 아님, 트리거 결손).

## 검증 (23:00 세션 실측)

### 무결성 전수 감사 — nominal 불변
- `logs/cop_dataset_target` = `data/episodes_rs232` (`.next`/`.pending` 없음)
- `logs/cop_trained_on.marker` = `episodes_rs232:1789546321` (불변)
- `logs/cop_measured.marker` = `episodes_rs232:1789666953` (불변, pending 마커 없음)
- `rollout_summary_rs232.json` mtime **Sep 18 23:02 불변**(=재측정 없음):
  seed42 부분성공 **0.600**(6/10)·완전분리 0.500 / legacy(옛 비핀치 판정) 0.900/0.800,
  median disp 9.66mm, threshold 부분 2.95/완전 5.9mm, device=cpu, wall 83.4s
- 데이터셋: `episodes_rs232` 100ep/16,093f · `episodes_rs232_dr` 100ep/15,337f, 둘 다 fps30
- 학습 프로세스 없음 (`pgrep train_act.py` → none)
- → 회귀/오염 **0**

### RS232 트윈 렌더 헬스 — PASS
`sim_rs232_unplug.py` 기본 **7/7 PASS**:
- 보유력 frictionloss 7.2N · 이탈 시작 7.31N (DE-9 규격 대역 1.76~30.1N)
- 물리 파지-당김 핀치 FULL 21/21 · jaw 열림 대조군 FULL 0/21 (변위 0.000mm)
- 무작위 리셋 200회 관통 0, 후드 top 프러스텀 200/200
- 렌더 top/closeup 640×480 OK

실기 정합 **[8][9][11] PASS**:
- 관절 한계 = 실기 스펙 6축, ctrlrange 클램프 정상
- base 충돌 활성(geom 10), HOME pan sweep 201점 base 접촉 0
- HOME 중력 3초 마지막 1초 |qvel| 최대 5.1e-14 rad/s (정적 안정)

## 다음 단계로의 연결
로드맵 866 재학습 절반은 드라이버가 새 사이클 조건 세팅 시 자동 수행:
`episodes_rs232_dr` 42epoch 재학습 → DR-trained 4-seed 측정 → nominal 0.600 공정 비교.
DR 데이터(100ep/15,337f)는 9/20 이미 준비 완료. 마커 2단계 격리로 baseline(0.600) 무손상 유지.
Phase 2 W1 실증상 DR 축은 sim 천장을 못 올렸으므로(0.825↔0.800) RS232 실측 확증이 재학습 목적.

후속(외부 의존 보류): RS232 실기 검증(894), DP vs ACT 비교(896).

## 미결(외부)
- Gmail 앱 비밀번호 재발급(07:00 SMTP 535, 9/12~ 지속) — 사용자 조치 대기.
