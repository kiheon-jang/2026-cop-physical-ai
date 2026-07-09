# Phase 2 W2 — floor 배치다양성 재학습 재시도 + FD 누수 자가치유

- **날짜**: 2026-07-09 (목요일)
- **단계**: Phase 2 - W2 - 배치 다양성(floor) 사이클 ACT 재학습 (재시도)
- **드라이버**: `scripts/cop_pipeline_advance.sh` (23:00, 재실행 금지 — 본 문서는 문서화/자가치유)

## 1. 무슨 일이 있었나 (드라이버 결과)

어제(7/8) 착수한 floor 사이클 학습(pid 94316)이 **이상종료**했다. 드라이버가 이를 감지:

```
⚠ 학습 이상종료 감지 (episodes_floor — metrics 마지막 epoch 미달) → 재학습 재시도 예약
OSError: [Errno 24] Too many open files
STAGE=학습시작  (episodes_floor 50ep 로 ACT 재학습, 100epoch → checkpoints/act_floor)
[start_act_train] 시작 pid=21661 args=--epochs 100 --no-resume
```

- **어제 run(pid 94316)**: `checkpoints/act_floor/` 는 `epoch_0009`(7/8 23:56) … `epoch_0049`(7/9 03:45)
  까지만 저장됨. epoch 50~59 사이에서 크래시 → metrics 가 마지막 epoch(99) 미달 → 드라이버가
  "이상종료" 판정.
- **크래시 원인**: `OSError: [Errno 24] Too many open files` — `_MultiProcessingDataLoaderIter`
  의 `os.pipe()` 에서 파일 디스크립터 고갈.
- **드라이버 대응(설계대로)**: 재학습 재시도 예약 → **새 run pid 21661** 을 23:00:28 에 시작
  (`--no-resume`, fresh FD 테이블). 현재 정상 진행 중(아래 관찰).

## 2. 근본 원인 규명 — DataLoader 워커 매 epoch 재spawn

`scripts/train_act.py`:
- DataLoader 는 학습 시작 시 **1회 생성**(line 497).
- epoch 루프(line 328)가 매 epoch `for step, batch in enumerate(dataloader)`(line 336)로 **재순회**.
- `num_workers=4` + `persistent_workers` 미설정(기본 False) → **매 epoch 마다 워커 4개를 새로 spawn**
  (`_MultiProcessingDataLoaderIter.__init__`).

macOS 는 spawn 시작방식 + 낮은 기본 `ulimit -n` 이라, epoch 마다 워커 파이프 FD 가 누적되어
**~50 epoch 후 FD 고갈** → `Too many open files`. 어제 run 이 정확히 epoch_0049 직후(50~55) 크래시한
지점과 일치. (직전 사이클 34291s≈9.5h/100ep 대비 03:45=epoch49 는 정상 속도였음 → 성능 아닌 FD 누수.)

## 3. 자가치유 — persistent_workers=True

`scripts/load_dataset()` 의 DataLoader 생성부에 `persistent_workers=workers > 0` 추가:

```python
return torch.utils.data.DataLoader(
    dataset, batch_size=config.batch_size, shuffle=True,
    num_workers=workers, pin_memory=use_pin, drop_last=True,
    persistent_workers=workers > 0,   # ← 추가
)
```

- 워커를 **1회 spawn 후 전 epoch 재사용** → epoch 마다 재spawn 하던 FD 누수 원천 제거.
- `num_workers=0`(smoke) 에서는 `persistent_workers` 가 반드시 False 여야 하므로 `workers > 0` 로 게이트.
- surgical 변경(해당 return 문 1줄 + 주석). 학습 로직/하이퍼파라미터/데이터 무변경.

## 4. 검증

- **구문**: `ast.parse` PARSE_OK.
- **DataLoader 스모크**(`scripts/_dl_smoke_tmp.py`, 실행 후 삭제):
  ```
  workers=0 persistent=False batches/epoch=4 OK
  workers=2 persistent=True  batches/epoch=4 OK   ← 3 epoch 재순회, 워커 재사용 정상
  DATALOADER_SMOKE_OK
  ```
  게이트 로직(0→False, >0→True) 및 persistent 워커 다-epoch 재사용 확인.
- **적용 시점 주의**: 현재 돌고 있는 pid 21661 은 코드 수정 **이전에** 모듈을 로드했으므로 이 fix 의
  혜택을 받지 못함 → **다시 ~epoch 50 부근에서 같은 크래시 가능**. 그 경우 내일 드라이버가 이상종료
  재감지 → **수정된 코드로 재시작 → 완주**. 하드룰상 야간 에이전트는 학습을 직접 kill/재실행하지
  않음(드라이버 담당) → pid 21661 은 그대로 두고, 코드 fix 는 다음 사이클에 발효.

## 5. 무결성 / 관찰 (비파괴)

- **현 학습 alive**: pid 21661 = `train_act.py --epochs 100`. train_start dataset_root=`episodes_floor`,
  ckpt=`checkpoints/act_floor`, resume_from=null, ts `2026-07-09T23:00:28`. epoch 0 step 200
  **loss 38.8→5.67**(정상 초기 수렴), CPU ~12%, RSS ~226MB.
- **마커 2단계 격리 정상**:
  - target = `episodes_floor`
  - `cop_trained_on.marker` = `episodes_cl_dr:1783346557` (직전 승격값 유지 → 운영 rollout_summary 불변)
  - `.pending` = `episodes_floor:1783324998` (대기, 미승격)
  - 6/22 SILENT 반대·설계대로 학습 미완 → 승격/측정 보류 → **baseline 무손상**.
- **체크포인트 격리**: `act`·`act_cl_dr`·`act_floor` 3자 분리 유지.
- **[자가치유]**: DataLoader `persistent_workers=True` 추가로 FD 누수(Too many open files) 재발 방지.

## 6. 다음 단계 연결

- **드라이버 담당(재실행 금지)**: pid 21661 학습 완료 시 → `.pending` 승격 → `act_floor/epoch_0099` 측정
  → floor-trained rollout. (또는 21661 이 FD 누수로 재크래시 시 → 내일 드라이버가 **수정 코드**로 재시작
  → 완주 후 측정.)
- **비교 검증**: floor-trained 를 동일 4 seed(42/7/123/2026) 공정추정으로 baseline(0.825)·DR-trained
  (0.800)와 비교. **핵심 질문**: 배치 다양성이 성공률 천장을 올리는가 / 실패 배치가 이동·축소되는가
  (7/7 W1 결론 = 병목은 섭동강건성 아닌 **배치 커버리지**의 실증).
- 실기 track: Orin/실기 SSH 미수신 지속 → W2 zero-shot 진입 불가, 수신 시 재개.
