# 시뮬 환경 단계별 로드맵 (Phase 0 ~ 4)

> **최초 작성**: 2026-05-01
> **2026-06-11 갱신**: 작업 9월 완료 일정으로 단축. 10월 = 시연 (phase 외부). 옛 Phase 5(10월 1차완성) → Phase 4(9월) 에 통합.
> **시뮬레이터**: MuJoCo 3.x (확정 — research/decisions/2026-04-22_simulator-selection.md 참조)
> **운영**: Hermes Agent가 매일 23:00에 이 파일을 읽고 오늘 진행할 단계를 식별합니다.
> 단계 완료 시 `[v]` 체크하고 다음 단계로 진행.

## 환경 사양
- **머신**: 로컬 Mac Mini (Apple Silicon ARM64)
- **시뮬레이터**: MuJoCo 3.x (네이티브, **3.8.0** 설치됨)
- **모델**: TheRobotStudio SO-ARM100/101 MJCF
- **모델 URL**: https://github.com/TheRobotStudio/SO-ARM100
- **언어**: Python 3.14 (.venv) + uv
- **학습 프레임**: HuggingFace LeRobot (이미 설치됨)

## 🐍 Python 가상환경 (.venv) — 절대규칙

**모든 Python 작업은 `.venv` 안에서 실행되어야 한다.** 시스템 Python에는 mujoco 등의 패키지가 없다.

### .venv 위치
```
/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv
```

### 사용 패턴 (둘 중 하나, 권장: B)

```bash
# 방법 A — 활성화 후 사용 (한 셸에서 여러 명령)
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
source .venv/bin/activate
python3 -c "import mujoco; print(mujoco.__version__)"

# 방법 B — .venv python 절대경로 (단일 명령, subshell 안전)
/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3 -c "import mujoco; print(mujoco.__version__)"
```

### 패키지 설치
```bash
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
source .venv/bin/activate
uv pip install <패키지명>
```

### 크론 환경 주의사항

크론은 매번 새 셸에서 시작되어 `.venv`가 자동으로 활성화되지 않는다. 따라서 모든 크론 prompt에서 매번:
1. `.venv` 활성화 (`source .venv/bin/activate`), 또는
2. `.venv/bin/python3` 절대경로 사용

이 누락되면 `ModuleNotFoundError: No module named 'mujoco'` 에러 발생. 자세한 내용은 SOUL.md 및 jobs.json의 각 크론 prompt 참조.

---

## Phase 0 — 시뮬 환경 셋업 (2026-05, 4주)

### W1 (5/1 ~ 5/7) — MuJoCo + 모델 import
- [v] **5/1**: MuJoCo 설치 검증 (`uv pip install mujoco`) + Apple Silicon 호환성 확인
- [v] **5/2**: SO-ARM100 MJCF 모델 다운로드 (`git clone TheRobotStudio/SO-ARM100`)
- [v] **5/3**: viewer로 6-DoF 동작 확인 (`python -m mujoco.viewer --mjcf=...`)
- [v] **5/4**: Joint limits 적용 (STS3215 사양: 360° 회전, 1.5Nm 토크)
- [v] **5/5**: 그리퍼 추가 + 그리퍼 동작 확인
- [v] **5/6**: 단순 동작 시연 스크립트 (`samples/training/sim_basic_motion.py`)
- [v] **5/7**: W1 정리 + W2 카메라 셋업 준비

### W2 (5/8 ~ 5/14) — 카메라 시뮬 셋업
- [v] **5/8~9**: 오버헤드 카메라 시뮬 추가 (`<camera mode="fixed">`)
- [v] **5/10~11**: 그리퍼 카메라 시뮬 추가 (그리퍼 body 자식)
- [v] **5/12**: `mujoco.Renderer`로 RGB 이미지 추출 검증 ✅ 차단 해제 (2026-05-15)
- [v] **5/13**: 카메라 파라미터 적용 (기본값 fovy=45, 640x480 사용 — 실측값 있으면 교체)
- [v] **5/14**: 두 카메라 동시 캡처 + 동기화 검증

### W3 (5/15 ~ 5/21) — 실기 ↔ 시뮬 매핑 검증
- [v] **5/15**: 시뮬 관절 한계 vs 실기 캘리브레이션 비교
- [v] **5/16**: 시뮬 무게/관성 조정 (기본값 사용 — 실측값 있으면 교체)
- [v] **5/17~18**: 동일 명령에 대한 시뮬 vs 실기 관절각 비교 (목표 ±1°)
- [v] **5/19**: 마찰계수 튜닝
- [v] **5/20**: 매핑 정확도 리포트 작성 (W4로 이월)
- [v] **5/21**: W3 마무리 + Phase 0 W4 시작 준비

### W4 (5/22 ~ 5/31) — Pick-and-Place 시뮬 + 자동 데이터셋

> ⚠️ **코드 작성 규칙 (크론 에이전트 필독)**
> - 모든 스크립트는 **headless (`mujoco.Renderer`)** 방식으로 작성. `mujoco.viewer` 호출 금지.
> - 완료된 항목은 반드시 `[ ]` → `[v]` 체크 후 git commit.

- [v] **5/22~24**: Pick-Place 시나리오 (큐브 1개) 시뮬 동작
  - 출력 파일: `samples/training/sim_pick_place.py`
  - 큐브 스펙: 50mm 정육면체, 질량 50g, MJCF body 이름 `cube`
  - 큐브 초기 위치: `pos="0.15 0 0.025"` (작업대 위)
  - 성공 기준: 그리퍼가 큐브에 접근(±5mm) 후 들어올리기(Z+50mm) 완료
  - headless 렌더링으로 프레임 저장 (`research/simulation/video/pick_place_demo.mp4`)

- [v] **5/25~27**: 자동 데이터 수집 스크립트 (`samples/training/sim_data_collector.py`)
  - LeRobot 로컬 저장 패턴: `LeRobotDataset.create(repo_id="local/cop-pickplace", root="data/episodes")`
  - 에피소드 구조: `observations.images.top` (640×480 RGB), `observations.state` (6DoF qpos), `actions` (6DoF ctrl), `timestamps`
  - 에피소드당 큐브 초기 위치 랜덤 변동: x±20mm, y±20mm
  - 목표: 50 에피소드

- [v] **5/28~30**: LeRobot Dataset 포맷으로 50 에피소드 합성
  - `sim_data_collector.py` 실행 → `data/episodes/` 로컬 저장
  - `info.json` + `data/chunk-000/` 구조 검증
  - 50 에피소드 완료 후 `agent/research-log/YYYY-MM-DD.md` 에 성공률/소요시간 기록

- [v] **5/31**: Phase 0 완료 리포트 + 6월 Phase 1 준비
  - `research/simulation/phase0_completion_report.md` 작성
  - Phase 0 완료 기준 4개 항목 체크

**Phase 0 완료 기준**:
- ✅ MuJoCo에서 SO-ARM101이 viewer로 동작
- ✅ 카메라 2대 RGB 이미지 합성 가능
- ✅ 시뮬-실기 관절각 오차 ±1° 이내
- ✅ Pick-Place 50 시뮬 에피소드 자동 생성

---

## Phase 1 — 사전학습 (2026-06, 4주)

### W1-2 (6/1 ~ 6/14) — 데이터 합성
- [v] 시뮬에서 200 에피소드 자동 생성 (다양한 시작 위치)
- [v] LeRobot Dataset 포맷 검증

### W3 (6/15 ~ 6/21) — ACT 학습
> ⚠️ **학습 실행 전략**: ACT epoch 100은 크론 타임아웃(600초) 초과. 아래 방식으로 실행.
> ```bash
> # 크론 1이 실행 (nohup 백그라운드)
> nohup .venv/bin/python3 scripts/train_act.py --epochs 100 > logs/act_train.log 2>&1 &
> echo $! > logs/act_train.pid
> # 다음 날 크론 1이 pid 파일 확인 → 완료 여부 체크
> ```
- [v] LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`) — 2026-06-21 commit `98be446` 런타임 버그 3건 수정 완성
- [v] nohup 백그라운드로 epoch 100 학습 실행 (완료까지 수일 소요) — 2026-06-21 13:46 PID 40835 시작, 6/21 23:01 epoch 28/100 진행
- [v] 매일 크론이 `logs/act_train.log` 마지막 줄 확인 → research-log에 진행률 기록 — 6/21, 6/22 완료
- [v] 학습 완료 후 `models/act_phase1.pt` 저장 — 6/22 22:27 학습 종료 (100 epoch, 32.7h, final loss 0.0012). `checkpoints/act/epoch_0099/model.safetensors` → `models/act_phase1.pt` 복사. *git push는 .gitignore + 320MB 한도로 제외* (config.json만 커밋)

### W4 (6/22 ~ 6/30) — 파이프라인 검증 완료 + 시뮬 grasp 정상화 착수

> 📌 **2026-06-22 현황 (중요)**: sandbox 블로커 14일(6/7~21) 해소 후 전 구간 **첫 실행**.
> 데이터→학습→추론→성공률 측정 파이프라인이 모두 실제로 가동됨을 확인. 그리고 측정 결과
> **시뮬 grasp task 자체의 근본 결함을 규명**:
> - 데이터 수집 expert(고정 관절 포즈)가 큐브에 ~5cm 못 미침 → **성공 시연 0개** → 학습 모델 Pick 성공률 **0%**
> - 그리퍼 개구폭 53.7mm vs 큐브 50mm = 편당 1.85mm **초정밀 공차** (사실상 그립 거의 불가 설정)
> - IK는 큐브에 **<1mm 정밀 도달** 확인 → 해법 경로 확보 (방향제어 IK + 큐브 축소 30mm)
> - 상세: [2026-06-22_grasp-task-root-cause.md](./2026-06-22_grasp-task-root-cause.md)

> 📌 **2026-06-23 갱신 (근본원인 재규명 + 해법 확보)**: 6-22 결론(공차/토크)은 **부정확**.
> 실측·다각 검증 결과 진짜 원인 = **그리퍼 단일 회전조의 닫힘 호(arc) 스윕 + open-loop expert**:
> - 토크(±6Nm도 실패)·개구폭(손끝 ~94mm, 50mm 들어감)·접촉모델(condim 3/4/6) 전부 반증.
>   실물은 텔레오퍼레이션(사람 closed-loop)으로 3~5cm 물체를 바닥에서 잘 잡음 → open vs closed-loop 차이.
> - **closed-loop expert(매 step 큐브추종 + 점진닫힘 + 재시도) 구현 → 30mm grasp 88%(FORCE6)/75%(FORCE3=12V 팔로워 실스펙). open-loop 0% → 해결.** `scripts/_grasp_closedloop.py`.
> - pick-place는 실물 우선이 정공법(LeRobot 합의)이나 **6월 실물수집 미예정 → 6월은 sim 트랙(closed-loop 자동수집)이 메인.** sim의 결정적 가치는 Phase 3+ RS232 작업(케이블 분리).
> - 정정 상세: 위 root-cause 문서 상단 정정 + 메모리(grasp-rootcause / sim-strategy / data-paths).

- [v] ACT 학습 파이프라인 가동 검증 (smoke → 100 epoch MPS 학습, loss 곡선 정상)
- [v] rollout 추론 + Pick 성공률 측정기 구축 (`scripts/render_act_rollout.py`)
- [v] **시뮬 grasp 근본원인 재규명 + closed-loop 해법 확보** (88%/75%, `_grasp_closedloop.py`)
- [v] **closed-loop 자동수집 파이프라인 드라이버 구축** (2026-06-24):
  결정론적 상태머신 `scripts/cop_pipeline_advance.sh` (수집→학습→측정→반복) 신규. 야간 cron
  (self-heal 스킬 §0)이 매일 호출 → 한 칸씩 전진. LLM 판단 불필요(어제 SILENT 멈춤 방지).
  수집기=closed-loop(`sim_data_collector.py`, 씬 scene_grasp_pads, 큐브30mm, forcerange3.0=12V, lift≥40mm 필터, 스모크 yield 100%).
  데이터 `data/episodes_cl`, train_act 는 `COP_DATASET_ROOT` 로 읽음. 상세: `agent/cron-jobs.md`.
- [v] **closed-loop 자동수집 1사이클 완주** (드라이버가 진행): 50ep 수집 → ACT 재학습 → rollout 측정.
  **완주(2026-06-25 23:00): 수집 50/50(yield 91%) → ACT 100epoch(loss 0.004564) → rollout 10중 7성공 = 성공률 70%, median lift 43.7mm.** open-loop 0% → closed-loop **70%** 로 end-to-end 입증. 상세: `2026-06-25_closed-loop-cycle1-complete.md`.
  (50mm 큐브 미적용·30mm 진행. **측정기 정합 후속**: `render_act_rollout.py` 를 closed-loop 씬/forcerange 로 맞춰야 측정 유효 — cron-jobs.md 참조.)
  - 🔄 **2026-06-24 23:00 진척**: 수집✓(`data/episodes_cl` 50ep/3350frame) → 학습중(pid 20078, epoch 64/100, loss 0.0077, ETA~02:00) → 측정대기. 측정기 정합은 commit `16d2548` 완료(2-rollout 스모크 OK). 현 `rollout_summary.json` 0%/6.4mm 는 baseline epoch_0009(open-loop) 성적이며 closed-loop 모델 측정은 학습 완료 후 드라이버가 자동 수행. 상세: `2026-06-24_closed-loop-cycle1-progress.md`.
  - 🔄 **2026-06-25 01:00 진척**: 학습중(pid 20078 alive, epoch **85/100**, loss 0.00556, MPS) → ETA ~02:20 → 측정대기. **데이터셋 정합 확정**: run2 step≈419/epoch=`episodes_cl`(로그 내 dataset_root=`data/episodes` 1550step 항목은 run1 open-loop 종료요약). **체크포인트 저장 정상**: `epoch_0079/model.safetensors` mtime 00:26(closed-loop 신선; 디렉터리 mtime 6/21~22 은 save_pretrained 덮어쓰기 특성·결함 아님). 자가치유 없음. 학습 미완이라 본 항목 `[ ]` 유지. 상세: `2026-06-25_closed-loop-cycle1-training.md`.
  - ✅ **2026-06-25 02:17 학습완료 / 23:00 측정완료**: pid 20078 종료, epoch_0099 model.safetensors mtime 02:17(closed-loop 신선). 드라이버 측정 스테이지 `rollout_summary.json`(mtime 23:00) = 10 rollout 7성공 70%, median lift 43.7mm. 본 항목 `[v]` 클로즈.
  - ✅ **2026-06-26~30 완료/유지**: 드라이버 STAGE=완료/유지(마커·산출물·체크포인트 3자 정합, 회귀 없음). **6/30 = W4 dated 범위(6/22~6/30) 마지막 날 → Phase 1 W4 dated 작업 종료, 7월 Phase 2(Sim2Real) 진입.** 상세: `2026-06-30_closed-loop-cycle1-hold.md`.
- [ ] 학습 모델 온디바이스(Orin Nano) 배포 — **시연 단계로 보류** *(2026-08-05 전제 갱신:
  실기 트랙이 omen(RTX 2080 Ti, 실기 담당자)에서 진행되어 실기 추론 경로가 Orin SSH 에서
  omen 협업으로 바뀜. Orin 배포는 10월 시연의 온디바이스 데모 항목으로 이동)*

**Phase 1 완료 기준 (2026-06-23 갱신)**:
- ✅ 시뮬 사전학습 파이프라인 전 구간 가동 (데이터 합성 → ACT 학습 → 추론 → 성공률 측정)
- ✅ 시뮬 grasp closed-loop 해법 확보 (30mm 88%/75%)
- ✅ 시뮬 Pick 성공률: closed-loop 1사이클 측정 완료 = **70%(7/10, median lift 43.7mm)**.
  open-loop 0% → closed-loop 70% 입증. (정책 70% < expert 88% 모방격차, sim 90%+ 목표는 후속 데이터증대 여지.)
  실물수집은 6월 미예정 → Phase 2(7월) 일정으로. sim의 결정적 가치는 Phase 3+ RS232 작업.

---

## Phase 2 — Sim2Real 검증 (2026-07, 4주)

- W1 (7/1 ~ 7/7): Domain Randomization (조명, 마찰, 카메라 노이즈)
  - [v] **7/1**: DR 기반 모듈 신규 작성 (`samples/training/sim_domain_randomization.py`) — 조명/마찰/카메라노이즈 3축 무작위화, 8샘플 self-test 적용범위 전부 정상, 샘플프레임 `research/simulation/dr_samples/`. 상세: `2026-07-01_phase2-w1-domain-randomization.md`
  - [v] DR 를 `sim_data_collector.py` reset 훅 + `render_act_rollout.py` 에 연결 → DR 데이터셋 합성·측정
    - 🔄 **2026-07-01 야간**: **연결(배선) 완료 + 비파괴 스모크 통과**. opt-in `--dr` 플래그로 두 스크립트에
      DR 연결(기본 off → 드라이버 파이프라인 불변). `snapshot_baseline`/`restore_baseline` 로 friction 곱셈·
      light_pos 덧셈 누적 방지. 수집기 DR 스모크 2/2(yield 100%, friction 1.188/0.802 독립), 측정기 DR 스모크
      2/2(→ `rollout_summary_dr.json`, 운영 summary 불변). 운영 `episodes_cl` 50ep·`rollout_summary.json` 7/10 무손상.
      상세: `2026-07-01_phase2-w1-dr-wiring.md`. **잔여**: `--dr` 로 DR 50ep 합성→재학습→DR on/off 비교(드라이버 사이클).
    - 🔄 **2026-07-02**: **측정 절반 = DR on/off 프록시 비교 완료**(재학습 불필요·비파괴). 기존 epoch_0099 에
      추론-시점 DR 적용(동일 seed 42, N=10): **DR-on 8/10=0.80 vs DR-off 7/10=0.70**(median lift 44.1 vs 43.7mm).
      1 rollout 차 = 노이즈 → **성능 동등** → closed-loop 정책이 조명/마찰/카메라노이즈 섭동에 **강건**(긍정적 Sim2Real 신호).
      실패 rollout 2·8 은 seed 공통 구조적 실패(DR 무관). `rollout_summary_dr.json` 만 갱신·운영 summary 7/10 불변·`episodes_cl` 무손상.
      드라이버 STAGE=완료/유지(50ep·0.7) 재실행 없음. 상세: `2026-07-02_phase2-w1-dr-onoff-proxy.md`.
    - 🔄 **2026-07-03**: **축별(per-axis) ablation 완료**(비파괴 프록시). `randomize_scene(axes=)` 부분집합 인자 +
      `--dr-axes` 플래그 추가(surgical, 하위호환). 조명/마찰/카메라노이즈 **각각 단독** 측정(seed 42, N=10, epoch_0099):
      **light 0.70 · friction 0.70 · camera 0.70 — 셋 다 실패집합 {2,5,8} 이 운영 baseline 과 완전 동일.**
      → 어느 단일 섭동축도 grasp 를 흔들지 않음(7/2 aggregate 의 +1=rollout5 는 3축 동시에서만 나오는 임계값 노이즈).
      **지배적 Sim2Real 섭동축 없음 · 정책 축별 강건.** 남은 실패는 섭동 아닌 특정 큐브배치(모방격차). 산출물
      `rollout_summary_dr_{light,friction,camera}.json`, 운영 summary·`episodes_cl` 불변. 상세: `2026-07-03_phase2-w1-dr-axis-ablation.md`.
    - 🔄 **2026-07-04**: **실패집합 seed 강건성 검증 = 모방격차 가설 실증**(비파괴 프록시). cube-placement seed
      3종(7/123/2026) 추가 측정(동일 epoch_0099, N=10). **실패 rollout 이 seed 마다 완전 이동**: 42→{2,5,8} ·
      7→{9} · 123→{0,1} · 2026→{5} → 실패는 정책 고정약점이 아니라 **특정 큐브배치**(7/3 모방격차 가설 실증).
      성공률 0.70~0.90 분포, **운영 seed42(0.70)는 비관적 끝단** · 4-seed 평균 **0.825** → 헤드라인 70%는
      정책 실력 과소평가(공정추정 ≈0.80~0.83). 남은 gap = 섭동강건성 아닌 **큐브배치 커버리지(데이터 다양성)** 로
      좁혀짐 → DR 50ep 재학습 정공법 확증. 운영 `rollout_summary.json` md5 복원 일치·`episodes_cl` 불변,
      신규 `rollout_summary_seed{7,123,2026}.json` 3종만 추가. 상세: `2026-07-04_phase2-w1-seed-robustness.md`.
      **본격 잔여**: DR 50ep 합성→재학습(수 시간, 드라이버 사이클).
    - 🔄 **2026-07-05**: **DR 50ep 합성 완료 = 본격 잔여의 첫 절반 달성**(실제 데이터, 비프록시).
      closed-loop expert + `--dr`(조명/마찰/카메라노이즈, 매 ep reset 훅 무작위화) 로 `data/episodes_cl_dr`
      **50ep/3350frame** 신규 합성(01:02~01:17, 성공 50/50·yield 86%·lift 40.2~45.3mm). DR 실인가 확인
      (friction 0.757~0.89 등 ep별 변동). **격리 무결성**: 별도 데이터셋 루트라 운영 `episodes_cl`(50/3350)·
      `rollout_summary.json`(0.70/43.7mm)·학습마커 전부 불변, 드라이버 STAGE=완료/유지(새 사이클 미트리거).
      상세: `2026-07-05_phase2-w1-dr-dataset-synthesis.md`. **남은 절반**: `COP_DATASET_ROOT=episodes_cl_dr`
      재학습→DR-trained rollout 비교(파이프라인 학습/측정=드라이버 담당, 마커/타겟 트리거 시).
    - 🔄 **2026-07-06**: **드라이버 STAGE=완료/유지(50ep·0.7) + 무결성 전수 감사**(비파괴). 새 사이클
      미트리거 → 수집/학습/측정 재실행 없음. 데이터·측정·마커·DR 산출물 **8종 회귀/오염 0** 확인
      (운영 `episodes_cl` 50/3350·`episodes_cl_dr` 50/3350·`rollout_summary.json` 0.70/43.7mm md5
      `70484a5c…` 7/4 복원값 일치·마커 6/24·6/25 불변). **관찰**: DR 재학습(잔여 절반)이 3일째
      미트리거 — 데이터는 준비 완료됐으나 드라이버 새 사이클 조건(마커 삭제 / `COP_TARGET_EP` 상향 /
      `COP_DATASET_ROOT=episodes_cl_dr` 전환)이 미세팅. 야간 에이전트는 하드룰상 직접 실행 안 함 →
      **트리거 결손을 표면화**(블로커 아님). 상세: `2026-07-06_phase2-w1-dr-retrain-pending-hold.md`.
    - 🔄 **2026-07-06 주간**: **파이프라인 적대적 감사(32건 검증→19건 확정, critical 6건 수정) 후
      DR 재학습 실제 트리거**(13:31, pid 74621). 수정 없이는 어느 경로로든 비교 실험이 깨졌음
      (측정 스킵→옛 0.70 오보고 / 엉뚱한 데이터 재학습 / baseline 모델 파괴). 데이터셋 타겟
      `logs/cop_dataset_target` 파일 도입, 체크포인트 격리(`checkpoints/act_cl_dr`), 마커
      `ds:sig` 형식 + pending 승격, 측정 히스토리(`inference_progress/history/`) + 3D 리플레이
      궤적 덤프 신설. baseline 은 `rollout_summary_baseline_cl.json` 아카이브. ETA ~22:30 →
      23:00 크론이 완료 승격 + DR 모델 측정 예상. 이후 다중시드(7/123/2026) 공정추정 비교.
      상세: `2026-07-06_phase2-w1-pipeline-audit-dr-retrain-trigger.md`.
      **치수 검증 부속**: "기기가 작아 3~5cm 못 잡나" 의심 기각(개구 94.5/70mm, 1:1 스케일,
      영상은 탑다운 1.4mm/px 착시). 단 30mm 전용 expert 상수라 50mm 는 후속 DR 축 필요.
      상세: `2026-07-06_gripper-scale-verification.md`.
    - 🔄 **2026-07-06 야간(23:00)**: **DR 재학습 진행중(STAGE=학습중)** — 주간 트리거된 pid 74621
      alive, `episodes_cl_dr`→`checkpoints/act_cl_dr` 100epoch, **epoch 99/100 진행중**(ETA ~22:30 대비
      소폭 지연, epoch_0099 는 종료 시 저장). loss 0.00498 정상수렴. 드라이버는 학습 미완을 인식해
      **stage 2.5 승격·stage 5 측정을 보류**(6/22 SILENT 멈춤 반대·설계대로). **무결성 격리 유지**: 운영
      `rollout_summary.json` 0.70/43.7mm 불변(DR 측정 미실행)·baseline 아카이브 보존·마커 `.pending`
      =`episodes_cl_dr:1783181837` 대기(미승격)·`episodes_cl`/`episodes_cl_dr` 각 50ep 불변. ckpt 격리
      +마커 2단계+baseline 아카이브(주간 6 critical 수정)로 학습중에도 baseline 무손상. **다음 사이클**:
      학습완료→마커 승격→`act_cl_dr/epoch_0099` 측정→DR-trained rollout, 이후 다중시드 공정추정 비교.
      상세: `2026-07-06_phase2-w1-dr-retrain-inflight.md`.
    - ✅ **2026-07-07 — W1 종료**: DR-trained 모델(`act_cl_dr/epoch_0099`) **측정 + 다중시드 공정추정
      비교 완료**(비파괴). 드라이버 STAGE=측정 seed42 0.70(median lift **50.2mm**, 마커 2단계 승격 정상,
      baseline 은 `rollout_summary_baseline_cl.json` 보존). 야간 에이전트가 동일 3 seed(7/123/2026) 추가
      → **4-seed 평균 baseline 0.825 vs DR-trained 0.800**(seed7 실패 1건 추가 = 노이즈, **성공률 통계적 동등**).
      유일 개선 = **median lift ~44→~50mm 전 시드 +6mm**(임계값 위라 이진판정 무영향). **실패 큐브배치 거의
      불변**(42{2,5,8}·123{0,1}·2026{5}) → **병목 = 섭동강건성 아닌 배치 커버리지(모방격차)** 7/3~7/4 가설
      DR 실모델로 실증. **결론: DR 축 증강은 sim 성공 천장을 못 올림 → 배치 다양성이 다음 레버(`.next=episodes_floor`).**
      신규 `rollout_summary_cldr_seed{7,123,2026}.json`, baseline seed 요약·`episodes_cl(_dr)` 불변.
      상세: `2026-07-07_phase2-w1-dr-trained-rollout-compare.md`.
  - [v] **7/2**: DR on/off 프록시 비교 — 동일 seed42 N=10 에서 DR-on 8/10=0.80 vs DR-off 7/10=0.70 → 1 rollout 차 = 노이즈, 성능 동등. 정책이 조명·마찰·카메라노이즈 섭동에 강건(긍정적 Sim2Real 신호). 상세: `2026-07-02_phase2-w1-dr-onoff-proxy.md`
  - [v] **7/3**: 축별(per-axis) ablation — light/friction/camera **각각 단독 0.70**, 실패집합 {2,5,8} 이 운영 baseline 과 완전 동일 → 지배적 Sim2Real 섭동축 없음. 상세: `2026-07-03_phase2-w1-dr-axis-ablation.md`
  - [v] **7/4**: 실패집합 seed 강건성 = 모방격차 가설 실증 — cube-placement seed 4종에서 실패 rollout 이 완전 이동(42{2,5,8}·7{9}·123{0,1}·2026{5}), 4-seed 평균 **0.825**(운영 seed42 0.70 은 비관적 끝단) → 병목 = 섭동강건성 아닌 **큐브배치 커버리지**. 상세: `2026-07-04_phase2-w1-seed-robustness.md`
  - [v] **7/5**: DR 50ep 합성 — `data/episodes_cl_dr` 50ep/3350frame(성공 50/50, yield 86%, lift 40.2~45.3mm), 별도 데이터셋 루트라 운영 `episodes_cl`·`rollout_summary.json` 불변. 상세: `2026-07-05_phase2-w1-dr-dataset-synthesis.md`
  - [v] **7/7 — W1 종료**: DR-trained(`act_cl_dr/epoch_0099`) 4-seed 공정추정 → baseline **0.825** vs DR-trained **0.800**(성공률 통계적 동등), 유일 개선 = median lift ~44→~50mm 전 시드 +6mm(임계값 위라 이진판정 무영향). **결론: DR 축 증강은 sim 성공률 천장을 못 올린다 → 다음 레버 = 배치 다양성.** 상세: `2026-07-07_phase2-w1-dr-trained-rollout-compare.md`
- W2 (7/8 ~): Zero-shot 실기 추론 → 격차 측정
  - *실기 스텝 = Orin/실기 SSH 외부의존 미수신 → 진입 불가. 대기 중 sim track 은 W1 결론이 지목한 배치 다양성 레버로 전진.*
  - [v] **7/8~7/21**: 배치 다양성(floor) 재학습 **결착** — `episodes_floor` 50ep/3350f 로 ACT 재학습을 **12-run 만에 창 안 완주**(`act_floor/epoch_0041`, 42epoch, 3.76h, loss 0.0259). 이상종료 원인 순차 규명(FD 누수 → `persistent_workers` fix · num_workers=0 · RLIMIT · GPU OOM/jetsam 반증) 끝에 **고정 벽시계 04:04 외부 SIGKILL 확정**, 자가치유 `COP_EPOCHS=42` 로 창 회피. 상세: `2026-07-19_*`, `2026-07-21_floor-trained-first-rollout.md`
  - [v] **7/21**: floor-trained 첫 rollout 측정 — seed42 N=10 → **success 10/10, 성공률 1.0, median lift 66.0mm**(max_lift 0.056~0.068m, 임계 0.04m 여유). open-loop 0% → closed-loop 0.70 → **floor 1.0** 도약. 상세: `2026-07-21_floor-trained-first-rollout.md`
  - [v] **7/22**: floor-trained 4-seed 공정추정 — seed 42/7/123/2026 **전부 1.0**(66.0/65.3/60.0/64.9mm), **40/40 rollout 성공 · 실패 배치 0건**. baseline 0.825 / DR-trained 0.800 → floor-trained **1.000** 으로 7/7 결론의 처방을 실증 확증. 운영 `rollout_summary.json` md5 `5207f67b…` 전후 불변. 상세: `2026-07-22_floor-trained-4seed-fair-estimation.md`
  - [ ] **Zero-shot 실기 추론 → Sim2Real 격차 측정** — *(2026-08-05 전제 갱신)* 실기가 omen
    (실기 담당자, soarm_lerobot)에서 진행 중이므로 경로 = Orin SSH 가 아니라 **omen 협업**.
    단, 실기 트랙 작업이 pick&place 가 아닌 S1 버튼누르기라 이 항목의 실효 검증은
    **Phase 3 W4 핸드오프로 이관**. Orin 온디바이스 배포는 시연 단계 항목으로 보류
  - [ ] **full-epoch(100) apples-to-apples 공정비교** — 현 결론은 42epoch 저학습 기준이라 방향은 더 강하지만 엄밀 비교는 미완. **Phase 3 착수로 우선순위 하향(보류)**. *8/5 갱신: 04:04 killer 원인 규명 완료(`ai.hermes.autoupdate` 04:00 → gateway kickstart 프로세스 그룹 SIGKILL — external-dependencies.md 참조), `start_act_train.sh` 세션 분리 fix 적용 → 이제 마음만 먹으면 full-epoch 가능*
  - 🔄 **2026-07-08 — 배치 다양성(floor) 사이클 ACT 재학습 착수(in-flight)**: 드라이버가 W1 타겟
    `episodes_cl_dr` 을 STAGE=완료/유지(50ep·0.7)로 닫고 **예약 사이클 `.next=episodes_floor`(바닥/받침대
    없는 파지 = 배치 커버리지↑)로 전환** → `episodes_floor`(50ep/3350f, 수집 yield 98%, 배치 x0.11~0.15)
    로 ACT 100epoch 재학습 시작(pid 94316, `--no-resume`, →`checkpoints/act_floor`). 현 epoch 0(막 시작).
    **마커 2단계+ckpt 3자 격리 정상**: target=`episodes_floor`·marker=`episodes_cl_dr:1783181837`(직전 승격값
    유지, 운영 rollout_summary 불변)·pending=`episodes_floor:1783324998`(대기). 6/22 SILENT 반대·설계대로
    학습 미완이라 승격/측정 보류 → baseline 무손상. **의의**: 7/7 W1 실증(병목=배치 커버리지, DR 축은 sim
    천장 0.825↔0.800 못 올림)의 처방 = 배치 다양성 데이터 재학습의 첫 실측. [자가치유] 없음. 상세:
    `2026-07-08_phase2-w2-floor-placement-retrain-inflight.md`. **다음(드라이버)**: 학습완료→pending 승격→
    `act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed(42/7/123/2026) 공정추정으로 배치 다양성이
    성공률 천장을 올리는지 비교.
  - 🔄 **2026-07-09 — floor 재학습 재시도 + FD 누수 자가치유(in-flight)**: 어제 run(pid 94316)이
    epoch ~50(epoch_0049 03:45 저장 후) 부근에서 **이상종료** — 드라이버가 감지(`metrics 마지막 epoch
    미달`) 후 원인 `OSError: [Errno 24] Too many open files` 로 **재학습 재시도**(STAGE=학습시작, **새 run
    pid 21661** `--no-resume`). **근본원인 규명**: `train_act.py` DataLoader 1회 생성 + epoch 루프 매 epoch
    재순회 + `num_workers=4` `persistent_workers` 미설정 → 매 epoch 워커 4개 재spawn → macOS spawn +
    낮은 `ulimit -n` 에서 파이프 FD 누적 → ~50 epoch 후 고갈. **[자가치유]**: DataLoader 에
    `persistent_workers=workers > 0` 추가(워커 1회 spawn 후 재사용, smoke 0 은 False 게이트) — surgical
    1줄, 학습 로직 무변경, ast/DataLoader 스모크 검증. **fix 발효**: pid 21661 은 수정 이전 로드 → 이 run 은
    미적용(재크래시 시 내일 드라이버가 수정 코드로 재시작→완주); 하드룰상 학습 kill/재실행 안 함. **무결성
    격리 유지**: target=`episodes_floor`·marker=`episodes_cl_dr:1783346557`(운영 rollout_summary 불변)·
    pending=`episodes_floor:1783324998` 대기, 학습 미완→승격/측정 보류→baseline 무손상. pid 21661 현재
    epoch 0 loss 38.8→5.67 정상 수렴. 상세: `2026-07-09_phase2-w2-floor-retrain-fd-selfheal.md`.
  - 🔄 **2026-07-10 — floor 재학습 3차 = FD-fix 발효 run(in-flight)**: 어제 run(pid 21661, fix
    미적용 코드 로드)이 예측대로 ~epoch 50 부근 FD 고갈 재크래시(`epoch_0049` 03:45 마지막) →
    드라이버가 이상종료 감지(`metrics 마지막 epoch 미달` + `OSError [Errno 24] Too many open files`)
    후 **새 run pid 39732** 시작(23:00:26, `--epochs 100 --no-resume`, →`checkpoints/act_floor`).
    **오늘의 진척 = fix 발효 시점 전환**: pid 39732 는 FD-fix 커밋 `c827ffe`(7/9) **이후** 디스크
    `train_act.py`(persistent_workers L185~196) 를 로드 → **수정이 이 run 에 실제 적용** → 매 epoch
    워커 재spawn 없이 **100epoch 완주 기대**(어제 예고 "내일 드라이버가 수정코드로 재시작→완주" 실현).
    현 epoch 0 step 120 loss 27.1→6.4 정상 수렴, log mtime 23:01:56. **무결성 격리 유지**:
    target=`episodes_floor`·marker=`episodes_cl_dr:1783181837`(직전 승격값 유지, 운영 rollout_summary
    act_cl_dr 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998` 대기(미승격), 학습 미완→승격/측정
    보류→baseline 무손상. datasets floor/cl/cl_dr 각 50/3350 불변. [자가치유] 없음(어제 fix 첫 발효가
    오늘의 진척). 상세: `2026-07-10_phase2-w2-floor-retrain-fdfix-run.md`. **다음(드라이버)**: 완주→
    pending 승격→`act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed 공정추정으로 배치
    다양성이 성공률 천장을 올리는지 비교.
  - 🔄 **2026-07-11 — floor 재학습 4차 = FD 누수 근본강화(RLIMIT_NOFILE) + 재시작(in-flight)**:
    어제 FD-fix(`persistent_workers`) 발효 run(pid 39732)이 crash 를 ~epoch **49→59** 로 밀었으나
    (`epoch_0059` 04:02 마지막, metrics 마지막=epoch 59, `epoch_0069`+ 없음) **100epoch 완주엔 실패** →
    드라이버가 이상종료 감지 후 **새 run pid 56445**(23:00:54, `--epochs 100 --no-resume`, →`act_floor`)
    시작. **근본원인 재규명**: 진짜 벽은 누수 *속도* 가 아니라 **크론 셸이 물려준 낮은 `RLIMIT_NOFILE`
    소프트 한도(macOS 기본 256)** — persistent_workers 로도 epoch 당 소량 FD/세마포어 누적
    (`256/~4≈64ep` → crash ~59 정합, 드라이버 출력 "21 leaked semaphore" 방증). **[자가치유]**:
    `train_act.py` `main()` 진입 즉시 `_raise_fd_limit()` 로 학습 프로세스가 **부모 셸과 무관하게
    자기 FD 소프트 한도를 하드(무제한)까지** 상승 → 천장 제거(surgical: 헬퍼1+main1줄+관측필드1,
    학습로직 무변경). **검증**: ast OK · 소프트 256 강제→호출→`after unlimited` PASS · `--dry-run`
    `fd_limit_raised` 노출. **발효는 다음 run**(pid 56445 는 미수정 코드 로드→~59 재crash 예상→내일
    드라이버 재시작이 수정코드 로드→완주 기대. 7/9→7/10 패턴). **무결성 격리 유지**: target=
    `episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(직전 승격값)·pending=`episodes_floor:1783324998`
    (대기)·measured=`episodes_cl_dr:1783346557`, 학습 미완→승격/측정 보류→운영 rollout_summary
    (act_cl_dr 0.70/50.2mm, 7/7) 불변→baseline 무손상. datasets floor/cl/cl_dr 각 50/3350 불변.
    상세: `2026-07-11_phase2-w2-floor-retrain-fd-rootfix.md`. **다음(드라이버)**: 완주→pending 승격→
    `act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed 공정추정으로 배치 다양성이 성공률
    천장을 올리는지 비교.
  - 🔄 **2026-07-12 — floor 재학습 5차 = RLIMIT-fix 발효 run(in-flight)**: 어제 run(pid 56445,
    RLIMIT-fix 미적용 코드 로드)이 예측대로 ~epoch 59 부근 FD 고갈 재크래시 → 드라이버가 이상종료
    감지(`21 leaked semaphore` + `OSError [Errno 24]`) 후 **새 run pid 85398** 시작(23:00, `--epochs
    100 --no-resume`, →`checkpoints/act_floor`). **오늘의 진척 = FD 근본 fix 발효 시점 전환**: pid
    85398 은 RLIMIT-fix 커밋 `3fa8bb6`(7/11) **이후** 디스크 `train_act.py`(persistent_workers L196 +
    `_raise_fd_limit()` L452) 를 로드 → 두 FD fix 실제 적용 → 지난 4 run(pid 94316·21661·39732·56445)
    을 ~49~59 epoch 에서 죽인 macOS 256 FD 천장 제거 → **100epoch 완주 기대**(7/9→7/10 패턴 재현,
    어제 예고 "내일 드라이버 재시작이 수정코드 로드→완주" 실현). 현 epoch 0 step 30 loss 36.7→17.4
    정상 수렴. **무결성 격리 유지**: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`
    (직전 승격값 유지, 운영 rollout_summary act_cl_dr 0.70/50.2mm 불변)·pending=
    `episodes_floor:1783324998`(mtime 7/12 23:00, 대기·미승격)·measured=`episodes_cl_dr:1783346557`,
    학습 미완→승격/측정 보류(6/22 SILENT 반대·설계대로)→baseline 무손상. datasets floor/cl/cl_dr 각
    50ep 불변. [자가치유] 없음(어제 RLIMIT-fix 첫 발효가 오늘의 진척). 상세:
    `2026-07-12_phase2-w2-floor-retrain-rlimit-effective-run.md`. **다음(드라이버)**: 완주→pending
    승격→`act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed 공정추정으로 배치 다양성이
    성공률 천장을 올리는지 비교.
  - 🔄 **2026-07-13 — floor 재학습 6차 = FD 누수 근본치유(num_workers=0) + 재시작(in-flight)**:
    어제 "RLIMIT-fix 발효 run"(pid 85398)이 예상과 달리 **또 epoch 58 에서 이상종료**(`21 leaked
    semaphore` + `OSError [Errno 24]`) → 드라이버 감지 후 **새 run pid 8470**(23:00:49, `--epochs 100
    --no-resume`, →`act_floor`) 시작. **두 선행 fix 무효 판명**: 크래시 트레이스백이 epoch 루프 안에서
    DataLoader 가 **매 epoch 새 워커 spawn**(`_MultiProcessingDataLoaderIter` 재생성→`os.pipe()`,
    `256/4워커≈58ep` 정합)함을 지목 → persistent_workers(7/9)·RLIMIT_NOFILE 셀프상승(7/11) 둘 다
    **재spawn 이라는 누수 원천을 못 막고 증상만 늦추려** 한 것. **[자가치유]**: `train_act.py` 비smoke
    학습 경로 `effective_workers` 를 `None`(→기본 4)에서 **`0` 강제**(`num_workers=0`)
    → SingleProcess DataLoader → 워커 subprocess/os.pipe/세마포어 **생성 자체 없음 → FD 누수 물리적
    불가**. 6-run 실패의 유일 원인(워커 churn) 근본 제거. 데이터 3350frame 소형이라 멀티프로세싱 이득
    미미(비용≈0). surgical(else 분기 상수 1개+주석, 로직 무변경), `ast` OK·`persistent_workers=workers>0`
    자동 False. **발효는 다음 run**(pid 8470 은 미수정 코드 로드→오늘밤 ~58 재크래시 예상→내일 드라이버
    재시작이 수정코드 로드→**완주 기대**; 7/9→7/10 패턴이나 이번은 증상지연 아닌 원천제거라 확실성↑).
    현 epoch 0 step 320 loss 41.2→4.5 정상 수렴. **무결성 격리 유지**: target=`episodes_floor`·
    trained_on=`episodes_cl_dr:1783181837`(직전 승격값·운영 rollout_summary act_cl_dr 0.70/50.2mm 불변)·
    pending=`episodes_floor:1783324998`(대기·미승격)·measured=`episodes_cl_dr:1783346557`, 학습 미완→
    승격/측정 보류→baseline 무손상. datasets floor/cl/cl_dr 각 50ep 불변. 상세:
    `2026-07-13_phase2-w2-floor-retrain-numworkers-selfheal.md`. **다음(드라이버)**: 완주→pending 승격→
    `act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed 공정추정으로 배치 다양성이 성공률
    천장을 올리는지 비교.
  - 🔄 **2026-07-14 — floor 재학습 7차 = num_workers=0 fix 발효 run(in-flight)**: 어제 run(pid 8470,
    num_workers=0 fix **미적용** 코드 로드)이 예측대로 **epoch 58 이상종료**(로그 tail `{"epoch": 58,
    "step": 340}` 직후 `21 leaked semaphore`) → 드라이버가 이상종료 감지 후 **새 run pid 48167**
    시작(23:00:41, `--epochs 100 --no-resume`, →`checkpoints/act_floor`). **오늘의 진척 = FD 누수
    근본치유(num_workers=0) 발효 시점 전환**: pid 48167 은 num_workers=0 커밋(7/13) **이후** 디스크
    `train_act.py` 로드 → 수정 실제 적용. 검증: L501~506 **비smoke else 분기** `effective_workers=0`
    (이 run 은 `--smoke` 없음→else 진입→workers=0), L196 `persistent_workers=workers>0`→자동 False →
    **워커 재spawn 없음 → FD 누수 물리적 불가 → 100epoch 완주 기대**(7/9→7/10 패턴, 이번은 증상지연
    아닌 누수 원천 제거라 확실성↑). 현 epoch 0 step 20 loss 35.99→22.58 정상 수렴. **무결성 격리
    유지**: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(직전 승격값 유지, 운영
    rollout_summary act_cl_dr 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998`(대기·미승격)·
    measured=`episodes_cl_dr:1783346557`, 학습 미완→승격/측정 보류→baseline 무손상. datasets
    floor/cl/cl_dr 각 50ep/3350frame 불변. [자가치유] 없음(어제 num_workers=0 fix 첫 발효가 오늘의
    진척). 상세: `2026-07-14_phase2-w2-floor-retrain-numworkers-effective-run.md`. **다음(드라이버)**:
    완주→pending 승격→`act_floor/epoch_0099` 측정→floor-trained rollout, 이후 4-seed 공정추정으로
    배치 다양성이 성공률 천장을 올리는지 비교.
  - 🔄 **2026-07-15 — floor 재학습 8차 = FD 가설 경험적 반증 + MPS OOM 재규명(in-flight)**:
    어제 "num_workers=0 발효 run"(pid 48167, fix **적용** 코드)이 예상과 달리 **또 epoch 57
    이상종료**(`metrics 마지막 epoch 미달`, shutdown `1 leaked semaphore` — 어제 21→오늘 1,
    워커 소멸 방증) → 드라이버가 새 run **pid 73001**(23:00:14, `--epochs 100 --no-resume`,
    →`act_floor`) 시작. **오늘의 반전 = 3일간 쫓던 워커 FD 누수 가설을 프로브로 직접 반증**:
    `_fd_leak_probe.py` 로 `episodes_floor`+num_workers=0 DataLoader 를 4 full-epoch(각 418 step
    완전 순회) 재순회 → `/dev/fd` = **baseline 6·epoch0~3 전부 6 고정**(누수 재현 불가). crash
    재규명 근거: ①num_workers=0 실제 적용에도 crash epoch=57(7 run 동일 천장) ②이번 run
    **OSError [Errno 24] traceback 부재** = epoch57 도중(step370/418) SIGKILL 시그니처(OOM)
    ③epoch 시간 **완전 평탄 ~313s**(점진 slowdown 아님). → **유력 원인 = MPS 메모리 누적
    OOM**(16GB M5, torch MPS 할당자 캐시 미반환), 워커 FD 는 2차 증상. **[자가치유]**:
    `train_act.py` epoch 루프에 ①`torch.mps.empty_cache()`+`gc.collect()`(완화, mps 게이트,
    정확도 무영향) ②`mps_mem=driver_allocated_memory()` 로깅(계측 — 다음 run 이 OOM 가설
    직접 확증/반증; 이전 3 fix 와 차이 = 가설을 계측으로 검증). 검증: ast OK·torch.mps API
    존재·`--smoke` 완주(cpu, `mps_mem:null`). **발효는 다음 run**(pid 73001 은 수정 이전 코드
    →오늘밤 ~57 재crash 예상→내일 드라이버 재시작이 수정+계측 코드 로드→완주 또는 메모리
    곡선 확보). **무결성 격리 유지**: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`
    (운영 rollout_summary act_cl_dr 0.70/50.2mm 불변)·pending=`episodes_floor:1783324998`(대기)·
    measured=`episodes_cl_dr:1783346557`, 학습 미완→승격/측정 보류→baseline 무손상. datasets
    floor/cl/cl_dr 각 50ep 불변. 상세: `2026-07-15_phase2-w2-floor-retrain-fd-disproof-mps-oom.md`.
    **다음(드라이버)**: 완주→pending 승격→`act_floor/epoch_0099` 측정→floor-trained rollout,
    이후 4-seed 공정추정 비교 / 재crash 시 `mps_mem` 곡선으로 OOM 확정→batch_size 축소 등 root fix.
  - 🔄 **2026-07-16 — floor 재학습 9차 = MPS-fix + mps_mem 계측 발효 run(in-flight)**: 어제 8차
    run(pid 73001, mps-fix **미적용** 코드)이 예측대로 **epoch 56 이상종료**(`metrics 마지막 epoch
    미달`, tail `{"epoch":56,"step":270}` 후 `1 leaked semaphore`) → 드라이버가 새 run **pid 7243**
    시작(23:00:22, `--epochs 100 --no-resume`, →`checkpoints/act_floor`). **오늘의 진척 = mps-fix
    발효 시점 전환**: pid 7243 은 mps-fix 커밋 `32fcb5d`(7/15) **이후** 디스크 `train_act.py` 로드
    → 수정 실제 적용(L395 `mps_mem=torch.mps.driver_allocated_memory()` 계측 · L414
    `torch.mps.empty_cache()`+`gc.collect()` 완화 · L509 `effective_workers=0` 유지). **의의**:
    8-run 을 ~56~59 에서 죽인 천장에 **처음으로 완화+계측 동시 적용** → 완주 시 MPS 캐시 미반환이
    진짜 원인 실증(해소), ~57 재crash 시 `mps_mem` 곡선으로 **OOM 직접 확증/반증→batch_size 축소 등
    root fix** 직행(어느 쪽이든 워커 FD red-herring 루프 탈출). 현 epoch 0 step 30 loss 28.5→14.2
    정상 수렴, pid 7243 alive. **무결성 격리 유지**: target=`episodes_floor`·trained_on=
    `episodes_cl_dr:1783181837`(직전 승격값 유지, 운영 rollout_summary act_cl_dr 0.70/50.2mm 불변)·
    pending=`episodes_floor:1783324998`(대기·미승격)·measured=`episodes_cl_dr:1783346557`, 학습 미완→
    승격/측정 보류→baseline 무손상. datasets floor/cl/cl_dr 각 50ep/3350frame 불변. `act_floor` 최신
    ckpt=`epoch_0059`(과거 run, crash56<59→신규 상위 ckpt 없음). [자가치유] 없음(어제 mps-fix 첫
    발효가 오늘의 진척). 상세: `2026-07-16_phase2-w2-floor-retrain-mps-fix-effective-run.md`.
    **다음(드라이버)**: 완주→pending 승격→`act_floor/epoch_0099` 측정→floor-trained rollout, 이후
    4-seed 공정추정 비교 / 재crash 시 `mps_mem` 곡선으로 OOM 확정→batch_size 축소 등 root fix.
  - 🔄 **2026-07-17 — floor 재학습 10차 = mps_mem 판독으로 GPU OOM 반증 + RSS 프로브(자가치유)**:
    어제 9차 run(pid 7243, **mps-fix 발효 코드**)이 완화(`empty_cache`)에도 **또 epoch 58 이상종료**
    (`metrics 마지막 epoch 미달`, tail `{"epoch":58,"step":10}` 후 `1 leaked semaphore`, traceback 없음)
    → 드라이버가 새 run **pid 26783**(23:00:34, `--epochs 100 --no-resume`, →`act_floor`) 시작.
    **오늘의 결착 = 9-run 만에 GPU OOM 가설 반증**: 계측된 `mps_mem` 곡선이 epoch 0 5.72GB→epoch 7
    6.65GB 1회 상승 후 **epoch 8~57 완전 평탄(6.65~6.67GB, 단조증가 전무)**. 6.65GB=16GB 통합메모리
    42% → **GPU OOM 물리적 불가**(7/15 OOM 가설 반증; FD 가설은 프로브로 이미 반증 → FD·GPU OOM 둘 다
    아님). **crash 시그니처 종합**: crash epoch ~57(9-run 천장)·mps_mem 평탄·elapsed_sec 평탄(~311s,
    slowdown 없음)·traceback 없음+leaked semaphore = **외부 SIGKILL 급사**. epoch57 done=04:03:54→crash
    ~04:04(고정 23:00 시작 탓 epoch~57↔벽시계~04:00 교락). **남은 유일 미측정 변수 = 프로세스 RSS**
    (mps_mem 은 GPU 할당자만 계측; jetsam 통합메모리 압박이면 GPU 평탄이어도 RSS 상승). **[자가치유]**:
    `train_act.py` ①모듈 top `import resource`(지역 import뿐→epoch 루프 NameError 방지) ②`epoch_metric`
    에 `rss_bytes`(getrusage RUSAGE_SELF, macOS=bytes) 1필드 ③반증된 OOM 주석 2곳 정정 — surgical, 학습
    로직 무변경(`ast` OK·샘플 17MB bytes 확인). 판독: 다음 crash 시 **RSS 평탄=외부/시각연동**(교락 해제/
    resume/epoch 하향), **RSS 상승=jetsam**(batch/워커 축소). 발효는 다음 run(pid 26783 은 23:00:34 편집前
    로드→오늘밤 ~57 재crash 예상→내일 재시작이 계측코드 로드). 현 epoch 0 step 350 loss 3.79 정상 수렴.
    **무결성 격리 유지**: target=`episodes_floor`·trained_on=`episodes_cl_dr:1783181837`(불변, 운영
    rollout_summary act_cl_dr 0.70/50.2mm 불변)·pending=`episodes_floor`(대기·미승격)·measured=
    `episodes_cl_dr:1783346557`, 학습 미완→승격/측정 보류→baseline 무손상. datasets floor/cl/cl_dr 각
    50ep/3350frame 불변. `act_floor` 최신 ckpt=`epoch_0059`(과거 run, crash56<59→신규 상위 ckpt 없음).
    상세: `2026-07-17_phase2-w2-floor-retrain-oom-refuted-rss-probe.md`. **다음(드라이버)**: 완주→pending
    승격→`act_floor/epoch_0099` 측정→floor rollout→4-seed 공정추정 / 재crash 시 RSS 곡선으로 jetsam vs
    외부 시각연동 판정→root fix. **오늘 OOM 반증 = 9-run 증상추적 루프 탈출의 첫 결착.**
  - 🔄 **2026-07-18 — floor 재학습 11차 = RSS 프로브 발효 run(in-flight)**: 어제 10차 run(pid 26783,
    RSS-probe **미적용** 코드)이 예측대로 **epoch 57 이상종료**(드라이버 tail `{"epoch":57,"step":310}`
    후 `1 leaked semaphore`, traceback 없음) → 드라이버가 새 run **pid 5069** 시작(23:00:52, `--epochs
    100 --no-resume`, →`checkpoints/act_floor`). **오늘의 진척 = RSS 프로브 발효 시점 전환**: pid 5069 는
    RSS-probe 커밋 `884294f`(7/17) **이후** 디스크 `train_act.py`(L22 `import resource` · L402 `rss_bytes`
    =getrusage RUSAGE_SELF) 로드 → 계측 실제 적용. 방증: 10차 run `act_train_metrics.jsonl` 은 `mps_mem`
    만 있고 `rss_bytes` 부재(편집前 코드). → **다음 crash(pid 5069)가 9-run 만에 처음 RSS 곡선 남김** →
    jetsam vs 외부 시각연동 최종 판정(마지막 미측정 변수 계측). **GPU OOM 재확인 반증**: 10차 run mps_mem
    epoch 54/55/56 **완전 평탄 6.64GB**(=16GB 42%) · elapsed_sec 평탄 ~313s · crash epoch ~57(천장 불변)
    · traceback 없음+leaked semaphore = **외부 SIGKILL 급사** 재현(FD·GPU OOM 둘 다 반증 유지). 현 epoch
    0 step 40 loss 29.2→12.3 정상 수렴. **무결성 격리 유지**: target=`episodes_floor`·trained_on=
    `episodes_cl_dr:1783181837`(직전 승격값 불변, 운영 rollout_summary act_cl_dr 0.70/50.2mm 불변)·pending=
    `episodes_floor:1783324998`(대기·미승격)·measured=`episodes_cl_dr:1783346557`, 학습 미완→승격/측정
    보류→baseline 무손상. datasets floor/cl/cl_dr 각 50ep/3350frame 불변. `act_floor` 최신 ckpt=
    `epoch_0059`(과거 run, crash57<59→신규 상위 ckpt 없음). [자가치유] 없음(어제 RSS 프로브 첫 발효가
    오늘의 진척). 우선순위 5종 회귀 PASS(camera·6dof·collector 2/2 yield100% lift43.5mm·pick 결정론
    0.3228m·관절각 0.0244°<1°). 상세: `2026-07-18_phase2-w2-floor-retrain-rss-probe-effective-run.md`.
    **다음(드라이버)**: 완주→pending 승격→`act_floor/epoch_0099` 측정→floor-trained rollout→4-seed
    공정추정 vs baseline 0.825/DR-trained 0.800 / 재crash 시 `rss_bytes` 곡선으로 jetsam vs 외부 시각연동
    판정→root fix.
  - 🔧 **2026-07-19 — floor 재학습 12차 = 시각연동 외부 SIGKILL 확정 + deadlock 규명 자가치유**:
    11차 run(pid 5069, RSS-probe 발효)이 **epoch 49 이상종료**(tail `{"epoch":49,"step":10}`,
    `1 leaked semaphore`, traceback 없음) → 드라이버가 새 run **pid 91975**(`--epochs 100 --no-resume`)
    재시작. **9-run 미스터리 종결**: RSS 프로브가 처음 남긴 곡선 = `rss_bytes` **789→811MB 초반 1회
    +22MB 후 39ep 완전 평탄**(jetsam 반증) · mps_mem ~6.64GB 평탄(GPU OOM 재반증). **결정적 증거 =
    epoch↔벽시계 교락 해제**: pid 5069 는 epoch 가 느려(평균 **368.8s** vs 이전 ~313s) **같은 ~04:04
    까지 49 epoch 만**(이전 57) 돌고 죽음(시작 23:00:52·ep48 완료 04:02:24·crash ~04:04:15) → crash 는
    **고정 epoch 아닌 고정 벽시계(~04:04)** = **외부 시각연동 SIGKILL 확정**(FD·GPU OOM·jetsam 3가설
    전부 기각). **진짜 deadlock 규명**: 100ep×~368s=~10h 는 23:00→04:04(5h) 창에 물리적으로 못 들어감 →
    `--no-resume` 매일 폐기 → 영원히 완주 불가(resume 도 L546 옵티마이저/epoch 리셋으로 완료게이트 못
    채움). **[자가치유]**: 드라이버 L36 `COP_EPOCHS:-100`→`:-42`(창 안 ~03:41 완주<04:04, override knob
    유지, surgical 1줄). 발효는 내일 재시작(오늘 pid 91975 는 편집前 --epochs 100 → 오늘밤도 재crash).
    **한계**: 42ep 저학습 → baseline(100ep) 대비 공정비교 아님. **full-epoch 복원 = ~04:04 killer 규명
    필요**(log show/launchctl → sandbox 차단, 에스컬레이션). **무결성 격리 유지**: 운영 rollout_summary
    act_cl_dr 0.70/50.2mm 불변·마커 4종 격리·datasets 불변·joint_angle 회귀 PASS 0.0244°. 상세:
    `2026-07-19_floor-retrain-timelinked-sigkill-confirmed.md`. **다음(드라이버)**: 내일 ~03:41 완주→
    pending 승격→`act_floor/epoch_0041` 측정→**12-run 만에 첫 floor rollout**→4-seed 공정추정.
  - ✅ **2026-07-21 — floor-trained 첫 rollout = seed42 10/10 = 1.0 (12-run 결착)**: 7/19 자가치유
    (`COP_EPOCHS=42`, 04:04 벽시계 killer 회피)가 발효 → floor 재학습이 **12-run 만에 처음 창 안 완주**
    (`act_floor/epoch_0041` mtime 7/21 02:46, 42epoch, wall_clock 3.76h, loss 0.0259, rss 925MB·mps
    5.66GB 평탄=jetsam·GPU OOM 재반증) → 드라이버 STAGE=측정(`epoch_0041`, seed42, N=10, 씬
    `scene_grasp_floor.xml`) = **success 10/10, success_rate 1.0, median lift 66.0mm**(max_lift
    0.056~0.068m 전부 임계 0.04m 여유). **의의**: open-loop 0%→closed-loop 0.70→**floor 1.0** —
    7/7 W1 결론(병목=배치 커버리지, DR 축은 천장 못 올림 0.825↔0.800)의 처방(배치 다양성 데이터)이
    실측으로 적중, seed42(비관적 끝단 0.70)에서 1.0 도약. **한계**: 42epoch<baseline 100epoch →
    완전 공정비교 아님(04:04 killer 탓 full-epoch 불가, 외부 에스컬레이션 대기) · 단일 seed42 →
    정식 판정은 4-seed 공정추정 후속. **무결성 격리 불변**: datasets floor/cl/cl_dr 각 50ep · 마커 3자
    정합(target=`episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=`episodes_floor:1783710169`).
    [자가치유] research-log 2026-07-20 결손 → git·마커로 재구성. 상세:
    `2026-07-21_floor-trained-first-rollout.md`. **다음(드라이버)**: `act_floor` 4-seed(42/7/123/2026)
    공정추정 → baseline 0.825/DR-trained 0.800 대비 배치 다양성이 성공률 천장을 올리는지 확정.
  - ✅ **2026-07-22 — floor-trained 4-seed 공정추정 = 4 seed 전부 1.0 (배치 다양성이 천장을 올렸다)**:
    드라이버 STAGE=완료/유지(새 사이클 미트리거)여서, 야간 에이전트가 7/4·7/7 과 동일 프로토콜로
    나머지 3 seed(7/123/2026)를 `act_floor/epoch_0041` 에 **비파괴 프록시** rollout(`--summary-suffix
    _floor_seed{N}`, 운영 summary 불변). **결과: seed42 1.0(66mm)·seed7 1.0(65.3mm)·seed123 1.0(60mm)·
    seed2026 1.0(64.9mm) → 4-seed 평균 성공률 1.000, 40/40 rollout 성공, 실패 배치 0건.** **결론**:
    baseline 0.825 / DR-trained 0.800 → **floor-trained 1.000** — 7/7 W1 결론(병목=큐브배치 커버리지,
    DR 축은 천장 못 올림)의 처방(배치 다양성 데이터)이 4-seed 로 **실증 확증**. baseline·DR-trained 이
    seed마다 특정 배치에서 실패(42{2,5,8}·123{0,1}·2026{5})했던 모방격차를 floor 데이터가 전 seed
    실패 0 으로 메움. **한계**: 42epoch<baseline 100epoch(04:04 killer 탓 full-epoch 불가) → 저학습에도
    1.0 이라 결론 방향은 더 강해지나 엄밀한 100ep apples-to-apples 는 04:04 killer 규명(외부
    에스컬레이션) 후속. **무결성 격리**: 운영 `rollout_summary.json` md5 `5207f67b…` 전후 불변·신규
    `rollout_summary_floor_seed{7,123,2026}.json` 3종만 추가·datasets floor/cl/cl_dr 각 50ep/3350f 불변·
    마커 3자 정합 유지. 상세: `2026-07-22_floor-trained-4seed-fair-estimation.md`. **다음**: sim 트랙
    성공률 레버 규명 완료 → 실기 스텝(W2 zero-shot, Orin SSH 외부의존 미수신 대기) / full-epoch 복원
    (04:04 killer 진단권한 대기).
  - 🔄 **2026-07-23 — sim 성공률 레버 결착 후 hold + 우선순위 5종 회귀**: 드라이버 STAGE=완료/유지
    (episodes_floor 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 트랙
    성공률 레버(배치 다양성)는 7/22 4-seed 공정추정(4/4=1.0)으로 이미 결착 → hold 일. 야간 에이전트가
    **우선순위 5종 회귀 독립 실행**: camera 30f 2대 · 6dof 2501f · pick min_approach 0.3228327m 결정론
    (max_lift 0.0=고정포즈 expert 미접근 기지값) · collector 2/2 yield100% lift41.8mm(스모크 격리→삭제) ·
    joint_angle 0.0244°<1° — **5종 전부 PASS**. **무결성 격리 불변**: 운영 `rollout_summary.json` md5
    `5207f67b189645de1bb26c124873b683` 7/22 값과 동일(측정 후 불변, act_floor/epoch_0041 seed42 1.0/66mm)·
    마커 3자 정합(target=`episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep 불변·학습 프로세스 없음. [자가치유] 없음.
    상세: `2026-07-23_phase2-w2-sim-lever-hold-regression.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 스텝(W2 zero-shot, Orin SSH 미수신) / full-epoch(100) 공정비교 복원(04:04 killer 진단권한 대기).
  - 🔄 **2026-07-25 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041)·마커 3자 정합(target=`episodes_floor`·
    trained_on=`episodes_floor:1783324998`·measured=`episodes_floor:1783710169`)·datasets
    floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스 없음 → **회귀/오염 0**. **[자가치유]
    2026-07-24 research-log 결손 → git 재구성**: 7/24 야간 sim 크론 전진 커밋 부재(git 상 7/24 는
    히스토리 커밋 `20f00da` 뿐)로 7/24 야간 전진 없이 hold 유지됐음을 확인, `research-log/2026-07-24.md`
    재구성 생성. 상세: `2026-07-25_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목
    모두 외부 의존 대기 — 실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer
    진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-26 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음 → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값 우회 산출. [자가치유]
    없음(7/25 log·roadmap 정합). 상세: `2026-07-26_phase2-w2-sim-lever-hold-integrity-audit.md`.
    **다음**: 남은 두 항목 모두 외부 의존 대기 — 실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100)
    공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-27 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25·7/26 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음 → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값 우회 산출. [자가치유]
    없음(7/26 log·roadmap 정합). 상세: `2026-07-27_phase2-w2-sim-lever-hold-integrity-audit.md`.
    **다음**: 남은 두 항목 모두 외부 의존 대기 — 실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100)
    공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-28 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25·7/26·7/27 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음 → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값 우회 산출. [자가치유]
    없음(7/27 log·roadmap 정합). 상세: `2026-07-28_phase2-w2-sim-lever-hold-integrity-audit.md`.
    **다음**: 남은 두 항목 모두 외부 의존 대기 — 실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100)
    공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-29 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25·7/26·7/27·7/28 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm,
    success 10/10)·마커 3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·
    measured=`episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습
    프로세스 없음(`pgrep train_act`→none) → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib
    로 동일 값 우회 산출. [자가치유] 없음(7/28 log·roadmap 정합). 상세:
    `2026-07-29_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-30 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25·7/26·7/27·7/28·7/29 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음(`pgrep train_act`→none) → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값
    우회 산출. [자가치유] 없음(7/29 log·roadmap 정합). 상세:
    `2026-07-30_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-07-31 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22·7/23·7/25·7/26·7/27·7/28·7/29·7/30 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음(`pgrep train_act`→none) → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값
    우회 산출. [자가치유] 없음(7/30 log·roadmap 정합). 상세:
    `2026-07-31_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-08-01 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22~7/31 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음(`pgrep train_act`→none) → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값
    우회 산출. [자가치유] 없음(7/31 log·roadmap 정합). 상세:
    `2026-08-01_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer 진단권한 에스컬레이션 대기).
  - 🔄 **2026-08-02 — sim 레버 결착 후 hold + 우선순위 5종 회귀 + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **우선순위 5종 회귀**
    (camera 30f×2 · 6dof 2501f · joint 0.0244°<1° · pick 0.3228327m 결정론 2run 동일 · collector 2/2
    yield100% lift42.3/43.5mm) **전부 PASS** + **비파괴 무결성 전수 감사**: 운영 `rollout_summary.json` md5
    `5207f67b189645de1bb26c124873b683` 7/22~8/01 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42,
    median lift 66.0mm)·마커 3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·
    measured=`episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음(`pgrep train_act`→none) → **회귀/오염 0**. [자가치유] collector `--root` 플래그 사용 / md5 CLI sandbox
    차단→`.venv` hashlib 우회. 상세: `2026-08-02_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은
    두 항목 모두 외부 의존 대기 — 실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer
    진단권한 에스컬레이션 대기).
  - 🔄 **2026-08-04 — sim 레버 결착 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_floor` 50ep·성공률 1.0, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. sim 레버
    (배치 다양성)는 7/22 4-seed 4/4=1.0 으로 이미 결착 → hold 일. 야간 에이전트가 **비파괴 무결성
    전수 감사**(이번 세션 도구결과): 운영 `rollout_summary.json` md5 `5207f67b189645de1bb26c124873b683`
    7/22~8/02 값과 **동일**(sr 1.0, ckpt act_floor/epoch_0041, seed42, median lift 66.0mm)·마커
    3자 정합(target=`data/episodes_floor`·trained_on=`episodes_floor:1783324998`·measured=
    `episodes_floor:1783710169`)·datasets floor/cl/cl_dr 각 50ep/3350f(info.json) 불변·학습 프로세스
    없음(`pgrep train_act`→none) → **회귀/오염 0**. md5 CLI sandbox 차단 → `.venv` python hashlib 로 동일 값
    우회 산출. **[자가치유] 2026-08-03 research-log 결손 → git 재구성**(8/03 야간 크론 전진 커밋 부재,
    마지막 커밋 `b9eaeec` 8/02 → hold 유지 확인, `research-log/2026-08-03.md` 재구성). 상세:
    `2026-08-04_phase2-w2-sim-lever-hold-integrity-audit.md`. **다음**: 남은 두 항목 모두 외부 의존 대기 —
    실기 W2 zero-shot(Orin SSH 미수신) / full-epoch(100) 공정비교(04:04 killer 진단권한 에스컬레이션 대기).
- W3: 실기 fine-tune (10 에피소드)
  - [ ] 실기 10 에피소드 수집 → fine-tune → 재측정 — 실기 확보 후 진입(W2 zero-shot 선행)
- W4: Diffusion Policy 동일 절차 + ACT 비교
  - [ ] Diffusion Policy 동일 절차 학습 + ACT 대비 비교

**완료 기준**: 실기 Pick 성공률 60% (Sim2Real 격차 < 30%p)

---

## Phase 3 — S1 리셋버튼 시뮬 (실기 정렬) (2026-08, 4주)

> **2026-08-05 재정의.** 실기 트랙(soarm_lerobot, omen)이 7/22 부터 **S1 = PCB 리셋 버튼
> 누르기 + P1 = 녹색 LED 판정**을 진행 중이다(데이터 10ep/목표 80, ACT 20k 학습 1회,
> 롤아웃 성공률 미측정·LED ROI 미캘리브). 시뮬은 막연한 "PCB 조정" 대신 **실기와 동일한
> 작업·동일한 관측 스키마**로 정렬한다 — 실기의 두 결핍(데이터 부족, 성공판정 부재)을
> 시뮬이 메우는 구조. 기존 pick&place 시뮬 트랙은 Phase 2 에서 결착(4-seed 1.0)로 종료.
> 참조: `https://github.com/deois/soarm_lerobot` (로컬 미러 `/Volumes/MARK_DATA/dev/soarm_lerobot`)
>
> **정렬 계약(실기와 동일해야 하는 것):** 카메라 이름 `top`(광각)+`closeup`(근접) 2대
> 640×480@30fps · `observation.state`/`action` = 6dof pos · task_label
> `"press the reset button"` · LeRobot v3 포맷(omen lerobot 0.6.1 로드 가능 확인 필수) ·
> PCB 15×15cm 존 배치 다양화(7/22 배치 커버리지 실증 교훈 그대로).

- W1 (8/5 ~ 8/11): 실기 트윈 씬 정합 — **2026-08-05 완료** (`sim/assets/pcb_reset_scene.xml` + `samples/training/sim_pcb_reset.py`, 자가검증 4/4 PASS)
  - [v] **8/5**: 실기 `pcb_reset_scene.xml` 기반 씬 이식 — 메인 레포 `sim/assets/`(SO-ARM100 중첩 레포 밖, 실기 레포와 동일한 assets 심링크 방식). 로드 스모크: 팔 6축 + pcb_board/reset_button/led
  - [v] **8/5**: 리셋 버튼 눌림 메커니즘 — 슬라이드 조인트(z, 3mm) + 스프링 복원(stiffness 150) + 변위 임계(-1.5mm). 자가검증: 눌림 latch → 스프링 복원 후에도 latch 유지, LED rgba 점등 반영
  - [v] **8/5**: `top`/`closeup` 2 카메라 640×480 실기 배치 근사 — top = 존 수직 상방(홈 자세에서 PCB 전체+팔 베이스, 실기 C920 뷰 서술과 일치 육안 검증) / closeup = 존 측면 근접(버튼·LED·그리퍼 접근영역, 보조광 추가로 그림자 해소). 홈 자세 `HOME_QPOS` 도입(팔이 top 뷰를 가리던 문제 해소)
  - [v] **8/5**: PCB 15×15cm 존 배치 무작위화 reset 훅 — x(0.15~0.30)×y(±0.075)+yaw ±10°, seed 결정론·존 경계 50회 검증
- W2 (8/12 ~ 8/18): expert + 합성 데이터 — **8/5 조기 착수** (`samples/training/sim_pcb_reset_collector.py`)
  - [v] **8/5**: closed-loop 버튼누르기 expert — **20-seed 95%**. 핵심 규명 3건:
    ① TCP(패드 갭 중점) 아닌 **jaw 끝 접촉점**(보드 접촉 실측 캘리브 `PRESS_LOCAL`)으로 겨냥해야 함
    ② 버튼↔보드 접촉 배제 필요(원본 트윈은 버튼 하단이 보드에 눌러붙어 물리적으로 안 눌렸음 — 실물 버튼은 보드 구멍 관통 구조. **버튼 치수·스프링은 실기 원본 그대로**, 환경 난이도 불변)
    ③ 남는 실패 5% = 존 구석의 기하 도달불가 배치(press 자세가 팔 링크의 보드 2.5mm 관통을 요구 — 같은 SO-101 인 실기도 동일). pan 정렬→경유→단계 하강(매단계 IK 재계산)→재시도 3
  - [v] **8/5**: LED latch = 공짜 정답 라벨 자동 성공판정 — 수집기가 latch 성공 에피소드만 저장 (P1 계약과 동일)
  - [v] **8/5**: 100ep 합성 완료 — `data/episodes_s1` **100ep/7,231frame** (시도 107, **yield 93%**, seed 20260805, 58MB). 전수 재로드 검증 통과: v3.0 · top+closeup 640×480 · state/action 6 · task "press the reset button". 실패 7건 = 기하 도달불가 배치(예측대로)
  - [ ] omen lerobot 0.6.1 로드 스모크 — 실기 담당자 협업 (데이터셋 전달 경로 협의 포함, W4 핸드오프와 병합 가능)
  - 🔧 **2026-08-05 야간 — S1 합성 결착 문서화 + Phase 2 hold + W3 ACT 인에이블러**:
    낮 세션이 Phase 3 W1+W2 커밋 완료(56cd84f 트윈 4/4·7096f13 expert 95%·88c655c
    100ep 합성). 야간 드라이버 STAGE=완료/유지(`episodes_floor` 50ep·sr 1.0, Phase 2
    레거시 타겟, 새 사이클 미트리거). **무결성 감사**: 운영 `rollout_summary.json` md5
    `5207f67b189645de1bb26c124873b683` 7/22~8/04 불변(sr 1.0, act_floor/epoch_0041,
    seed42, 66.0mm)·학습 프로세스 없음 → 회귀/오염 0. **S1 데이터셋 실측**:
    `episodes_s1` 100ep/7,231f, top+closeup, v3. **W3 인에이블러**: `train_act.py`
    미커밋 변경(`COP_DATASET_REPO_ID`+`COP_CAMERA_KEYS` env 오버라이드 3필드,
    기본값 불변·하위호환, `ast.parse` OK) → W3 ACT 학습이 `episodes_s1`(2카메라)를
    읽도록 준비. [자가치유] 없음. 상세: `2026-08-05_phase3-w2-s1-synth-hold-w3-enabler.md`.
    **다음**: W2 잔여 omen 로드 스모크(실기 협업) / W3(8/19~) episodes_s1 ACT 학습→LED 채점 rollout.
- W3 (8/19 ~ 8/25): ACT 학습 + 측정 — **2026-08-06 조기 완주** (`scripts/render_act_rollout_s1.py`)
  - [v] ACT 학습 (obs = top+closeup+state6) — 8/5 22:59~8/6 09:37 `episodes_s1`(2카메라) 30epoch
    완주(`act_s1_sim/epoch_0029`, wall 10.6h, loss 0.0133). **04:04 killer 관통 확증**(`start_new_session`
    분리로 gateway kickstart 그룹 SIGKILL 회피, epoch_0019 06:11·epoch_0029 09:37 생존).
  - [v] sim rollout 성공률 측정 (LED latch 자동 채점, 4-seed 공정추정) — seed 42/7/123/2026 =
    0.90/0.90/1.00/0.90 → **4-seed 평균 0.925**(37/40), nominal seed42 0.90, median press 2.1~3.7mm.
    **완료 기준 70% 초과.** 실패 3/40 = 존 구석 기하 도달불가(expert 95% 동류). 상세:
    `2026-08-06_phase3-w3-s1-act-rollout.md`.
  - 🔄 **2026-08-07 — 4-seed 재측정 재현성 확인 + W4 hold**: 드라이버 STAGE=측정, 수집/학습
    재실행 없음. 동일 ckpt `act_s1_sim/epoch_0029` 재측정(23:01~23:03) → seed42/7/123/2026 =
    0.90/0.90/1.00/0.90 **평균 0.925(37/40)**, 8/6 최초 측정과 완전 동일 = 결정론적 재현. ckpt
    측정 승격 복제 `epoch_0029_measured_0.925.bak` 생성, 요약 4종 갱신(측정시각·ckpt명·wall_clock만).
    실행 가능한 dated 항목 소진 → 다음 pending = W4 omen 핸드오프(외부 의존, 진입 불가). **관찰**:
    S1 정책 DR 민감도(8/7 02:xx 산출물, aggregate ~0.45 · light 0.6/friction 0.8/camera 0.8) —
    floor pick-place 정책(DR 강건)과 대조적, W4 Sim2Real 격차 보고 후보. [자가치유] 없음. 상세:
    `2026-08-07_phase3-w3-s1-remeasure-reproducibility-hold.md`.
  - 🔄 **2026-08-08 — S1 완주 후 hold + 무결성 전수 감사**: 드라이버 STAGE=완료/유지
    (`episodes_s1` 100ep·성공률 0.925, 새 사이클 미트리거) → 수집/학습/측정 재실행 없음. dated
    항목 W1~W3 전부 완료·다음 pending = W4 omen 핸드오프(외부 의존, 진입 불가) → hold 일. 야간
    에이전트 **비파괴 무결성 전수 감사**: 마커 3자 정합(target=`data/episodes_s1`·trained_on=
    `episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·학습 프로세스 없음·운영 4-seed
    (ckpt `act_s1_sim/epoch_0029_measured_0.925.bak`) 42/7/123/2026 = 0.90/0.90/1.00/0.90
    **평균 0.925(37/40)** 8/6·8/7 과 동일(`rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929`)·
    datasets s1 100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-08_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-09 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. dated W1~W3 완료·다음 pending = W4 omen
    핸드오프(외부 의존) → hold. 비파괴 감사: 마커 3자 8/8 값과 바이트 일치(target=`data/episodes_s1`·
    trained_on=`episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·학습 프로세스 없음·
    `rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8 대비 불변·datasets s1
    100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-09_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-10 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. dated W1~W3 완료·다음 pending = W4 omen
    핸드오프(외부 의존) → hold. 비파괴 감사: 마커 3자 8/9 값과 바이트 일치(target=`data/episodes_s1`·
    trained_on=`episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·학습 프로세스 없음·
    `rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8·8/9 대비 불변·datasets s1
    100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-10_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-11 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. 오늘은 W1 dated 범위(8/5~8/11) 마지막 날이나
    W1 전부 이미 `[v]` · dated W1~W3 완료 · 다음 pending = W4 omen 핸드오프(외부 의존) → hold.
    비파괴 감사: 마커 3자 8/10 값과 바이트 일치(target=`data/episodes_s1`·trained_on=
    `episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·학습 프로세스 없음·
    `rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8·8/9·8/10 대비 불변·
    datasets s1 100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-11_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-12 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. 오늘은 W2 dated 범위(8/12~8/18) 시작일이나
    잔여 W2 항목 = omen lerobot 로드 스모크 1건뿐(외부 의존) · dated W1~W3 실행가능 항목 전부 `[v]` ·
    다음 pending = W4 omen 핸드오프(외부 의존) → hold. 비파괴 감사: 마커 3자 8/11 값과 바이트 일치
    (target=`data/episodes_s1`·trained_on=`episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·
    학습 프로세스 없음·`rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8~8/11 대비
    불변·datasets s1 100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-12_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-13 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. W2 dated 범위(8/12~8/18) 안, 잔여 W2 = omen
    lerobot 로드 스모크 1건뿐(외부 의존) · dated W1~W3 실행가능 항목 전부 `[v]` · 다음 pending =
    W4 omen 핸드오프(외부 의존) → hold. 비파괴 감사: 마커 3자 8/12 값과 바이트 일치(target=
    `data/episodes_s1`·trained_on=`episodes_s1:1785931493`·measured=`episodes_s1:1786060554`)·
    학습 프로세스 없음·`rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8~8/12 대비
    불변·datasets s1 100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-13_phase3-w3-s1-hold-integrity-audit.md`.
  - 🔄 **2026-08-14 — hold 유지 + 무결성 감사 재확인**: 드라이버 STAGE=완료/유지(`episodes_s1`
    100ep·0.925, 새 사이클 미트리거) → 재실행 없음. W2 dated 범위(8/12~8/18) 안, 잔여 W2 = omen
    lerobot 로드 스모크 1건뿐(외부 의존) · dated W1~W3 실행가능 항목 전부 `[v]` · 다음 pending =
    W4 omen 핸드오프(외부 의존) → hold. 비파괴 감사: 마커 3자 8/13 값과 바이트 일치(target=
    `data/episodes_s1`·trained_on=`episodes_s1:1785931493`·measured=`episodes_s1:1786060554`, `.next` 없음)·
    학습 프로세스 없음·`rollout_summary_s1.json` md5 `fbeef25775e5846ba2e3ce887afd1929` 8/8~8/13 대비
    불변·datasets s1 100ep/7231f·floor·cl 각 50ep/3350f 불변 → **회귀/오염 0**. [자가치유] 없음. 상세:
    `2026-08-14_phase3-w3-s1-hold-integrity-audit.md`.
- W4 (8/26 ~ 8/31): sim2real 핸드오프
  - [ ] 합성 데이터셋 + sim-trained 정책 omen 전달 (실기 담당자 협업 — 실기 fine-tune 대조군)
  - [ ] P1 LED ROI 캘리브 지원 — 시뮬 top/closeup 프레임으로 ROI·임계값 검증 결과 공유
  - [ ] Sim2Real 격차 보고 (sim 성공률 vs 실기 롤아웃)

**완료 기준**: 시뮬 버튼누르기 성공률 70% (LED 자동 판정) + 합성 데이터셋 omen 로드 확인

---

## Phase 4 — RS232 HHT 케이블 분리 + 1차 기능 완성 (2026-09, 4주, 작업 완료 시점)

> ⚠️ 옛 Phase 4(RS232) + 옛 Phase 5(1차 기능 완성) 통합. 9월 말 = 24주 작업 완료.

- W1: RS232 커넥터 mesh 모델링, 케이블 분리(꽂힌 케이블 빼기) 시뮬 데이터 합성
- W2: DR 강화 + 학습, 실기 검증
- W3: 최종 모델 선정 (ACT vs DP), 1차 통합 모델 미세조정
- W4: 실기 검증 (PCB + RS232 통합), 실패 케이스 분석, 10월 시연 시나리오 확정

**완료 기준**: 시뮬 분리 부분성공 50% + PCB 70% / RS232 부분성공 40% (보고서 목표값)

---

## 10월 — 시연 + 사내 발표 (phase 외부)

> Phase 작업은 9월에 완료. 10월은 시연 + 사내 성과 발표만.

- W1: 최종 시연 모델 락(lock) + 시연 환경 준비
- W2: 1차 통합 리허설 (PCB)
- W3: 2차 통합 리허설 (PCB + RS232)
- W4: 사내 발표 + 차년도 과제 정리

**시연 일자**: 2026-10-31 (월말, 추후 확정)

---

## 월별 보고용 트랙과의 매핑

> 보고용 월별 계획서는 `docs/01_overview/`에 별도 보존.
> 매월 말 `agent/report-evidence/2026-MM/INDEX.md`에서 보고서 섹션별 증거 후보 정리.

| 보고서 월 | 보고서 항목 | 실제 트랙 매핑 |
|---|---|---|
| 4월 | Kick-off, 하드웨어 발주 | 사전학습 / Kick-off (phase 외부) |
| 5월 | 하드웨어 조립, 환경 구축 | Phase 0 W1-4 (시뮬 환경) |
| 6월 | 텔레오퍼레이션 검증 | Phase 1 W1-4 (시뮬 사전학습) |
| 7월 | 데이터 50 에피소드 | Phase 2 (Sim2Real) — 실기 50 ep만 보고 |
| 8월 | ACT 학습 | Phase 3 (PCB) — ACT 학습 부분만 보고 |
| 9월 | DP 비교, 기능 완성 | Phase 4 (RS232 + 1차 기능 완성) |
| 10월 | 시연 | phase 외부 — 통합 시연 + 사내 발표 |

---

## 변경 이력
- 2026-05-01: 최초 작성. Isaac Lab → MuJoCo 변경. Phase 0~5 정의.
- 2026-06-11: 작업 9월 종료 일정으로 단축. Phase 0~4 (5개) 구조. 옛 Phase 5(10월 1차완성) → Phase 4(9월) 통합. 10월 = phase 외부 시연.
- 2026-08-05: 7/2~7/22 성과를 체크 항목으로 승격(파서 버그 수정과 함께). **Phase 3 재정의** — "PCB 조정" → "S1 리셋버튼 시뮬 (실기 정렬)". 실기 트랙(deois/soarm_lerobot, omen)과 작업·관측 스키마 정렬. Phase 2 잔여 2건: zero-shot 실기 = Phase 3 W4 이관(Orin SSH → omen 협업 전제 갱신), full-epoch 공정비교 = 보류.
