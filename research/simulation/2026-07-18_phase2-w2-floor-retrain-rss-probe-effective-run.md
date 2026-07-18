# Phase 2 W2 — floor 재학습 11차: RSS 프로브 발효 run (in-flight)

- **날짜**: 2026-07-18 (토요일)
- **단계**: Phase 2 - W2 - floor 배치다양성 재학습 11차
- **성격**: 결정론적 드라이버 전진 + 야간 에이전트 비파괴 진단/문서화 (파이프라인 재실행 없음)

> W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가 → floor sim 사이클 전진.

## 결정론적 드라이버 결과 (재실행 없음)

`cop_pipeline_advance.sh`(23:00):

- **10차 run(pid 26783, RSS-probe 미적용 코드) epoch 57 이상종료 감지**
  (`metrics 마지막 epoch 미달`, 드라이버 tail `{"epoch": 57, "step": 310, "loss": 0.0141}` 후
  `1 leaked semaphore`, traceback 없음) → 재학습 재시도 예약.
- **새 run pid 5069** 시작 (`--epochs 100 --no-resume`, →`checkpoints/act_floor`, 23:00:52).
  현 epoch 0 step 40 loss 29.2→12.3 정상 수렴, log 활성(alive).

## 오늘의 진척 = RSS 프로브 발효 시점 전환

pid 5069 는 RSS-probe 커밋 `884294f`(7/17) **이후** 디스크 `scripts/train_act.py` 를 로드
→ 계측 실제 적용. 확인:

- `train_act.py:22` 모듈 top `import resource`
- `train_act.py:402` `epoch_metric` 에 `"rss_bytes": resource.getrusage(RUSAGE_SELF).ru_maxrss`

직전 10차 run 의 `logs/act_train_metrics.jsonl` 은 `mps_mem` 만 있고 **`rss_bytes` 부재**
= pid 26783 이 편집前 코드 로드였음을 방증. 따라서 **다음 crash(pid 5069)가 9-run 만에
처음으로 RSS 곡선을 남긴다** → jetsam vs 외부 시각연동 최종 판정.

## GPU OOM 재확인 반증 (10차 run mps_mem 판독)

`logs/act_train_metrics.jsonl` 말미 (pid 26783):

| epoch | loss | elapsed_sec | mps_mem (bytes) |
|---|---|---|---|
| 54 | 0.01547 | 313.97 | 6,640,533,504 |
| 55 | 0.01465 | 312.85 | 6,640,533,504 |
| 56 | 0.01436 | 313.42 | 6,640,533,504 |

- **mps_mem 완전 평탄 6.64GB** (= 16GB 통합메모리 42%) → GPU OOM 물리적 불가 재확인
  (7/15 OOM 가설·FD 가설 둘 다 반증 상태 유지).
- **elapsed_sec 평탄 ~313s** (점진 slowdown 없음).
- **crash epoch ~57** (9-run 천장 불변) · traceback 없음 + `1 leaked semaphore`
  = **외부 SIGKILL 급사** 시그니처 재현.
- epoch57 벽시계 ~04:04 (고정 23:00 시작 탓 epoch~57 ↔ ~04:00 교락 지속).

## 우선순위 5종 회귀 테스트 (학습과 병행, 비파괴)

| 스크립트 | 결과 |
|---|---|
| `joint_angle_comparison_sim.py` | PASS. 최대 관절각 오차 **0.0244°**(elbow 45.0244 vs 45) < 1° |
| `sim_pick_place.py` | 결정론 fail, min_approach_dist **0.3228m** (어제와 동일, open-loop fixed-pose 씬 특성) |
| `sim_camera_verification.py` | PASS. 30프레임 양 카메라 동기 캡처 |
| `sim_data_collector.py --episodes 2` | 2/2 성공, **yield 100%**, lift **43.5mm** (closed-loop, ≥40mm 필터 통과, scratch `data/episodes`) |
| `sim_headless_6dof_video.py` | PASS. 6관절 순차 애니 2501프레임 → `sim_6dof_animation.mp4` |

## 무결성 격리 유지 (전수 확인)

- **target** = `data/episodes_floor`
- **trained_on** marker = `episodes_cl_dr:1783181837` (직전 승격값 불변)
- **pending** marker = `episodes_floor:1783324998` (대기·미승격)
- **measured** marker = `episodes_cl_dr:1783346557`
- 학습 미완 → 승격/측정 보류(6/22 SILENT 멈춤 반대·설계대로) → 운영
  `research/simulation/inference_progress/rollout_summary.json`
  (act_cl_dr epoch_0099 seed42 **0.70** / median lift **50.2mm**, 측정 2026-07-07) **불변** → baseline 무손상.
- datasets `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 **50ep/3350frame** 불변.
- `act_floor` 최신 ckpt = `epoch_0059` (과거 run, crash57<59 → 신규 상위 ckpt 없음).

## 자가치유

- 없음. 오늘은 어제(7/17) RSS 프로브의 **첫 발효 run** — 계측 코드가 pid 5069 에 실제 로드됨.
- sandbox: `ps`/`log show`(jetsam 확인) 권한 차단 지속 — external-dependencies.md v3.2 allowlist 블로커.
  프로세스 alive 는 `act_train.log` epoch 진행으로 간접 확인.

## 다음 단계 (드라이버 담당 — 재실행 금지)

- **완주 시**: pending 승격 → `act_floor/epoch_0099` 측정 → floor-trained rollout →
  4-seed(42/7/123/2026) 공정추정 vs baseline 0.825 / DR-trained 0.800
  (배치 다양성이 성공률 천장을 올리는가).
- **재crash 시**: **pid 5069 이 남길 `rss_bytes` 곡선으로 판정** — RSS 평탄=외부/시각연동
  (교락 해제/resume/epoch 하향), RSS 상승=jetsam(batch/워커 축소). **9-run 증상추적 루프의
  마지막 미측정 변수가 오늘 처음 계측된다.**
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — external-dependencies.md 미수신 지속 감시.
