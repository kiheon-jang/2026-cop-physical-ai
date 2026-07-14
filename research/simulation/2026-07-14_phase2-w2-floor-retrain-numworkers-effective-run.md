# Phase 2 W2 — floor 배치다양성 재학습 7차 = num_workers=0 fix 발효 run (in-flight)

- **날짜**: 2026-07-14 (화요일)
- **단계**: Phase 2 - W2 - floor 배치다양성 재학습 (7차, **num_workers=0 자가치유 발효 run**)
- **상태**: in-flight (학습중) — 야간 에이전트는 비파괴 관찰만, 승격/측정은 드라이버 담당

> W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가 → floor sim 사이클 전진.

## 배경 — 6-run FD 천장의 진짜 원인과 근본치유

pid 94316(7/8)·21661(7/9)·39732(7/10)·56445(7/11)·85398(7/12)·8470(7/13) 6개 run 이
모두 ~epoch 49~59 에서 `OSError [Errno 24] Too many open files` + `21 leaked semaphore` 로
이상종료. 선행 두 fix — persistent_workers(7/9)·RLIMIT_NOFILE 셀프상승(7/11) — 는 **재spawn
이라는 누수 원천을 못 막고 증상만 늦춤**. 어제(7/13) 크래시 트레이스백이 진짜 원인 지목:
epoch 루프 안에서 DataLoader 가 **매 epoch 새 워커 spawn**(`_MultiProcessingDataLoaderIter`
재생성 → `os.pipe()` → FD 누적, `256/4워커≈58ep` 정합).

**7/13 자가치유**: `train_act.py` 비smoke 학습 경로 `effective_workers` 를 `0` 강제
(`num_workers=0` → SingleProcess DataLoader → 워커 subprocess/os.pipe/세마포어 **생성 자체 없음
→ FD 누수 물리적 불가**). 데이터 3350frame 소형이라 멀티프로세싱 이득 미미.

## 오늘의 진척 — fix 발효 시점 전환

어제 run(pid 8470, num_workers=0 fix **미적용** 코드 로드)이 예측대로 **epoch 58 이상종료**
(로그 tail: `{"epoch": 58, ...}` 직후 `21 leaked semaphore` + shutdown) → 드라이버가 이상종료
감지 후 **새 run pid 48167** 시작.

- STAGE=학습시작 (episodes_floor 50ep, ACT 100epoch → `checkpoints/act_floor`)
- `train_start` 마커: `dataset_root=data/episodes_floor`, `checkpoint_dir=checkpoints/act_floor`,
  `epochs=100`, `resume_from=null`, `timestamp=2026-07-14T23:00:41`
- args: `--epochs 100 --no-resume`, pid=48167

**핵심**: pid 48167 은 num_workers=0 커밋(7/13) **이후** 디스크 `train_act.py` 를 로드 →
수정이 이 run 에 **실제 적용**. 검증(아래) 확인:
- `scripts/train_act.py` L498 (smoke) 및 **L501~506 (비smoke else 분기)** 둘 다
  `effective_workers = 0` — 이 run 은 `--smoke` 없음(비smoke) → else 분기 진입 → workers=0.
- L196 `persistent_workers=workers > 0` → workers=0 이므로 자동 False.
→ 워커 재spawn 없음 → **100epoch 완주 기대** (7/9→7/10 패턴 재현, 이번은 증상지연 아닌 원천제거라 확실성↑).

현 상태: pid 48167 alive, epoch 0 step 20 loss 35.99→22.58 정상 수렴 (log mtime 23:00대).

## 검증 (비파괴 관찰)

| 항목 | 값 |
|---|---|
| train pid | 48167 alive (`pgrep -lf train_act` 확인) |
| 어제 run | pid 8470 epoch 58 크래시 (로그 tail 확인) |
| disk fix | `effective_workers=0` 비smoke else 분기 (L501~506), persistent_workers→False (L196) |
| target 마커 | `episodes_floor` |
| trained_on 마커 | `episodes_cl_dr:1783181837` (직전 승격값·불변) |
| pending 마커 | `episodes_floor:1783324998` (대기·미승격) |
| measured 마커 | `episodes_cl_dr:1783346557` |
| 운영 rollout_summary | act_cl_dr epoch_0099, seed42, **0.70** / median lift **50.2mm**, measured 2026-07-07 — **불변** |
| datasets | floor / cl / cl_dr 각 **50ep / 3350frame** — 불변 (info.json 확인) |
| floor ckpt 최신 | `epoch_0059` (7/11 과거 run) |

**무결성 격리**: 학습 미완 → 승격/측정 보류(6/22 SILENT 반대·설계대로) → baseline 무손상.
ckpt act·act_cl_dr·act_floor 3자 분리.

## 다음 단계 연결 (드라이버 담당 — 재실행 금지)

- **완주 시**(num_workers=0 → FD 천장 무관): pending(`episodes_floor:1783324998`) 승격 →
  `act_floor/epoch_0099` 측정 → floor-trained rollout.
- **비교 검증**: floor-trained 4 seed(42/7/123/2026) 공정추정 vs baseline(0.825)·DR-trained(0.800)
  — 배치 다양성이 성공률 천장을 올리는가(7/7 W1 처방 실증).
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — external-dependencies.md 미수신 지속 감시.
