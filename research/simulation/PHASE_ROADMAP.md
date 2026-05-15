# 시뮬 환경 단계별 로드맵 (Phase 0 ~ 5)

> **최초 작성**: 2026-05-01
> **시뮬레이터**: MuJoCo 3.x (확정 — research/decisions/2026-04-22_simulator-selection.md 참조)
> **운영**: Hermes Agent가 매일 23:00에 이 파일을 읽고 오늘 진행할 단계를 식별합니다.
> 단계 완료 시 `[v]` 체크하고 다음 단계로 진행.

## 환경 사양
- **머신**: Mac Mini M5 16GB (Apple Silicon ARM64)
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
- [ ] **5/4**: Joint limits 적용 (STS3215 사양: 360° 회전, 1.5Nm 토크)
- [ ] **5/5**: 그리퍼 추가 + 그리퍼 동작 확인
- [ ] **5/6**: 단순 동작 시연 스크립트 (`samples/training/sim_basic_motion.py`)
- [ ] **5/7**: W1 정리 + W2 카메라 셋업 준비

### W2 (5/8 ~ 5/14) — 카메라 시뮬 셋업
- [ ] 외부 의존: 웹캠 캘리브레이션값 수신 (실기 담당, 마감 5/14)
- [ ] **5/8~9**: 오버헤드 카메라 시뮬 추가 (`<camera mode="fixed">`)
- [ ] **5/10~11**: 그리퍼 카메라 시뮬 추가 (그리퍼 body 자식)
- [ ] **5/12**: `mujoco.Renderer`로 RGB 이미지 추출 검증 ✅ 차단 해제 (2026-05-15: .venv/bin/python3 + mujoco.Renderer 정상 확인)
- [ ] **5/13**: 카메라 캘리브레이션 파라미터 적용 (FOV, 해상도) — 웹캠 스펙 수신 후 진행
- [ ] **5/14**: 두 카메라 동시 캡처 + 동기화 검증 — 웹캠 스펙 수신 후 진행

### W3 (5/15 ~ 5/21) — 실기 ↔ 시뮬 매핑 검증
- [ ] 외부 의존: SO-ARM101 실측 무게/마찰 수신 (실기 담당, 마감 5/21)
- [ ] **5/15**: 시뮬 관절 한계 vs 실기 캘리브레이션 비교
- [ ] **5/16**: 시뮬 무게/관성 조정 (실측값 반영)
- [ ] **5/17~18**: 동일 명령에 대한 시뮬 vs 실기 관절각 비교 (목표 ±1°)
- [ ] **5/19**: 마찰계수 튜닝
- [ ] **5/20**: 매핑 정확도 리포트 작성
- [ ] **5/21**: W3 마무리 + Phase 0 W4 시작 준비

### W4 (5/22 ~ 5/31) — Pick-and-Place 시뮬 + 자동 데이터셋
- [ ] **5/22~24**: Pick-Place 시나리오 (큐브 1개) 시뮬 동작
- [ ] **5/25~27**: 자동 데이터 수집 스크립트 (`samples/training/sim_data_collector.py`)
- [ ] **5/28~30**: LeRobot Dataset 포맷으로 50 에피소드 합성
- [ ] **5/31**: Phase 0 완료 리포트 + 6월 Phase 1 준비

**Phase 0 완료 기준**:
- ✅ MuJoCo에서 SO-ARM101이 viewer로 동작
- ✅ 카메라 2대 RGB 이미지 합성 가능
- ✅ 시뮬-실기 관절각 오차 ±1° 이내
- ✅ Pick-Place 50 시뮬 에피소드 자동 생성

---

## Phase 1 — 사전학습 (2026-06, 4주)

### W1-2 (6/1 ~ 6/14) — 데이터 합성
- [ ] 시뮬에서 200 에피소드 자동 생성 (다양한 시작 위치)
- [ ] LeRobot Dataset 포맷 검증

### W3 (6/15 ~ 6/21) — ACT 학습
- [ ] LeRobot ACT 학습 파이프라인 구성
- [ ] epoch 100 학습 실행
- [ ] 학습 곡선 모니터링

### W4 (6/22 ~ 6/30) — 실기 fine-tune (예정)
- [ ] 학습 모델 git push → Orin Nano
- [ ] 실기 5~10 에피소드로 fine-tune (실기팀)
- [ ] 시뮬 vs 실기 정확도 비교

**Phase 1 완료 기준**: 시뮬 Pick 성공률 90% 이상

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

## Phase 4 — RS232 HHT 결선 (2026-09, 4주)

- W1: RS232 커넥터 mesh + 핀 정밀 모델링 (±0.5mm)
- W2: 정밀 삽입 시뮬 데이터 합성 (300 에피소드)
- W3: DR 강화 + 학습
- W4: 실기 검증 + 실패 케이스 분석

**완료 기준**: 시뮬 결선 부분성공 50%

---

## Phase 5 — 통합 시연 (2026-10, 4주)

- W1: 최종 데이터 추가 + 모델 미세조정
- W2: 1차 통합 리허설 (PCB)
- W3: 2차 통합 리허설 (PCB + RS232)
- W4: 사내 발표 + 차년도 과제 정리

**완료 기준**: PCB 70% / RS232 부분성공 40% (보고서 목표값)

---

## 월별 보고용 트랙과의 매핑

> 보고용 월별 계획서는 `docs/01_overview/`에 별도 보존.
> 매월 말 `agent/report-evidence/2026-MM/INDEX.md`에서 보고서 섹션별 증거 후보 정리.

| 보고서 월 | 보고서 항목 | 실제 트랙 매핑 |
|---|---|---|
| 5월 | 하드웨어 조립, 환경 구축 | Phase 0 W1-4 (시뮬 환경) |
| 6월 | 텔레오퍼레이션 검증 | Phase 1 W1-4 (시뮬 사전학습) |
| 7월 | 데이터 50 에피소드 | Phase 2 (Sim2Real) — 실기 50 ep만 보고 |
| 8월 | ACT 학습 | Phase 3 (PCB) — ACT 학습 부분만 보고 |
| 9월 | DP 비교 | Phase 4 (RS232) — DP 비교 부분만 보고 |
| 10월 | 시연 | Phase 5 (통합 시연) |

---

## 변경 이력
- 2026-05-01: 최초 작성. Isaac Lab → MuJoCo 변경. Phase 0~5 정의.
