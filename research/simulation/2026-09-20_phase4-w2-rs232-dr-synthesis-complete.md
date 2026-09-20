# Phase 4 W2 — RS232 DR 데이터셋 합성 완주 + 재학습 트리거 준비 (2026-09-20)

## 오늘 진행 단계
로드맵 866행 `[ ] RS232 DR 합성 + 재학습` 의 **합성 절반 완주 확인**.
(867 실기 검증 = 외부 의존 보류로 skip.)

드라이버 STAGE=완료/유지: `episodes_rs232` 100ep · nominal 성공률 0.600(목표 0.50 충족) — 재실행 없음.

## 무엇을 했나

### 1. 어제(9/19) detached 재기동한 DR 합성이 완주했는지 검증
9/19 야간 잡이 `data/episodes_rs232_dr` 100ep 합성을 `os.fork()`+`os.setsid()` 로
detached 재기동(PID 29014)한 상태였다. 오늘 검증 결과:

- **완주 확인**: `data/episodes_rs232_dr/meta/info.json` → `total_episodes=100`,
  `total_frames=15337`, `fps=30`, top/closeup 듀얼 카메라, LeRobot v3.0 포맷.
  meta 파일(info/stats/pcb_traj) mtime 23:56 = 재기동 프로세스가 정상 종료하며 메타 마감.
- **프로세스 정리 확인**: PID 29014 gone, `pgrep -fl episodes_rs232_dr` = no collector running
  → 좀비/중복 수집 프로세스 없음.
- nominal `episodes_rs232`(100ep/16,093f) 대비 DR 은 15,337f — 프레임 수 comparable
  (DR reset 훅 무작위화로 에피소드 길이 변동, 정상 범위).

### 2. 무결성 격리 전수 확인 (별도 데이터셋 루트 → nominal 불변)
DR 합성은 별도 루트라 nominal 파이프라인 산출물이 전부 불변이어야 한다. 확인:

| 대상 | 값 | 상태 |
|---|---|---|
| `logs/cop_dataset_target` | `data/episodes_rs232` | 불변 (DR 로 미전환) |
| `logs/cop_trained_on.marker` | `episodes_rs232:1789546321` | 불변 (9/16) |
| `logs/cop_measured.marker` | `episodes_rs232:1789666953` | 불변 (9/18) |
| pending marker | 없음 | 측정 클로즈 상태 유지 |
| `rollout_summary_rs232.json` | seed42 0.6/0.5, mtime Sep 18 23:02 | 불변 |
| `data/episodes_rs232` | 100ep/16,093f | 불변 |

→ **회귀/오염 0.** DR 합성은 nominal baseline(부분성공 0.600/완전분리 0.600)을 건드리지 않았다.

### 3. `.gitignore` 정합
`data/episodes_rs232_dr/` 가 미ignore 상태(untracked 노출)였다. 형제 DR 데이터셋
(`episodes_cl_dr`, `episodes_s1_dr`)은 전부 ignore — 대용량 로컬 보존 원칙. 동일 패턴으로
`data/episodes_rs232_dr/` 한 줄 추가(surgical).

## 어떻게 검증했나
- `info.json` 직접 읽기: `total_episodes=100` (metric).
- `ps`/`pgrep` 로 수집 프로세스 종료 확인.
- 마커·타겟·rollout_summary mtime/내용 대조로 nominal 불변 확증.

## 다음 단계로의 연결 (재학습 절반 = 드라이버 담당)
866행의 남은 절반 = **DR 재학습 → DR-trained 4-seed 측정 → nominal 0.600 과 공정 비교**.
이건 드라이버(`cop_pipeline_advance.sh`)의 새 사이클이다. 트리거 조건(에이전트는 하드룰상
직접 실행 안 함, **준비 완료만 표면화**):

- `logs/cop_dataset_target` → `data/episodes_rs232_dr` 전환, **또는** 마커 삭제로 새 사이클 유도.
- 전환 시 드라이버가 `episodes_rs232_dr` → `checkpoints/act_rs232_dr`(격리) 42epoch 재학습
  → epoch_0041 4-seed(42/7/123/2026) 측정 → nominal 0.600 과 비교.

**예상 결론(사전)**: Phase 2 W1 실증상 DR 축은 sim 성공 천장을 못 올림
(baseline 0.825 ↔ DR-trained 0.800). RS232 정합 환경에서 이 실측 확증이 본 항목의 목적 —
즉 "DR 이 도움 안 됨"을 RS232 에서도 재현하는 게 성공 기준. 합성 데이터는 이제 준비 완료.
