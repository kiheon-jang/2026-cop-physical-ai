# floor 재학습 12차 — 시각연동 외부 SIGKILL **확정** + deadlock 규명 자가치유 (2026-07-19)

## 오늘 진행 단계
Phase 2 - W2 - floor 배치다양성 재학습 **12차** (RSS 프로브 첫 crash 판독 + 근본 deadlock 규명)

> W2 dated 실기 스텝(zero-shot)은 Orin/실기 SSH 외부의존 미수신 → 진입 불가 → floor sim 사이클 전진.

## 결정론적 드라이버 결과 (재실행 없음)
`cop_pipeline_advance.sh`(23:00): **11차 run(pid 5069, RSS-probe 발효 코드) 이상종료 감지**
(`metrics 마지막 epoch 미달`, tail `{"epoch": 49, "step": 10}`, `1 leaked semaphore`, traceback 없음)
→ 새 run **pid 91975**(`--epochs 100 --no-resume`, →`checkpoints/act_floor`) 재시작.

## 오늘의 결착 — 9-run 미스터리 종결: 고정 벽시계 외부 SIGKILL

어제(7/18) 발효한 RSS 프로브(`rss_bytes`, getrusage RUSAGE_SELF)가 **9-run 만에 처음 crash 까지의
RSS 곡선**을 남겼다. pid 5069 실측(`logs/act_train_metrics.jsonl`, 49 epoch):

| 지표 | 값 | 판정 |
|---|---|---|
| **rss_bytes** | 827MB(초반 10ep) → 811MB… 아니 **789MB→811MB 초반 1회 +22MB 후 39ep 완전 평탄** | 단조증가 전무 → **jetsam 반증** |
| **mps_mem** | epoch 0 6.59GB → ~6.64GB 평탄 (=16GB의 42%) | **GPU OOM 반증**(재확인) |
| **elapsed_sec** | 313~417s, 평균 **368.8s** (점진 slowdown 없음) | 자원누적 반증 |
| **crash epoch** | **49** (이전 9-run 은 56~59) | ↓ 아래 핵심 |

정확값: rss_bytes 는 딱 두 값만 존재 — `827,211,776`(10 epoch) · `850,837,504`(39 epoch).
(789→811MB 표기는 반올림; 초반 1회 +22MB 후 crash 까지 39 epoch 완전 고정.)

### epoch↔벽시계 교락이 풀렸다 = 결정적 증거
- pid 5069: 시작 **23:00:52**, 마지막 완료 epoch **48 @ 04:02:24**, crash ~**04:04:15**.
- 이전 9-run: crash epoch **~57** 이지만 **역시 벽시계 ~04:00~04:04**.
- **차이의 원인**: pid 5069 는 epoch 가 느렸다(평균 **368.8s** vs 이전 ~313s) → **같은 ~04:04
  까지 49 epoch 만** 돌았다(이전은 57). → crash 는 **고정 epoch 이 아니라 고정 벽시계(~04:04)**.

즉 "9-run 연속 ~57 epoch 천장"은 애초에 epoch 천장이 아니라 **매일 ~04:04 에 발생하는 벽시계
이벤트**였다. 느린 epoch 가 이 교락을 풀어 **epoch 49 에서(=이전보다 8 epoch 일찍) 같은 04:04 에
죽음**으로써 이를 실증. **자원(FD·GPU·RSS)은 전부 평탄** + traceback 없음 + leaked semaphore =
**외부에서 프로세스를 시각에 맞춰 급사(SIGKILL)**.

**FD 누수(7/15 프로브 반증) · GPU OOM(7/17 mps_mem 반증) · jetsam(오늘 RSS 반증) — 세 메모리
가설 전부 기각.** 남은 결론은 하나: **~04:04 에 도는 외부 프로세스가 학습을 죽인다.**

## 진짜 deadlock (오늘 규명)
- 100 epoch × ~368s = **~10.2h**. 23:00 시작 → 완주 예상 **~09:00**.
- 그러나 kill 은 **~04:04** = 창(window) **5h ≈ 최대 ~48~49 epoch**.
- → **100 epoch 는 23:00→04:04 창에 물리적으로 못 들어감.** 드라이버가 매일 `--no-resume`
  으로 재시작(진행분 폐기)하므로 **영원히 완주 불가 = 실질 deadlock**. 12-run 무측정의 근본.
- **resume 은 해법 아님**: `train_act.py` L546 경고 — resume 는 **가중치만 복원, 옵티마이저/
  epoch 카운터 리셋**. 드라이버 완료 게이트(L113 `epoch==EPOCHS-1`)를 단일 run 으로 못 채움.

## 자가치유 — 목표 epoch 하향으로 창 안 완주
`scripts/cop_pipeline_advance.sh` L36 기본값 **`COP_EPOCHS:-100` → `:-42`** (surgical 1줄 + 근거 주석).
- 42 × ~400s(최악) = ~4.67h → **~03:41 완주 < 04:04** (평균 368s 면 03:18). 안전 마진 ~20분+.
- 완주 → 드라이버 stage 2.5 pending 승격 → stage 5 `act_floor/epoch_0041` **측정** → **12-run 만에
  첫 floor rollout** → 4-seed 공정추정 vs baseline 0.825 / DR-trained 0.800.
- **override knob 유지**: `COP_EPOCHS=100` 로 언제든 복원(ponytail: 창 크기 = 튜닝 노브).
- **발효 시점**: 오늘 드라이버는 이미 pid 91975 를 `--epochs 100`(편집前 값)으로 띄움 → **오늘밤도
  ~04:04 재crash**. 편집은 **내일 드라이버 재시작이 로드**(7/9→7/10 패턴).

### 한계 / 후속 (정직)
- 42-epoch floor 모델은 baseline(100ep, loss ~0.0045) 대비 **저학습**(ep41 loss ~0.019) →
  성공률 비교가 **epoch 교락**. 첫 신호 확보 목적엔 유효하나, **공정 비교엔 full-epoch 필요**.
- **full-epoch 복원 조건 = ~04:04 killer 규명 후 제거/리스케줄.** 이는 `log show`/`launchctl`/`ps`
  필요 → **sandbox allowlist 차단(external-dependencies.md 블로커)**. → 에스컬레이션.

## 무결성 격리 (전수 확인, 비파괴)
- 운영 `rollout_summary.json`: **success_rate 0.70 · median_lift 50.2mm · act_cl_dr/epoch_0099** 불변(7/7).
- 마커: target=`episodes_floor` · trained_on=`episodes_cl_dr:1783181837`(불변) ·
  pending=`episodes_floor:1783324998`(대기·미승격) · measured=`episodes_cl_dr:1783346557`.
- datasets `episodes_floor`·`episodes_cl`·`episodes_cl_dr` 각 존재·불변. `act_floor` 최신 ckpt=`epoch_0059`(과거 run).
- 회귀 spot-check: `joint_angle_comparison_sim.py` PASS, 최대오차 **0.0244°**(elbow) < 1°.

## 다음 단계 (드라이버 담당 — 재실행 금지)
1. **오늘밤**: pid 91975(`--epochs 100`) ~04:04 재crash 예상(편집 미적용).
2. **내일(7/20)**: 드라이버 재시작이 `COP_EPOCHS=42` 로드 → **~03:41 완주 → pending 승격 →
   floor rollout 측정 → 4-seed 비교**. 배치 다양성이 성공률 천장을 올리는가 첫 실측.
3. **root fix(full-epoch 복원)**: sandbox 언블록 후 ~04:04 killer(macOS 주기 유지보수/백업/스케줄
   프로세스 후보) 규명·제거 → `COP_EPOCHS=100` 복원.

## 다음 단계와의 연결
7/7 W1 결론(병목=배치 커버리지, DR 축은 sim 천장 못 올림)의 처방 = floor 배치 다양성 재학습.
그 재학습이 12-run 무측정으로 막혀 있었고 **오늘 근본원인(시각연동 SIGKILL)과 deadlock 을
확정 규명**, 창 안 완주 자가치유로 **내일 첫 floor 측정 경로를 열었다**.
