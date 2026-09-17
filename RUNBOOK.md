# RUNBOOK — 이 파이프라인을 처음 받는 사람을 위해

> 목적: 이 저장소를 인수한 사람이 **명령 4개로** 수집→학습→측정→확인을 재현할 수 있게 한다.
> 시간·수치는 2026-09-17 기준 실측값이다(Mac mini M5 16GB, 학습 동시 실행 중 측정 포함).

---

## 0. 절대 규칙

**모든 파이썬은 `.venv` 로 실행한다.** 시스템 파이썬에는 mujoco·lerobot 이 없다.

```bash
cd /Volumes/MARK_DATA/dev/2026-cop-physical-ai
.venv/bin/python3 <스크립트>
```

**측정 산출물은 기본으로 운영 디렉터리에 떨어진다.** 실험·스모크는 반드시 `--out-dir` 로
`research/simulation/inference_progress/` **밖**을 지정한다. 그 안에 쓰면 대시보드가 읽는
공표 수치를 덮어쓴다.

**중첩 저장소 `SO-ARM100/` 은 절대 `git add` 하지 않는다.**

---

## 1. 네 개의 명령

### (1) 데이터 수집 — RS232 3단계

```bash
.venv/bin/python3 samples/training/sim_rs232_unplug_collector.py
```
산출: `data/episodes_rs232/` (LeRobot v3, parquet + mp4). 현재 100 에피소드 / 16,093 프레임.
2카메라 계약(top, closeup) 고정. 수집 시드는 스크립트 상수.

### (2) 학습 — ACT

```bash
COP_DATASET_ROOT=$PWD/data/episodes_rs232 \
COP_CKPT_DIR=$PWD/checkpoints/act_rs232_sim \
COP_DATASET_REPO_ID=local/rs232_unplug_sim \
COP_CAMERA_KEYS=top,closeup \
bash scripts/start_act_train.sh --epochs 42 --no-resume
```
**실측 46.6분/epoch**, 42 epoch = 약 33시간. 10 epoch 마다 + 마지막에 저장하며
**같은 디렉터리를 제자리 덮어쓴다**(`epoch_0009/0019/0029/0039/0041`).
진행 확인: `tail -1 logs/act_train_metrics.jsonl`, pid 는 `logs/act_train.pid`.

> ⚠ 이전 사이클 가중치를 보존하려면 학습 시작 **전에** 복사해 둘 것.
> 예: `checkpoints/_published_baseline_20260913/` (2026-09-17 대피분)

### (3) 측정 — 4시드 공정추정

```bash
.venv/bin/python3 scripts/render_act_rollout_rs232.py
```
**실측 79.5~80초/시드**(단독), 학습 동시 실행 시 **약 134초/시드**. 4시드 총 5~9분.
산출: `research/simulation/inference_progress/rollout_summary_rs232{,_seed7,_seed123,_seed2026}.json`
\+ 이력 사본 `history/` + 영상.

판정: 완전 분리 = 플러그 변위 ≥ 5.90mm, 부분 = ≥ 2.95mm. **임계는 바꾸지 않는다.**

### (4) 대시보드 갱신

```bash
.venv/bin/python3 dashboard/build.py --json
```
산출: `dashboard/data.json` (gitignore 대상). 서버는 `dashboard/template.html` 을 직접 서빙하므로
템플릿을 고치면 즉시 반영된다. `_sian_previews/` 의 임베드를 고쳤다면
`.venv/bin/python3 dashboard/bake_embeds.py` 도 실행한다.

---

## 2. 실험용 도구 (운영 수치 불변)

```bash
# 보유력 민감도 — 모델 로드 후 마찰만 덮어씀, 씬 XML 불변
.venv/bin/python3 scripts/sweep_rs232_sensitivity.py --friction 12.0 \
  --checkpoint checkpoints/_published_baseline_20260913/epoch_0041 \
  --out-dir /tmp/sweep_f12 --seeds 42 --rollouts 10 --video-rollouts 0

# 옛 씬 대조 — git 에서 복원한 씬으로 측정
git show 8fa5adb^:sim/assets/rs232_unplug_scene.xml > /tmp/old/rs232_unplug_scene.xml
cp sim/assets/so101_real.xml /tmp/old/ && ln -s "$PWD/sim/assets/assets" /tmp/old/assets
.venv/bin/python3 scripts/sweep_rs232_sensitivity.py --scene /tmp/old/rs232_unplug_scene.xml \
  --checkpoint checkpoints/_published_baseline_20260913/epoch_0041 --out-dir /tmp/dec_old

# S1 DR 게이트 — 운영 S1 수치를 보호하며 측정
.venv/bin/python3 scripts/gate_s1_dr.py --out-dir /tmp/gate_dr_on \
  --checkpoint checkpoints/act_s1_sim_dr/epoch_0029 --dr --video-rollouts 0
```

두 래퍼 모두 측정기 파일을 수정하지 않는다 — 모듈 전역만 교체한다.

---

## 3. 야간 자동화

| 시각 | 잡 | 하는 일 |
|---|---|---|
| 23:00 | `76b3cd4eb4fc` | `cop_pipeline_advance.sh` 로 단계 판정 → 문서화 → 커밋·푸시 |
| 23:30 | `f88b3198c9b6` | 렌더 스택 헬스체크 + 메트릭 수집 → 커밋·푸시 |
| 07:00 | `fb6d7cb26650` | 보고서 생성 + 대시보드 빌드 + 메일 발송 |

드라이버 단계 판정(`scripts/cop_pipeline_advance.sh`):
`수집중 → 학습중 → 학습 종료 확정 → 데이터 부족 → 학습시작 → 측정 → 완료·유지`

마커 3종 (`logs/`):
- `cop_dataset_target` — 현재 타겟 데이터셋
- `cop_trained_on.marker(.pending)` — 학습에 쓴 데이터 서명
- `cop_measured.marker` — 측정한 모델 서명 `DS:<최신 ckpt 내부 최신 mtime>`

> 서명이 **디렉터리가 아니라 내부 파일 mtime** 인 이유: 학습이 같은 디렉터리를 제자리
> 덮어쓰기 때문이다. 디렉터리 mtime 만 보면 갱신을 놓친다.

**야간 잡이 자동 `git add` 하는 경로**:
`research/simulation/ agent/research-log/ agent/report-evidence/ agent/external-dependencies.md samples/ sim/ scripts/ docs/01_overview/daily-reports/`
→ `dashboard/` 와 그 밖의 경로는 자동 커밋되지 않는다.

크론 멈추기: `hermes cron disable 76b3cd4eb4fc f88b3198c9b6`

---

## 4. 자주 겪는 함정

| 증상 | 원인 | 대처 |
|---|---|---|
| 측정이 옛 모델을 잰다 | `find_latest_checkpoint()` 가 `epoch_*` 정렬 마지막(=0041)을 고름. 학습 중엔 아직 옛 가중치 | `--checkpoint` 로 명시 |
| 실험 결과가 사이트에 올라감 | `--out-dir` 기본값이 운영 디렉터리 | 항상 `--out-dir` 지정 |
| 매일 밤 같은 측정 반복 | 드라이버 호출 timeout 초과로 마커 기록 전에 죽음 | `cop_sim_env.py` timeout ≥ 600s, hermes `script_timeout_seconds` ≥ 3600 |
| `ModuleNotFoundError: mujoco` | 시스템 파이썬 사용 | `.venv/bin/python3` |
| 3D 뷰어가 "데이터 없음" 고정 | `_sim3dInit` 빗장이 데이터 도착 전에 걸림 | 데이터 갱신 시 재렌더 (적용됨) |
| 학습이 두 번 뜸 | pid 파일 stale | `start_act_train.sh:39` 가 막지만, `logs/act_train.pid` 확인 |

---

## 5. 지금 상태에서 이어받는 사람이 먼저 읽을 것

| 문서 | 내용 |
|---|---|
| `CLAIMS.md` | 공표 수치 전부 + 분모·판정·체크포인트·신뢰구간 |
| `ASSUMPTIONS.md` | 검증되지 않은 전제 8개 + 반증 조건 + 실측 요청 목록 |
| `research/simulation/2026-09-17_rs232-retention-operating-envelope.md` | 보유력 운영 범위 곡선 |
| `agent/report-corrections/2026-09-17_monthly-report-corrections.md` | 월간 보고서 정정안 |
| `research/simulation/2026-09-16_session-handoff.md` | 직전 세션 인계 |
