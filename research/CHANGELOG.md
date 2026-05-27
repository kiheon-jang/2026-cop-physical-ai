# 리서치 갱신 이력 (CHANGELOG.md)

> 리서치 파일의 생성, 검수 통과, 갱신, 삭제 이력을 추적합니다.

---

## 형식

```
### YYYY-MM-DD
- ✅ [확정] <파일명> — drafts/ → latest-tech/ 이동
- 🔄 [갱신] <파일명> — 내용 최신화
- 🗑️ [삭제] <파일명> — 이유
- 📋 [초안] <파일명> — drafts/ 생성
```

---

## 이력






### 2026-05-27
- 🛠 [시뮬] LeRobot Dataset 포맷으로 50 에피소드 합성 — 2026-05-28
- chore(self-heal): 자가치유 기록 추가 (research-log 2026-05-28 소급 작성)
- 📊 [로그] 2026-05-27 시뮬 테스트 — 데이터 수집 및 시뮬 스크립트 실행
- 🛠 [시뮬] 자동 데이터 수집 스크립트 실행 — 2026-05-27
- chore(submodule): Update SO-ARM100 submodule reference with cube additions

### 2026-05-25
- chore(self-heal): 자가치유 기록 추가
- 📝 [히스토리] 2026-05-24 작업 기록 + README 현황 업데이트 — 2026-05-25

### 2026-05-24
- chore(self-heal): 자가치유 기록 추가
- 🔄 [주간정리] 2026-05-24 W4 — 보고용 증거 4건

### 2026-05-23
- 📊 [로그] 2026-05-23 시뮬 테스트 — Pick-Place 시뮬 동작 및 로그 기록
- 🛠 [시뮬] Pick-Place 시나리오 (큐브 1개) 시뮬 동작 — 2026-05-23
- 📝 [히스토리] 2026-05-22 작업 기록 + README 현황 업데이트 — 2026-05-23

### 2026-05-22
- 🔧 [자동화] Hermes cron 4개 `--clear-skills` 처리 — terminal/file/web 오탐 경고 제거
- 🛠 [스킬] `cop-physical-ai-self-heal` 신설 — cron 자가진단+복구 프로토콜
- 📝 [보고] `generate_daily_report.py` — `research/CHANGELOG.md` + `README.md` 자동 업데이트 추가 (메일 발송 후 git push)
- 📋 [인수인계] 전체 문서 소급 업데이트 (CHANGELOG, AGENT_PROCESS, cron-jobs, decisions, HANDOVER)

### 2026-05-21
- 📋 [로그] 2026-05-19~21 research-log 소급 작성 (크론 실패 복구)
- ✅ [로드맵] W1~W3 완료 항목 `[v]` 체크 — 크론 혼선 방지

### 2026-05-19
- 🛠 [시뮬] W3 마찰계수 튜닝 — `samples/training/sim_friction_tuning.py` 작성, frictionloss 파라미터 동적 조정

### 2026-05-18
- 🛠 [시뮬] W3: 동일 명령 시뮬 vs 실기 관절각 비교 (시뮬 결과) — `W3_joint_angle_comparison_2026-05-18.md`

### 2026-05-17
- 🛠 [시뮬] W3: 관절 각도 비교 스크립트 준비 — `sim_joint_angle_comparison_script.py` 작성

### 2026-05-16
- 🛠 [시뮬] W3: 시뮬 무게/관성 조정 — MJCF inertial 값에 CAD 기본값 주석 추가, `sim_mass_inertia_adjustment_2026-05-16.md`

### 2026-05-15
- 🔧 [환경] Hermes Agent v0.10.0 → v0.13.0 업그레이드 (3481 커밋, 22개 신규 스킬)
- 🔧 [환경] Hermes gateway launchd plist 갱신 (`hermes gateway install`)
- 🔧 [환경] `generate_daily_report.py` 파싱 버그 3개 수정 (외부의존 `\n` 리터럴, 이슈/진척 헤더 패턴 멀티-폴백)
- 📝 [의존] SO-ARM100 로컬 커밋 완료 — `so101_new_calib.xml` (오버헤드 카메라 추가 + 관절 range 조정)
- 📋 [계획] 웹캠 캘리브레이션값 / SO-ARM101 실측값 → **옵션으로 재분류** (없어도 시뮬 진행 가능, 기본값 사용)

### 2026-05-14
- 🛠 [시뮬] W2 5/14: 카메라 동기화 검증 — 오버헤드+그리퍼 카메라 동시 캡처 검증

### 2026-05-12
- 🛠 [시뮬] W2 5/12: `mujoco.Renderer` RGB 이미지 추출 검증 (차단됐다가 5/15 해제)
- 🛠 [시뮬] W2: 오버헤드 카메라 셋업 보고서

### 2026-05-11
- 🛠 [시뮬] W2: 카메라 2대(오버헤드+그리퍼) 시뮬 셋업 및 RGB 이미지 추출 검증

### 2026-05-10
- 🛠 [시뮬] W2: Joint limits 재적용 (W1 이어서 — MJCF forcerange 조정)

### 2026-05-06
- 🛠 [시뮬] W1: 단순 동작 시연 스크립트 — sin파 패턴 6-DoF 관절 제어

### 2026-05-05
- 🛠 [시뮬] W1: 그리퍼 추가 + 단순 동작 시연 (`Claude CLI 인증 오류`로 claude -p 우회)

### 2026-05-04
- 🛠 [시뮬] W1: Joint limits 적용 — STS3215 사양 (360° / 1.5Nm)
- 📧 [메일] 일일 보고 시스템 시뮬 트랙으로 전면 재작성 (`generate_daily_report.py` v3)
- 📧 [메일] `오늘의 한 줄` 섹션 추가 (Gemini API 자동 생성, 비전공자 친화)
- 📧 [메일] 모바일 반응형 + `오늘의 결과물` 미디어 카드 섹션 추가
- 📧 [메일] 수신자 추가 — kimeun091473@gmail.com (총 4명)

### 2026-05-03
- 🛠 [시뮬] W1: 6-DoF 동작 확인 — viewer로 SO-ARM101 관절 동작 검증
- 📊 [로그] 2026-05-03 research-log 작성

### 2026-05-01
- 🛠 [의사결정] 시뮬레이터 최종 확정: **MuJoCo 3.x** (Phase 0~2 메인) + Isaac Lab (Phase 3+, 차년도 별도 GPU 서버)
  - 사유: Mac Mini M5 (Apple Silicon)에서 Isaac Lab 미지원
- 🤖 [구조] 자동화 플랫폼: OpenClaw → Hermes Agent (로컬 Mac Mini, 2026-04-29 마이그레이션 후 시뮬 트랙으로 재구성)
- 🔄 [구조] 크론 4개 prompt 전체 재작성 (요일별 주제 순환 폐기 → PHASE_ROADMAP.md 기반 단계별 점진 구축)
  - 신규 ID: 9ad85007cf27, 85d322d3b37c, fb6d7cb26650, 0b1d4a7b2bf7
  - 폐기 ID: dc257031, b2e623a4, dcbf84a5, ed5aff22, 20ee15d4
- 📁 [구조] 신규 폴더: research/simulation/, agent/research-log/, agent/report-evidence/, ~/Obsidian/00_AI_Wiki/CoP_PhysicalAI/
- 📋 [신설] research/simulation/PHASE_ROADMAP.md — Phase 0~5 단계별 로드맵 (5월~10월)
- 📋 [신설] research/simulation/00_kickoff.md — Phase 0 W1 킥오프
- 📋 [신설] agent/external-dependencies.md — 외부 의존 / 사용자 수동 작업 누적
- 📧 [개편] 메일 [4-A] 외부 의존 섹션 신설 (사용자 수동 작업 매일 노출)
- 🗂️ [구조] 보고용 트랙 ↔ 실제 연구 트랙 분리 (월별 계획서는 그대로 유지, 시뮬은 선행)

### 2026-04-29
- 🤖 [마이그레이션] OpenClaw → Hermes Agent (Mac Mini M5 24/7 로컬 운영) 완료
- 🔧 [정리] fcc-proxy 배제, NVIDIA NIM 직결 라우팅
- 📝 [업데이트] AGENT_PROCESS.md 플랫폼 표기 (OpenClaw → Hermes)

### 2026-04-22
- 📋 [초안] 2026-04-22_sim2real-gap-techniques.md — Sim2Real 격차 해소 최신 기법 (Digital Cousins, Sim2Real-VLA, RL Co-Training, PACE, lerobot-sim2real)

### 2026-04-21
- 📁 [구조] research/drafts/ 폴더 신설 (초안 보관용)
- 📁 [구조] research/latest-tech/ 확정본 전용으로 용도 명확화
- 📁 [구조] research/decisions/ 결정 로그 폴더 신설
- 📋 [초안] 리서치 자동화 시작 — 매일 23:00 크론으로 drafts/ 에 초안 생성 예정
- 📋 [초안] 2026-04-21_isaac-lab-sim-rl-trends.md — Isaac Lab/Isaac Sim 강화학습 최신 동향 (v2.3.x → 3.0, Isaac Sim 6.0 EAR)
