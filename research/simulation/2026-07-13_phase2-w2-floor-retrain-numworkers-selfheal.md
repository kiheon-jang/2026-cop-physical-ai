# Phase 2 W2 — floor 재학습 6차: FD 누수 근본치유 (num_workers=0) — 2026-07-13

## 배경
W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가. 대기 중
sim track 은 7/7 W1 결론이 지목한 **배치 다양성(floor)** 레버로 전진 중. floor ACT 재학습이
FD 누수로 **6 run 연속 미완주**.

## 오늘의 핵심: 어제 "RLIMIT-fix 발효 run" 이 또 실패 → 근본원인 재규명

### 결정론적 드라이버 결과 (재실행 없음)
- 어제 run(pid 85398, RLIMIT-fix 발효 예상)이 **epoch 58 에서 또 이상종료** — 지난 run 들과
  동일한 ~58~59 천장. `21 leaked semaphore` + `OSError [Errno 24] Too many open files` 재현.
- 드라이버가 이상종료 감지 → STAGE=학습시작 → **새 run pid 8470** (`--epochs 100 --no-resume`,
  →`checkpoints/act_floor`, train_start 23:00:49). 현재 epoch 0 정상 수렴(loss 41.2→4.5).

### 크래시 트레이스백이 진짜 원인을 지목
```
File ".../train_act.py", line 341, in train
    for step, batch in enumerate(dataloader):
File ".../torch/utils/data/dataloader.py", line 433, in _get_iterator
    return _MultiProcessingDataLoaderIter(self)
File ".../multiprocessing/util.py", line 517, in spawnv_passfds
    errpipe_read, errpipe_write = os.pipe()
OSError: [Errno 24] Too many open files
```
→ **epoch 루프 내부에서 DataLoader 가 매 epoch 새 워커를 spawn** (`w.start()` / `os.pipe()`).
매 spawn 이 파이프 FD 를 누적 → 크론 셸의 낮은 소프트 한도(macOS 기본 256, `256/4워커≈58ep`
정합)에 도달 → 이상종료.

### 왜 지난 2개 fix 가 실패했나
- **persistent_workers (7/9)**: 이론상 워커 1회 spawn 후 재사용해야 하나, macOS `spawn`
  컨텍스트에서 매 epoch `__iter__`→`_get_iterator()` 가 여전히 새 워커를 띄움(트레이스백이
  `_MultiProcessingDataLoaderIter(self)` 재생성 증명). 재spawn 자체를 못 막음.
- **RLIMIT_NOFILE 셀프상승 (7/11)**: `setrlimit((hard, hard))` 로 소프트를 하드까지 올리려
  했으나, 크론 프로세스에서 실효 없음(크래시 지점이 여전히 ~58 = 256 소프트 한도 그대로).
  두 fix 모두 **재spawn 이라는 누수 원천을 남겨둔 채 증상만 늦추려** 함.

## 자가치유 — 멀티프로세싱 제거로 누수 원천 차단
[자가치유] `train_act.py` 실운영(비smoke) 학습 경로의 `effective_workers` 를 `None`(→config
기본 4) 에서 **`0` 으로 강제**. 근거:
- `num_workers=0` → `_SingleProcessDataLoaderIter` → **워커 subprocess 없음 → os.pipe/세마포어
  생성 없음 → FD 누수 물리적으로 불가능**. 6-run 실패의 유일 원인(멀티프로세싱 워커 churn)을
  근본 제거.
- 데이터셋 3350 frame 소형 → DataLoader 멀티프로세싱 이득 미미(GPU/MPS 컴퓨트가 병목,
  로딩 아님) → 워커 제거 비용 사실상 없음.
- surgical: 분기 1곳(else 브랜치) 상수 변경 + 주석, 학습 로직·smoke 경로 무변경.

**검증**: `ast.parse` OK. `num_workers=0` → `load_dataset` 의 `persistent_workers=workers>0`
자동 False → SingleProcess 경로 확정(smoke 경로가 이미 동일 0-워커 구성으로 통과 중).

**발효 시점**: pid 8470 은 이미 **수정 이전 코드**를 로드해 실행 중(하드룰상 kill/재시작 안 함)
→ 오늘 밤 ~58 에서 재크래시 예상 → 내일(7/14) 드라이버 재시작이 **수정 코드 로드 → 100epoch
완주 기대**. (7/9→7/10, 7/11→7/12 와 동일한 "fix 지금 커밋, 다음 run 발효" 패턴. 단 이번 fix 는
증상 지연이 아닌 **누수 원천 제거**라 완주 확실성이 높음.)

## 무결성 격리 (전부 불변)
- target=`episodes_floor` · trained_on/marker=`episodes_cl_dr:1783181837`(직전 승격값 유지) ·
  pending=`episodes_floor:1783324998`(대기·미승격) · measured=`episodes_cl_dr:1783346557`.
- 학습 미완 → 승격/측정 보류(6/22 SILENT 반대·설계대로) → 운영 `rollout_summary.json`
  (act_cl_dr, seed42, **0.70**/median lift 50.2mm, measured 2026-07-07) **불변** → baseline 무손상.
- datasets `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 50ep 불변. ckpt act·act_cl_dr·
  act_floor 3자 분리. `checkpoints/act_floor` 최신 저장 = `epoch_0059`(7/11, 과거 run).

## 다음 단계 (드라이버 담당 — 재실행 금지)
- **완주 시**(num_workers=0 → FD 천장 무관 → 100epoch 도달 기대): pending 승격 →
  `act_floor/epoch_0099` 측정 → floor-trained rollout.
- **비교 검증**: floor-trained 를 4 seed(42/7/123/2026) 공정추정으로 baseline(0.825)·
  DR-trained(0.800) 와 비교 — **배치 다양성이 성공률 천장을 올리는가**(7/7 W1 처방 실증).
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — external-dependencies.md 감시.
