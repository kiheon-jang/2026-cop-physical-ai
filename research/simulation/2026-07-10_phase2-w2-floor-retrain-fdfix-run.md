# Phase 2 · W2 — floor 배치다양성 재학습 3차(FD-fix 발효 run) · 2026-07-10 (금)

> 어제(7/9) 자가치유한 DataLoader FD 누수 수정(`persistent_workers`)이 **처음으로 발효되는 run**.
> W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가.
> 대기 중 sim track 은 7/7 W1 결론(병목=배치 커버리지)이 지목한 floor 배치 다양성 레버로 전진.

## 결정론적 드라이버 결과 (재실행 금지 — 드라이버 담당)
`scripts/cop_pipeline_advance.sh`(23:00):
- 타겟 = `data/episodes_floor` → `checkpoints/act_floor`.
- 어제 run(pid 21661)의 산출물을 검사 → **학습 이상종료 감지**(`metrics 마지막 epoch 미달`),
  로그에 원인 `OSError: [Errno 24] Too many open files` 잔존 → **재학습 재시도 예약**.
- STAGE=학습시작 → **새 run pid 39732** 시작(`--epochs 100 --no-resume`, log=`logs/act_train.log`,
  train_start 타임스탬프 `2026-07-10T23:00:26`).

## 오늘의 핵심 = fix 발효 시점 전환
- 어제 기록대로 pid 21661 은 **수정 이전** 모듈을 로드한 run 이라 fix 미적용 → 예측대로 ~epoch 50
  부근에서 FD 고갈 재크래시. 마지막 체크포인트 `checkpoints/act_floor/epoch_0049`(7/9 03:45).
- **오늘의 pid 39732 는 23:00:26 시작** = FD-fix 커밋 `c827ffe`(7/9) **이후**에 디스크의
  `scripts/train_act.py` 를 로드 → **persistent_workers 수정이 이 run 에 실제 적용됨**.
  - 검증: `grep persistent_workers scripts/train_act.py` → L185~196 존재
    (`persistent_workers=workers > 0`, 워커 1회 spawn 후 재사용, smoke `num_workers=0` 은 False 게이트).
  - 검증: `git log -- scripts/train_act.py` 최신 = `c827ffe`(7/9) → 이후 변경 없음 = pid 39732 가 로드한 코드 = fixed.
- ⇒ 이 run 은 매 epoch 워커 4개 재spawn 을 하지 않으므로 ~epoch 50 FD 고갈 없이 **100 epoch 완주 기대**.
  (어제 예고 "재크래시 시 내일 드라이버가 수정 코드로 재시작→완주" 가 정확히 실현된 상태.)

## 실행 테스트 결과 (야간 에이전트, 비파괴 관찰만 — 수집/학습/측정 재실행 없음)
- **run alive & 정상 수렴**: `logs/act_train.log` mtime 23:01:56(신선), 마지막 metric
  `epoch 0 step 120 loss 6.42`(l1 0.087, kl 0.63) — 시작 27.1 → 120step 6.4 정상 하강.
- **어제 크래시 run 잔재 확인**: `checkpoints/act_floor/` = epoch_0009…epoch_0049(전부 7/8~7/9,
  마지막 03:45) 5개만. 새 run 은 epoch 0 진행중이라 아직 신규 체크포인트 없음(첫 저장은 epoch_0009 예정).

## 무결성 격리 (전수 확인, 회귀 0)
| 항목 | 값 | 판정 |
|---|---|---|
| `logs/cop_dataset_target` | `data/episodes_floor` | 타겟 정상 |
| `cop_trained_on.marker` | `episodes_cl_dr:1783181837` | **직전 승격값 유지**(운영 rollout_summary=DR-trained) |
| `cop_trained_on.marker.pending` | `episodes_floor:1783324998` | 대기(**미승격** — 학습 미완) |
| `cop_measured.marker` | `episodes_cl_dr:1783346557` | 7/7 DR 측정값 |
| 운영 `rollout_summary.json` | act_cl_dr/epoch_0099, seed42, **7/10=0.70**, median lift **50.2mm**, measured 2026-07-07 | **불변**(baseline 보존) |
| datasets | `episodes_floor` 50/3350 · `episodes_cl` 50/3350 · `episodes_cl_dr` 50/3350 | 전부 불변 |
| ckpt 분리 | `act` · `act_cl_dr` · `act_floor` 3자 격리 | 정상 |

→ 학습 미완이므로 pending **미승격** → `act_floor` 미측정 → 운영 summary·baseline 무손상.
2단계 마커 + ckpt 3자 격리(주간 6 critical 수정)로 학습중에도 baseline 안전.

## 자가치유
- **없음(신규)**. 어제 발효한 `persistent_workers` fix 가 이 run 에 처음 적용된 것이 오늘의 진척.
  하드룰상 야간 에이전트는 학습 kill/재실행하지 않음 → pid 39732 유지, 드라이버가 완주 관리.

## 다음 단계로의 연결 (드라이버 담당 — 재실행 금지)
- **완주 시**(fix 덕에 이번엔 ~epoch 50 크래시 없이 100epoch 도달 기대): pending 승격
  → `act_floor/epoch_0099` 측정 → floor-trained rollout.
- **비교 검증**: floor-trained 를 4 seed(42/7/123/2026) 공정추정으로 baseline(0.825)·DR-trained(0.800)
  과 비교. 핵심질문 = **배치 다양성이 성공률 천장을 올리는가 / 실패 배치가 이동·축소되는가**
  (7/7 W1 결론 = 병목=배치 커버리지 실증의 처방 검증).
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — `agent/external-dependencies.md` 미수신 지속 감시.
