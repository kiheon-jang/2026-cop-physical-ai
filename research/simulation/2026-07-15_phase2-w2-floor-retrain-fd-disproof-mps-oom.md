# Phase 2 · W2 — floor 재학습 8차: FD 누수 가설 **경험적 반증** + MPS OOM 재규명

- 날짜: 2026-07-15 (수)
- 단계: Phase 2 W2 배치다양성(floor) 사이클 — ACT floor 재학습 8차 (in-flight)
- 스크립트: `scripts/train_act.py`, 진단 `scripts/_fd_leak_probe.py`

## 요약 (오늘의 반전)

지난 3일(7/9 persistent_workers · 7/11 RLIMIT_NOFILE · 7/13 num_workers=0)의 자가치유는
전부 **"DataLoader 워커 FD 누수"** 가설 위에 세워졌다. 오늘 **그 가설을 직접 프로브로
반증**했다. 8-run 연속 ~57~59 epoch 이상종료의 진짜 원인은 FD 가 아니라 **MPS 메모리 누적
OOM(SIGKILL)** 이 유력.

## 드라이버 결과 (재실행 없음)

`cop_pipeline_advance.sh`(23:00): 어제 run(pid 48167, **num_workers=0 fix 적용 코드**) 이
**또 epoch 57 에서 이상종료**(`metrics 마지막 epoch 미달`) → 새 run **pid 73001**
(`--epochs 100 --no-resume`, →`checkpoints/act_floor`, train_start 23:00:14) 재시작.

## 결정적 증거

1. **num_workers=0 는 실제 적용됐다** — shutdown 세마포어 누수 `21 → 1` 로 급감(워커 소멸 방증).
   그럼에도 crash epoch = **57**, 지난 7 run(~49~59) 과 동일 천장. → 워커 제거가 천장을 못 옮김.
2. **이번 run 은 OSError traceback 없음** — 로그 tail = `{"epoch": 57, "step": 370}` 직후
   `resource_tracker ... 1 leaked semaphore` 만 있고 `OSError [Errno 24]` 부재. epoch 57 **도중**
   (step 370/418) 사망 = Python 예외 아닌 **SIGKILL 시그니처**(OOM 커널 킬).
3. **epoch 시간 완전 평탄** — metrics 상 epoch 0~56 모두 **~313~314s** (증가 없음). 점진적
   slowdown 아님 → "고정량 자원이 매 epoch 누적돼 하드 천장에서 급사".
4. **FD 프로브 = 누수 없음(직접 반증)** — `_fd_leak_probe.py`: `episodes_floor` 데이터셋 +
   `num_workers=0` DataLoader 를 **4 full-epoch(각 418 step 완전 순회)** 재순회하며 `/dev/fd`
   측정:
   ```
   baseline fds after load: 6
   full-epoch 0: steps=418 open_fds=6
   full-epoch 1: steps=418 open_fds=6
   full-epoch 2: steps=418 open_fds=6
   full-epoch 3: steps=418 open_fds=6
   ```
   → **데이터 경로 FD 완전 고정**. 3일간 쫓던 FD 누수는 num_workers=0 에서 재현 불가 = red herring.

## 재규명: MPS 메모리 누적 OOM

평탄한 epoch 시간 + 고정 epoch(~57) 무-traceback SIGKILL + FD 불변 → 남는 유력 가설 =
**PyTorch MPS 할당자 캐시가 epoch 마다 증가해 물리 메모리 천장(16GB M5)에서 OOM** (torch MPS
의 알려진 특성). 워커 FD 는 num_workers=4 run 들의 **2차 증상**이었을 뿐, 사망 epoch 을 정한
1차 요인은 처음부터 메모리였을 가능성이 높다(그래서 워커 설정 무관하게 ~57 고정).

## [자가치유] — 가설기반 완화 + 다음 run 직접 검증 계측

`train_act.py` epoch 루프에 surgical 2건:
- **완화**: 매 epoch 종료 시 `torch.mps.empty_cache()` + `gc.collect()` (device.type=="mps" 게이트).
  표준 MPS 누적 완화책, loss/정확도 무영향.
- **계측**: `epoch_metric["mps_mem"] = torch.mps.driver_allocated_memory()` — 다음 run 이
  epoch 별 메모리 곡선을 남겨 OOM 가설을 **직접 확증/반증**.

검증: `ast` OK · `torch.mps.{driver_allocated_memory,empty_cache}` 존재 확인 · `--smoke`
완주(cpu 경로, `mps_mem: null`, gc.collect 무해). **발효는 다음 run**: pid 73001 은 수정 이전
코드 로드(오늘밤 ~57 재crash 예상) → 내일 드라이버 재시작이 수정+계측 코드 로드 →
완주 또는 메모리 곡선 확보(7/9→7/10 패턴, 단 이번은 가설을 계측으로 검증하는 점이 다름).

## 무결성 격리 (불변)

학습 미완 → 마커 승격/측정 보류(6/22 SILENT 반대·설계대로) → baseline 무손상.
- target=`episodes_floor` · trained_on=`episodes_cl_dr:1783181837`(직전 승격값 유지)
- pending=`episodes_floor:1783324998`(대기·미승격) · measured=`episodes_cl_dr:1783346557`
- 운영 `rollout_summary.json`(act_cl_dr, seed42, **0.70** / median lift 50.2mm, 2026-07-07) 불변
- datasets `episodes_floor`/`episodes_cl`/`episodes_cl_dr` 각 50ep/3350frame 불변

## 다음 단계 (드라이버 담당 — 재실행 금지)

- **완주 시**: pending(`episodes_floor:1783324998`) 승격 → `act_floor/epoch_0099` 측정 →
  floor-trained rollout → 4-seed(42/7/123/2026) 공정추정 vs baseline 0.825 / DR-trained 0.800
  (배치 다양성이 성공률 천장을 올리는가 — 7/7 W1 처방 실증).
- **재crash 시**: 다음 run 의 `mps_mem` 곡선으로 OOM 가설 확정 → 필요 시 batch_size 축소 등
  진짜 root fix.
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개(external-dependencies.md 감시).
