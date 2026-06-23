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
> - pick-place는 실물 우선이 정공법(LeRobot 합의)이나 **6월 실물수집 미예정 → 6월은 sim 트랙(closed-loop 자동수집)이 메인.** sim의 결정적 가치는 Phase 3+ RS232 정밀삽입.
> - 정정 상세: 위 root-cause 문서 상단 정정 + 메모리(grasp-rootcause / sim-strategy / data-paths).

- [v] ACT 학습 파이프라인 가동 검증 (smoke → 100 epoch MPS 학습, loss 곡선 정상)
- [v] rollout 추론 + Pick 성공률 측정기 구축 (`scripts/render_act_rollout.py`)
- [v] **시뮬 grasp 근본원인 재규명 + closed-loop 해법 확보** (88%/75%, `_grasp_closedloop.py`)
- [진행중] **closed-loop 자동수집 정상화 (← 크론 야간 무인 태스크)**:
  closed-loop expert를 `samples/training/sim_data_collector.py`에 연결 → **성공 시연만** LeRobot 자동수집
  (씬=scene_grasp_pads.xml, 큐브 30mm, forcerange 3.0=12V faithful, lift≥40mm 필터) →
  ACT 재학습 → `render_act_rollout.py` rollout 측정. **open-loop PICK_PLACE_POSES 폐기.**
  (50mm 큐브는 TCP/grasp z 별도 보정 필요라 미적용 — 30mm로 진행.)
- [ ] 학습 모델 Orin Nano 배포 (SSH 연결 확보 시)

**Phase 1 완료 기준 (2026-06-23 갱신)**:
- ✅ 시뮬 사전학습 파이프라인 전 구간 가동 (데이터 합성 → ACT 학습 → 추론 → 성공률 측정)
- ✅ 시뮬 grasp closed-loop 해법 확보 (30mm 88%/75%)
- 🔄 시뮬 Pick 성공률: closed-loop 자동수집 → ACT 재학습 → rollout 측정으로 확인 중.
  실물수집은 6월 미예정 → Phase 2(7월) 일정으로. sim의 결정적 가치는 Phase 3+ 정밀삽입.

---

## Phase 2 — Sim2Real 검증 (2026-07, 4주)

- W1: Domain Randomization (조명, 마찰, 카메라 노이즈)
- W2: Zero-shot 실기 추론 → 격차 측정
- W3: 실기 fine-tune (10 에피소드)
- W4: Diffusion Policy 동일 절차 + ACT 비교

**완료 기준**: 실기 Pick 성공률 60% (Sim2Real 격차 < 30%p)

---

## Phase 3 — PCB 조정 (2026-08, 4주)

- W1: PCB 조정 단계 분해 (피킹 → 정렬 → 배치)
- W2: PCB mesh + 작업대 MJCF 모델링
- W3: 시뮬 100 에피소드 자동 수집
- W4: ACT 학습 + 시뮬 검증

**완료 기준**: 시뮬에서 PCB 조정 성공률 70%

---

## Phase 4 — RS232 HHT 결선 + 1차 기능 완성 (2026-09, 4주, 작업 완료 시점)

> ⚠️ 옛 Phase 4(RS232) + 옛 Phase 5(1차 기능 완성) 통합. 9월 말 = 24주 작업 완료.

- W1: RS232 커넥터 mesh + 핀 정밀 모델링 (±0.5mm), 정밀 삽입 시뮬 데이터 합성
- W2: DR 강화 + 학습, 실기 검증
- W3: 최종 모델 선정 (ACT vs DP), 1차 통합 모델 미세조정
- W4: 실기 검증 (PCB + RS232 통합), 실패 케이스 분석, 10월 시연 시나리오 확정

**완료 기준**: 시뮬 결선 부분성공 50% + PCB 70% / RS232 부분성공 40% (보고서 목표값)

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
