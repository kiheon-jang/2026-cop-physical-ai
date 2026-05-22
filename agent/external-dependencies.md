# 외부 의존 / 사용자 수동 작업 누적 파일

> Mac Mini Hermes 에이전트가 단독으로 처리할 수 없는 항목.
> 실기 옆 작업자, 다른 머신, 또는 사용자(장기헌)의 수동 처리가 필요한 항목을 누적합니다.
> 매일 07:00 보고 메일 [4-A] 섹션은 이 파일에서 자동 추출됩니다.

## 사용 규칙

- 항목 추가 시 형식:
  - `[ ]` 또는 `[v]` 체크박스
  - `[담당]` 태그: `[실기 담당]`, `[전체]`, `[장기헌]`, `[CoP 위원회]` 등
  - 마감일
  - 사유/방법 (선택)
- 완료 시 `[v]`로 체크하고 완료일 기록
- 7일 지난 완료 항목은 하단 **완료 이력**으로 이동

---

## 🔴 진행중 (메일에 매일 포함)

### 우선순위 1 — Phase 0 차단 항목

- [v] [장기헌] **SO-ARM100 로컬 커밋 완료** — 2026-05-15
  - `Simulation/SO101/so101_new_calib.xml` 로컬 커밋 완료 (오버헤드 카메라 추가 + 관절 range 시뮬용 조정)
  - 원본 TheRobotStudio 레포에는 push 안 함 (시뮬 전용 수정이므로 upstream 부적합)

- [v] [전체] **MuJoCo 사내 사용 라이선스 확인** — 2026-05-22 결정
  - CoP 단계 내부 연구개발 용도로 사용 승인 (Apache 2.0, 상업 배포 아님)
  - 결과: research/decisions/README.md 결정 완료 항목으로 이동

---

### 🟡 옵션 항목 — 있으면 정확도 향상, 없어도 시뮬 진행 가능

> 이 항목들이 없어도 크론 에이전트는 시뮬 작업을 계속 진행한다.
> 제공되면 해당 파라미터를 MJCF/config에 반영하여 Sim2Real 정확도를 높인다.

- [ ] [실기 담당] **웹캠 사양 + 캘리브레이션값 제공** *(옵션 — Phase 2 Sim2Real 전까지)*
  - 없을 경우: 시뮬 가상 카메라 기본값 사용 (pos='0 0 1', fovy=45, 해상도 640x480)
  - 제공 시 반영 위치: `docs/02_hardware/camera-spec.yaml` → MJCF `<camera>` 파라미터 업데이트
  - 필요 정보: 모델명, 해상도, 수평 FOV, 오버헤드/그리퍼 카메라 위치(X,Y,Z,cm)

- [ ] [실기 담당] **SO-ARM101 실측 무게 + 관절 마찰계수** *(옵션 — Phase 2 Sim2Real 전까지)*
  - 없을 경우: MJCF 기존 inertial 값 사용 (TheRobotStudio 기본값)
  - 제공 시 반영 위치: `docs/02_hardware/physical-spec.yaml` → MJCF `<inertial>` + `<joint frictionloss>` 업데이트
  - 필요 정보: 각 링크별 무게(g), 그리퍼 무게(g), 관절 정지 마찰력

### 우선순위 2 — 의사결정 대기

- [ ] [실기 담당] **Phase 1 W4 실기 에피소드 수집 + Orin Nano 접근 계획**
  - 마감: 2026-06-22 (Phase 1 W4 시작일)
  - 사유: Phase 1 W4 "실기 5~10 에피소드로 fine-tune" — Hermes 크론 단독 처리 불가
  - 필요 항목:
    1. SO-ARM101 실기 로봇 연결된 머신에서 LeRobot 텔레오퍼레이션 5~10 에피소드 수집
    2. 에피소드를 LeRobot Dataset 포맷으로 저장 후 GitHub push
    3. Orin Nano (추론 머신) SSH 접속 정보 또는 로컬 실행 방법 확인
  - 이 항목이 없으면 Phase 1 W4 fine-tune은 시뮬 only로 대체

- [ ] [CoP 위원회] **Phase 3/4 차년도 추진 여부 결정**
  - 마감: 2026-09-30
  - 사유: 10월 시연 후 차년도 과제 도출 시 필요
  - Phase 3: Isaac Sim 강화학습 (NVIDIA GPU 필요 → 별도 서버 도입 검토)
  - Phase 4: LeKiwi/XLeRobot 모바일 매니퓰레이터

### 우선순위 3 — 정보성 (의사결정 무관, 참고용)

- - [v] OpenClaw → Hermes Agent 마이그레이션 (2026-04-29)
- [v] fcc-proxy 배제, NVIDIA NIM 직결 라우팅 (2026-04-29)

---

## ✅ 완료 이력

### 2026-05

- [v] **환경 설정 오류 해결 (Claude Code CLI / MuJoCo)** — 2026-05-15
  - `claude -p` 인증 정상 복구 확인
  - `mjpython` 대신 `.venv/bin/python3 + mujoco.Renderer` 방식으로 전환 확인 (3.8.0 정상 동작)
  - W2 5/12 (mujoco.Renderer 검증) 진행 가능 상태

### 2026-04


---

## 메모

- 이 파일은 Hermes 에이전트가 매일 자동 갱신
- 사용자가 수동으로 추가한 항목도 동일 형식으로 적으면 다음 메일에 반영됨
- 항목 완료 시 사용자가 `[ ]` → `[v]` 변경 후 commit하면 다음 메일에서 자동 제외
