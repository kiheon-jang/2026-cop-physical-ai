# Phase 2 W2 — floor 재학습 9차 = MPS-fix + 계측(mps_mem) 발효 run (in-flight)

- **날짜**: 2026-07-16 (목요일)
- **단계**: Phase 2 - W2 - 배치 다양성(floor) 사이클 ACT 재학습
- **상태**: in-flight (학습중, 승격/측정 보류 — 설계대로)

## 요약 (한 줄)
어제(7/15) run(pid 73001, mps-fix **미적용** 코드)이 예측대로 **epoch 56 이상종료** → 드라이버가 감지 후
새 run **pid 7243** 시작. pid 7243 은 mps-fix 커밋 `32fcb5d`(7/15) **이후** 디스크 `train_act.py` 로드
→ **`torch.mps.empty_cache()` 완화 + `mps_mem` 계측이 이 run 에 실제 적용** → 완주 시 OOM 가설 해소 확인,
재crash 시 **`mps_mem` 곡선으로 MPS OOM 가설 직접 확증/반증**.

## 결정론적 드라이버 결과 (재실행 없음)
`cop_pipeline_advance.sh`(23:00):
- pid 73001(mps-fix 미적용) **epoch 56 이상종료 감지** (`metrics 마지막 epoch 미달`).
  - 로그 tail: `{"epoch": 56, "step": 270, "loss": 0.0139…}` 직후 shutdown `1 leaked semaphore`
    (어제 8차와 동일 시그니처 — 워커 소멸 상태에서도 crash → 워커 FD 아님 재확인).
- 새 run **pid 7243** 시작 (`--epochs 100 --no-resume`, →`checkpoints/act_floor`, train_start 23:00:22).
  - 현 epoch 0 step 30, loss 28.5→14.2 정상 수렴. log mtime 갱신중, 프로세스 alive(R state).

## 오늘의 진척 = mps-fix 발효 시점 전환
- pid 7243 는 mps-fix 커밋 `32fcb5d`(7/15) 이후 디스크 `train_act.py` 로드 → 코드 검증:
  - L395 `"mps_mem": torch.mps.driver_allocated_memory()` — epoch 종료마다 MPS 할당 메모리 계측.
  - L414 `torch.mps.empty_cache()` (+ `gc.collect()`) — epoch 종료마다 MPS 캐시 반환(완화).
  - L509/517 `effective_workers = 0`(비smoke) — num_workers=0 유지(7/13 fix).
- **의의**: 8-run(pid 94316·21661·39732·56445·85398·8470·48167·73001)을 ~56~59 epoch 에서 죽인
  천장에 대해, 이번 run 이 **처음으로 완화(empty_cache) + 계측(mps_mem) 동시 적용**.
  - 완주하면: MPS 캐시 미반환 = 진짜 원인이었음을 실증(OOM 가설 확증 + 해소).
  - ~57 재crash 하면: `mps_mem` 곡선이 epoch별 증가 추세를 남겨 **OOM 확정 → batch_size 축소 등
    진짜 root fix** 로 직행(계측이 다음 진단의 근거). 어느 쪽이든 3일 헛돌던 워커 FD 루프 탈출.
- 7/9→7/10, 7/11→7/12, 7/13→7/14, 7/15→7/16 동일 패턴(전날 fix 커밋 → 다음 run 발효). 이번은 완화+계측 조합.

## 무결성 격리 유지 (검증 결과)
| 항목 | 값 | 상태 |
|---|---|---|
| target | `episodes_floor` | 유지 |
| trained_on marker | `episodes_cl_dr:1783181837` | **불변**(직전 승격값) |
| pending marker | `episodes_floor:1783324998` (mtime 7/16 23:00) | 대기·미승격 |
| measured marker | `episodes_cl_dr:1783346557` | 불변 |
| 운영 rollout_summary.json | success **0.70** / median lift **50.2mm** / `act_cl_dr/epoch_0099` | **불변**(2026-07-07) |
| datasets floor/cl/cl_dr | 각 50ep / 3350frame | 불변 |
| act_floor 최신 ckpt | `epoch_0059` (과거 run) | crash epoch56<59 → 신규 상위 ckpt 없음 |

학습 미완 → pending 승격·측정 보류(6/22 SILENT 반대·설계대로) → baseline 무손상.

## 어떻게 검증했나
- `tail logs/act_train.log`: pid 73001 epoch56 step270 후 `1 leaked semaphore` → pid 7243 train_start 23:00:22 → epoch0 수렴.
- `ps aux | grep train_act`: pid 7243 alive.
- `grep mps_mem/empty_cache/effective_workers scripts/train_act.py`: L395·L414·L509 확인.
- `git log train_act.py`: `32fcb5d`(7/15 mps-fix) HEAD 반영 확인.
- 마커 4종 + 운영 rollout_summary(0.70/50.2mm) + datasets 3종 전수 불변 확인.

## 다음 단계 (드라이버 담당 — 재실행 금지)
- **완주 시**: pending 승격 → `act_floor/epoch_0099` 측정 → floor-trained rollout →
  4-seed(42/7/123/2026) 공정추정 vs baseline 0.825 / DR-trained 0.800 (배치 다양성이 sim 성공 천장을 올리는가).
- **재crash 시**: 이 run 의 `mps_mem` 곡선(epoch별)으로 OOM 확정/반증 → batch_size 축소 등 root fix.
- 실기 track: Orin/실기 SSH 미수신 지속 감시 (external-dependencies.md).

## [자가치유]
없음 — 어제 mps-fix(empty_cache + mps_mem 계측) 첫 발효가 오늘의 진척. 새 코드 변경 불필요.
