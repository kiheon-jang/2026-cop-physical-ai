# Phase 2 W2 — floor 배치다양성 재학습 5차 = RLIMIT-fix 발효 run (in-flight)

> **2026-07-12 (일요일)** · 야간 sim-환경 에이전트 v3.2
> 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가. sim track =
> 7/7 W1 결론이 지목한 **배치 다양성(floor) 레버**로 전진.

## 결정론적 드라이버 결과 (재실행 없음)
- `cop_pipeline_advance.sh`(23:00): 어제 run(pid 56445) **이상종료 감지** → **재학습 재시도**.
  - STAGE=학습시작 → **새 run pid 85398**(`--epochs 100 --no-resume`, →`checkpoints/act_floor`).
  - shutdown 시 `resource_tracker: 21 leaked semaphore objects` + `OSError [Errno 24]` 경고
    (직전 pid 56445 잔재 = FD/세마포어 누수 방증, 로그 append 로 남음).

## 오늘의 진척 = FD 근본 fix 발효 시점 전환
어제(7/11) 추가한 `_raise_fd_limit()`(RLIMIT_NOFILE 셀프-상승, commit `3fa8bb6`)이 어제 run
(pid 56445)에는 **미적용**(미수정 코드 로드)이었다. 오늘 새 run **pid 85398 은 fix 커밋
이후 디스크 `train_act.py` 를 로드** → 두 FD fix 가 실제로 이 run 에 적용된다:

- `persistent_workers=workers > 0` (L196) — 워커 매 epoch 재spawn 방지 (7/9 fix, `c827ffe`)
- `_raise_fd_limit()` main 진입 즉시 호출 (L452) — 학습 프로세스가 부모 셸과 무관하게
  자기 FD 소프트 한도를 하드(무제한)까지 상승 → macOS 기본 256 천장 제거 (7/11 fix, `3fa8bb6`)

→ 어제 예고("내일 드라이버가 수정코드로 재시작 → 100epoch 완주 기대. 7/9→7/10 패턴")의
**실현**. 지난 4 run 의 crash 궤적(pid 94316 ~49 · pid 21661 ~49 · pid 39732 ~59 · pid 56445 미완)
을 만든 256 FD 천장이 이 run 에서 제거됨 → 완주 기대.

## 검증 (비파괴 관찰)
- **코드 fix 실재**: `grep` 확인 — `persistent_workers`(L196) · `_raise_fd_limit`(L427 정의/L452 호출)
  · `fd_limit_raised` 관측필드(L466) 모두 디스크 `train_act.py` 존재. pid 85398 는 이 파일 로드.
- **run 정상 수렴**: `logs/act_train.log` 말미 pid 85398 fresh 시작 — epoch 0 step 30,
  loss 36.7→17.4 정상 하강. `--no-resume` 로 baseline 오염 없음.
- **무결성 격리 유지 (마커 2단계 + ckpt 3자 분리)**:
  - target(`logs/cop_dataset_target`) = `data/episodes_floor`
  - trained_on 마커 = `episodes_cl_dr:1783181837` (직전 승격값 유지 — 운영 rollout 불변)
  - pending 마커 = `episodes_floor:1783324998` (mtime 7/12 23:00, **대기·미승격**)
  - measured 마커 = `episodes_cl_dr:1783346557`
  - 학습 미완 → 드라이버가 pending 승격·측정 **보류**(6/22 SILENT 멈춤 반대·설계대로)
- **운영 baseline 불변**: `research/simulation/inference_progress/rollout_summary.json` =
  `act_cl_dr`/epoch_0099 · seed 42 · 7/10 = **0.70** · median lift **50.2mm** · measured **2026-07-07**.
  DR 측정 미실행 → 무손상.
- **datasets 전수 불변**: `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 **50 episodes**
  (`meta/info.json total_episodes=50`). ckpt `act`·`act_cl_dr`·`act_floor` 3자 분리.

## 자가치유
- **없음.** 어제 RLIMIT fix 가 오늘 첫 발효되는 것이 진척 그 자체. 하드룰상 실행중 pid 85398 은
  kill/재시작 안 함 → 드라이버가 완주 관리.

## 다음 단계 연결 (드라이버 담당 — 재실행 금지)
- **완주 시**(256 천장 제거 → 100epoch 도달 기대): pending 승격 → `act_floor/epoch_0099` 측정
  → floor-trained rollout.
- **비교 검증**: floor-trained 를 4 seed(42/7/123/2026) 공정추정으로 baseline(0.825)·
  DR-trained(0.800) 와 비교. 핵심질문 = **배치 다양성이 성공률 천장을 올리는가 / 실패 배치가
  이동·축소되는가** (7/7 W1 처방의 실증).
- 실기 track: Orin/실기 SSH 수신 시 W2 zero-shot 재개 — `external-dependencies.md` 미수신 지속 감시.
