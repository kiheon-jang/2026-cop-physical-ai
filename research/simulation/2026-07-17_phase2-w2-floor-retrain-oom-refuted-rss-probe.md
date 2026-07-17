# Phase 2 W2 — floor 재학습 10차: mps_mem 계측 판독 = GPU OOM 반증 + RSS 프로브 (2026-07-17)

## 오늘 진행 단계
Phase 2 - W2 - floor 배치다양성 재학습 **10차**.
W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가 → floor sim 사이클 전진.

## 결정론적 드라이버 결과 (재실행 없음)
`cop_pipeline_advance.sh`(23:00):
- **9차 run(pid 7243, mps-fix 발효 코드) epoch 58 이상종료 감지** — driver `⚠ 학습 이상종료 감지
  (episodes_floor — metrics 마지막 epoch 미달)`. log tail: `{"epoch": 58, "step": 10, "loss": 0.0156}`
  직후 `resource_tracker: 1 leaked semaphore` (SIGKILL, **OSError traceback 부재**).
- **새 run pid 26783** 시작(`--epochs 100 --no-resume`, →`checkpoints/act_floor`, train_start 23:00:34).
  현 epoch 0 step 350 loss 3.79 정상 수렴, alive.

## 오늘의 판정 = GPU OOM 가설 반증 (9-run 만에 결착)

9차 run(pid 7243)은 mps-fix(`torch.mps.empty_cache()` 완화 + `mps_mem` 계측)가 **실제 적용된** 첫 run.
그럼에도 **또 epoch 58 crash** → 완화 무효. 하지만 계측이 붙어 crash 원인을 직접 판독했다.

**epoch별 `mps_mem`(GPU 드라이버 할당, bytes) 곡선:**

| epoch | mps_mem (GB) |
|---|---|
| 0 | 5.72 |
| 3~6 | 5.57~5.61 |
| **7** | **6.65** (1회 계단 상승) |
| 8 ~ 57 | **6.65 ~ 6.67 평탄** (누수 없음) |
| 58 (crash step10) | — |

→ **epoch 7 에서 6.65GB 로 한 번 오른 뒤 crash 직전(57)까지 완전 평탄.** 단조 증가 전무.
6.65GB 는 16GB 통합메모리의 42% — **GPU OOM 물리적으로 불가**. 7/15 세운 "MPS 캐시 미반환 OOM"
가설 **반증**. (7/15 FD 누수 가설도 프로브로 이미 반증됨 → FD·GPU OOM 둘 다 아님.)

**crash 신호 종합 (9-run 일관):**
- crash epoch 클러스터 **~49·56·57·58·59** — 9 run 모두 ~57 천장.
- `mps_mem` 평탄(6.65GB) · `elapsed_sec` 평탄(~311s, epoch별 slowdown 없음) → **점진 자원 고갈 아님**.
- SIGKILL 시그니처: Python traceback 없음 + shutdown `1 leaked semaphore` = **외부에서 프로세스 급사**.
- 시각: epoch 57 done = **2026-07-17 04:03:54**, crash 04:04. 23:00 시작 + 평탄 311s/epoch →
  57 epoch 은 항상 ~04:00 착지. **crash 의 epoch~57 vs 벽시계~04:00 은 (고정 23:00 시작 탓) 교락**.

**남은 유일 미측정 변수 = 프로세스 전체 RSS(통합메모리).** `mps_mem` 은 GPU 할당자만 계측한다.
Apple Silicon 통합메모리에선 CPU측 + wired + 파일캐시가 함께 압박 → jetsam 이 최대 프로세스를 SIGKILL
(traceback 없음) 하면 정확히 이 시그니처. GPU 할당자가 평탄해도 프로세스 RSS 는 오를 수 있다.

## [자가치유] RSS 프로브 추가 (surgical, 다음 run 발효)

`scripts/train_act.py`:
- 모듈 top `import resource` (기존엔 `_raise_fd_limit` 안에 지역 import 뿐 → epoch 루프에서 NameError 방지).
- `epoch_metric` 에 `"rss_bytes": resource.getrusage(RUSAGE_SELF).ru_maxrss` 1필드 추가(macOS=bytes).
- 반증된 OOM 주석 2곳 정정(L394 계측 목적 · L410 완화책 근거).

**판독 설계 (다음 crash 시):**
- RSS 도 평탄 → **프로세스 메모리 문제 아님** → 외부 SIGKILL / 시각연동(~04:00 macOS periodic·백업 등)
  → 처방 = 교락 해제(다른 시각 시작) 또는 crash 생존(체크포인트 resume) / epoch 목표 하향.
- RSS 상승(mps_mem 평탄인데) → CPU측 통합메모리 누적 압박(jetsam) → batch/워커/캐시 측 root fix.

검증: `ast OK` · `resource.getrusage` 샘플 17MB(macOS bytes 확인). 학습 로직 무변경, 정확도 무영향.
발효는 **다음 run**(pid 26783 은 23:00:34 로드 = 편집 이전 → 오늘밤 ~57 재crash 예상 → 내일 드라이버
재시작이 RSS-계측 코드 로드 → RSS 곡선 확보). 하드룰상 학습 kill/재실행 안 함.

## 무결성 격리 (불변 재확인)
- target=`episodes_floor` · trained_on=`episodes_cl_dr:1783181837`(직전 승격값 유지) ·
  pending=`episodes_floor`(대기·미승격) · measured=`episodes_cl_dr:1783346557`.
- 학습 미완 → 승격/측정 보류(6/22 SILENT 반대·설계대로) → 운영 `rollout_summary.json`
  (act_cl_dr, seed42, **0.70** / median lift 50.2mm, 2026-07-07) **불변** → baseline 무손상.
- datasets `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 50ep/3350frame 불변.
- `act_floor` 최신 ckpt = `epoch_0059`(과거 crash run, 이번 crash56<59 → 신규 상위 ckpt 없음).

## 다음 단계로의 연결 (드라이버 담당 — 재실행 금지)
- **완주 시**: pending 승격 → `act_floor/epoch_0099` 측정 → floor-trained rollout →
  4-seed(42/7/123/2026) 공정추정 vs baseline 0.825 / DR-trained 0.800 (배치 다양성이 천장 올리는가).
- **재crash 시**: RSS-계측 곡선으로 jetsam vs 외부 시각연동 판정 → 그에 맞는 root fix(교락 해제 /
  resume / epoch 하향 / batch 축소). **9-run 증상추적 루프 탈출 = 오늘 OOM 반증이 첫 결착.**
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — external-dependencies.md 미수신 지속 감시.
