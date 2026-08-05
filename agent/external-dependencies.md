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

- [v] [장기헌] **Orin Nano SSH 접속 정보 제공** — 2026-08-05 전제 무효로 해소
  - 실기 트랙이 omen(실기 담당자, deois/soarm_lerobot)에서 진행되어 실기 추론 경로가
    Orin SSH → omen 협업으로 바뀜. Orin 온디바이스 배포는 10월 시연 항목으로 보류.
  - (원 요구: 마감 6/22, IP/유저명/네트워크 — 44일 미수신 상태였음)

- [ ] [CoP 위원회] **Phase 3/4 차년도 추진 여부 결정**
  - 마감: 2026-09-30
  - 사유: 10월 시연 후 차년도 과제 도출 시 필요
  - Phase 3: Isaac Sim 강화학습 (NVIDIA GPU 필요 → 별도 서버 도입 검토)
  - Phase 4: LeKiwi/XLeRobot 모바일 매니퓰레이터

### 우선순위 3 — 정보성 (의사결정 무관, 참고용)

- - [v] OpenClaw → Hermes Agent 마이그레이션 (2026-04-29)
- [v] fcc-proxy 배제, NVIDIA NIM 직결 라우팅 (2026-04-29)

- [ ] [장기헌] **Claude Code v3.2 harness 권한 allowlist 점검** *(블로커 — 2026-06-07/08 nightly 연속 누적)*
  - 증상: `.venv/bin/python3 ...` (심볼릭 링크 대상이 working dir 밖) / `git add`·`commit`·`push` (mutation) / `cp ... 00_AI_Wiki/...` (working dir 밖 쓰기) 모두 Bash sandbox 권한으로 차단됨.
  - 영향: 23:00/23:30 nightly cron 이 (a) 시뮬 런타임 메트릭 수집 불가, (b) 산출물 git push 불가, (c) Obsidian 미러 불가. 워킹트리에 미커밋 산출물 누적 (2026-06-07, 2026-06-08 분).
  - 필요 조치: settings.json hooks/permissions 에서 `.venv/bin/python3` 절대경로 + `git add|commit|push` + `cp ... 00_AI_Wiki/CoP_PhysicalAI/...` 를 명시적 allow 또는 working-dir 확장.
  - 임시 우회: 사용자 수동 `git add -A && git commit -m "..." && git push` 1회 + Obsidian 폴더 수동 sync.
  - **2026-07-19 추가 — floor 재학습 04:04 killer 규명용 진단권한**: floor ACT 재학습이 12-run 연속
    **고정 벽시계 ~04:04 외부 SIGKILL**로 죽음(RSS·mps_mem·FD 전부 평탄, epoch↔벽시계 교락 해제로 확정 —
    상세 `research/simulation/2026-07-19_floor-retrain-timelinked-sigkill-confirmed.md`). 야간 자가치유로
    `COP_EPOCHS=42`(창 안 완주)로 우회했으나 **full-epoch(100) 공정비교 복원엔 04:04 killer 규명·제거 필요**.
    → `log show --predicate 'eventMessage contains "kill"'` / `launchctl list` / `ps` 권한 필요(macOS 주기
    유지보수·백업·스케줄 프로세스 후보). 현재 sandbox 차단.
    - **✅ 2026-08-05 규명 완료 — 범인 = `ai.hermes.autoupdate`(launchd, 매일 04:00)**:
      업데이트 시도(요즘 매일 실패→롤백) 후 gateway 를 kickstart 재시작하면서 **gateway
      프로세스 그룹 전체 SIGKILL**. 야간 크론(gateway 자식)이 nohup 으로 띄운 학습이 같은
      그룹이라 동반 사살(nohup 은 SIGHUP 만 무시). 증거: 백업 zip `pre-update-*-0400xx`,
      gateway.log 04:03:52 재시작(8/5), 사망 시각 ~04:04 일치. **수정**: `start_act_train.sh`
      가 학습을 `start_new_session`(새 세션 = 새 프로세스 그룹)으로 분리 — kickstart 가
      gateway 그룹을 죽여도 학습 생존. 확증 실험 = 8/5 밤 S1 학습(30ep, 04:04 관통) 진행 중.

---

## ✅ 완료 이력

### 2026-05

- [v] **환경 설정 오류 해결 (Claude Code CLI / MuJoCo)** — 2026-05-15
  - `claude -p` 인증 정상 복구 확인
  - `mjpython` 대신 `.venv/bin/python3 + mujoco.Renderer` 방식으로 전환 확인 (3.8.0 정상 동작)
  - W2 5/12 (mujoco.Renderer 검증) 진행 가능 상태
- [v] [장기헌] **SO-ARM100 로컬 커밋 완료** — 2026-05-15
  - `Simulation/SO101/so101_new_calib.xml` 로컬 커밋 완료 (오버헤드 카메라 추가 + 관절 range 시뮬용 조정)
  - 원본 TheRobotStudio 레포에는 push 안 함 (시뮬 전용 수정이므로 upstream 부적합)
- [v] [전체] **MuJoCo 사내 사용 라이선스 확인** — 2026-05-22 결정
  - CoP 단계 내부 연구개발 용도로 사용 승인 (Apache 2.0, 상업 배포 아님)
  - 결과: research/decisions/README.md 결정 완료 항목으로 이동
- [v] [실기 담당] **Phase 1 W4 실기 에피소드 수집 → 시뮬 200 에피소드로 대체 확정** — 2026-05-22 결정
  - 실기팀 에피소드 없음 확정 → Phase 1 W4 fine-tune 시 시뮬 추가 200 에피소드로 대체
  - 크론이 자동으로 `sim_data_collector.py` 200 에피소드 추가 생성으로 처리
  - Orin Nano SSH 접속 정보는 별도 항목으로 분리 (아래 참조)

### 2026-04


---

## 메모

- 이 파일은 Hermes 에이전트가 매일 자동 갱신
- 사용자가 수동으로 추가한 항목도 동일 형식으로 적으면 다음 메일에 반영됨
- 항목 완료 시 사용자가 `[ ]` → `[v]` 변경 후 commit하면 다음 메일에서 자동 제외
