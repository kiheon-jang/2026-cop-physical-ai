# 🤖 AI Agent 운영 가이드 (AGENT_PROCESS.md)

> 이 문서는 어떤 AI 툴에서도 이 레포를 이어받아 작업할 수 있도록  
> 현재 자동화 구조, 크론 스케줄, 작업 프로세스를 완전히 기술합니다.  
> **요구사항이 변경되면 이 문서를 반드시 업데이트하세요.**

---

## 📦 상세 인수인계 패키지 → [`agent/`](./agent/)

이 파일은 요약본입니다. 완전한 인수인계를 위한 상세 문서는 `agent/` 폴더에 있습니다.

| 파일 | 내용 |
|------|------|
| [agent/HANDOVER.md](./agent/HANDOVER.md) | **메인 인덱스** — 새 에이전트가 가장 먼저 읽는 파일 |
| [agent/env.md](./agent/env.md) | VM / GitHub / 이메일 / 하드웨어 환경 전체 |
| [agent/cron-jobs.md](./agent/cron-jobs.md) | 크론 5개 페이로드 완전 서술 (재등록용) |
| [agent/skills/README.md](./agent/skills/README.md) | 사용 스킬 목록 및 사용 패턴 |
| [agent/templates/README.md](./agent/templates/README.md) | 메일/결정폼 템플릿 경로 안내 |

---

## 📌 프로젝트 컨텍스트

| 항목 | 내용 |
|------|------|
| **프로젝트명** | 사내 CoP Physical AI — 첫걸음 |
| **목적** | SO-ARM101 로봇팔 기반 모방학습 → 강화학습 → 모바일 매니퓰레이터 |
| **현재 단계** | Phase 1 완료 (조립/환경/텔레오퍼레이션), Phase 2 진입 직전 (데이터 수집) |
| **GitHub** | https://github.com/kiheon-jang/2026-cop-physical-ai |
| **담당자** | 장기헌 (xaqwer@gmail.com) |
| **보고 수신자** | insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com |

---

## 🏗️ 레포지토리 구조

```
2026-cop-physical-ai/
│
├── AGENT_PROCESS.md        ← 이 파일 (AI 운영 가이드)
├── CONTRIBUTING.md         ← 품질 기준
├── README.md               ← 프로젝트 개요
│
├── docs/                   ← 단계별 실습 문서
│   ├── 01_overview/        프로젝트 개요, 전략 보고서
│   ├── 02_hardware/        BOM, 조립 가이드
│   ├── 03_software-setup/  LeRobot 환경 설치
│   ├── 04_teleoperation/   Follower/Leader/카메라 (✅ 완료)
│   ├── 05_data-collection/ 데이터 수집 가이드 + TRACKING.md
│   ├── 06_imitation-learning/ ACT/Diffusion Policy 학습
│   ├── 07_simulation-rl/   Isaac Sim 강화학습 (예정)
│   └── 08_expansion/       LeKiwi/XLeRobot 확장 (예정)
│
├── research/
│   ├── drafts/             ← 자동 생성 초안 (매일 밤 크론)
│   ├── latest-tech/        ← 검수 완료 확정본 (주간 정리 후 이동)
│   ├── decisions/          ← 채택/기각 결정 로그
│   ├── benchmarks/         ← 성능 벤치마크
│   └── CHANGELOG.md        ← 리서치 갱신 이력
│
├── samples/
│   ├── unit/               ← 하드웨어 없이 실행 가능
│   ├── hardware/           ← 실제 로봇 연결 후 실행
│   ├── training/           ← 학습 파이프라인
│   ├── inference/          ← 인퍼런스
│   └── SAMPLE_STATUS.md    ← 전체 샘플 완성도 현황판
│
├── assets/
│   └── images/
│
└── archive/                ← 원본 Obsidian 노트 보존
```

---

## ⚙️ 자동화 크론 스케줄

> **플랫폼**: **Hermes Agent** (로컬 Mac Mini 24/7, Gemini 2.5 Flash 무료 백엔드)  
> **상태**: 2026-04-29 OpenClaw → Hermes 마이그레이션 완료 ✅  
> **시간 기준**: KST (Asia/Seoul)

| 크론 ID | 이름 | 스케줄 | 역할 |
|---------|------|--------|------|
| `9ad85007cf27` | 시뮬 환경 단계별 구축 | 매일 23:00 KST | `research/simulation/`에 Phase별 환경 구축 (MuJoCo) |
| `85d322d3b37c` | 시뮬 테스트 + 메트릭 수집 | 매일 23:30 KST | `agent/research-log/`에 테스트 결과 기록 (성공률, 추론시간 등) |
| `fb6d7cb26650` | 아침 보고 메일 | 매일 07:00 KST | 매거진 형식 보고 메일 3명 발송 (외부 의존 항목 포함) |
| `0b1d4a7b2bf7` | 주간 정리 + 보고용 증거 식별 | 매주 일요일 22:00 KST | `agent/report-evidence/2026-MM/INDEX.md` 갱신 |

---

## 🎯 실제 연구 트랙 (선행) — 2026-05-01 변경

> **보고용 트랙(월별 계획서)** 과 **실제 연구 트랙(시뮬 선행)** 을 분리합니다.
> 보고용은 매월 보고 기준에 맞춰 증거만 추출, 실제 연구는 빠르게 선행 진행.

### 시뮬레이터 결정 (2026-05-01)

| 항목 | 결정 |
|------|------|
| 시뮬레이터 | **MuJoCo 3.x** (Apple Silicon 네이티브) |
| 변경 사유 | Isaac Lab/Sim은 NVIDIA GPU 필수 → Mac M5 미지원 |
| 모델 | TheRobotStudio SO-ARM100/101 MJCF 공식 모델 |
| 학습 환경 | Mac Mini M5 16GB (단독으로 시뮬+학습+메트릭 처리 가능) |
| 실기 검증 | 학습 모델 git push → Orin Nano에서 실기 추론 (별도) |

### Phase 로드맵 (5월~10월)

| Phase | 기간 | 핵심 산출물 |
|-------|------|------------|
| **Phase 0** 시뮬 환경 셋업 | 5월 (4주) | MJCF + 카메라 2대 + 관절 검증 |
| **Phase 1** 사전학습 | 6월 (4주) | 시뮬 200 ep + ACT 학습 + 실기 fine-tune |
| **Phase 2** Sim2Real 검증 | 7월 (4주) | DR 적용 + ACT/DP 비교 |
| **Phase 3** PCB 조정 | 8월 (4주) | PCB MJCF + 학습 + 시뮬 검증 |
| **Phase 4** RS232 결선 | 9월 (4주) | 정밀 삽입 (±0.5mm) |
| **Phase 5** 통합 시연 | 10월 (4주) | 사내 발표 + 영상 |

상세 내역: `research/simulation/PHASE_ROADMAP.md`

---

## 🔄 작업 프로세스 상세 (2026-05-01 재정의)

### 1. 시뮬 환경 단계별 구축 (매일 23:00)
```
1. agent/research-log/{어제 날짜}.md 확인 → 진척 상태 파악
2. research/simulation/PHASE_ROADMAP.md 확인 → 오늘 단계 식별
3. 오늘 단계 작업 수행:
   - MuJoCo 환경 구축 / MJCF 수정 / 시뮬 코드 작성
   - 결과물을 research/simulation/<단계명>.md 에 기록
4. 동시에 ~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/2026-MM/ 에 복사
5. git commit -m "🛠 [시뮬] <단계명> — YYYY-MM-DD"
6. git push
```
**5월 W1 단계 예시:**
- 5/1: MuJoCo 설치 + Apple Silicon 호환성 검증
- 5/2: SO-ARM100 MJCF 다운로드 + viewer 동작 확인
- 5/3: 6-DoF 관절 동작 + joint limit 적용
- 5/4~5: 그리퍼 추가 + 단순 동작 시연
- 5/6~7: 5월 W1 정리 + W2 카메라 셋업 준비

### 2. 시뮬 테스트 + 메트릭 수집 (매일 23:30)
```
1. 오늘 23:00에 구축한 환경 실행 테스트
2. 메트릭 측정:
   - 시뮬 동작 성공률
   - 추론 속도 (ms)
   - 시뮬-실기 관절각 오차 (Phase 1+ 부터)
   - 학습 손실 (학습 시작 이후)
3. agent/research-log/YYYY-MM-DD.md 작성 (메트릭 + 관찰 + 다음 단계)
4. 새로운 외부 의존 항목 발견 시 agent/external-dependencies.md 추가
5. git commit -m "📊 [로그] YYYY-MM-DD 시뮬 테스트 — <한줄 요약>"
6. git push
```

### 3. 아침 보고 메일 (매일 07:00)
```
1. GitHub 최신 커밋 이력 확인
2. agent/research-log/{어제 날짜}.md 읽기
3. research/simulation/ 신규 파일 확인
4. agent/external-dependencies.md 의 [ ] 미완료 항목 추출 → [4-A] 섹션
5. agent/report-evidence/2026-MM/INDEX.md 확인 → 보고용 증거 후보
6. docs/01_overview/mail-template.md 형식대로 메일 작성
7. 3명에게 발송: xaqwer@gmail.com, insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com
```
**핵심 변경**: [4-A] 외부 의존 섹션 추가 — 사용자 수동 작업 항목을 매일 노출.

### 4. 주간 정리 + 보고용 증거 식별 (매주 일요일 22:00)
```
1. agent/research-log/ 일주일치 파일 모아서 진행률 종합
2. research/simulation/ 단계 진행 상태 업데이트
3. agent/report-evidence/2026-MM/INDEX.md 갱신:
   - 이번 주 결과 중 보고서에 인용 가능한 메트릭/스크린샷 식별
   - 해당 월 보고서의 어느 섹션과 매핑되는지 표시
4. agent/external-dependencies.md 정리:
   - 7일 지난 완료 항목을 "완료 이력"으로 이동
   - 새 외부 의존 항목 추가
5. SAMPLE_STATUS.md 전체 업데이트
6. git commit -m "🔄 [주간정리] YYYY-MM-DD W주차 — 보고용 증거 X건"
7. push
```

---

## 🔧 Git 인증 방법

이 레포는 GitHub CLI(`gh`)로 인증합니다.

```bash
# push 전 항상 실행
git remote set-url origin https://$(gh auth token)@github.com/kiheon-jang/2026-cop-physical-ai.git

# 또는
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
```

---

## 📋 현재 미완료 / 진행 중 작업

| 상태 | 항목 | 담당 |
|------|------|------|
| 🔄 진행중 | **Phase 0**: 시뮬 환경 셋업 (5월) — MuJoCo + SO-ARM101 MJCF | Hermes Agent |
| ⏳ 대기 | MuJoCo 사내 라이선스 확인 (마감 5/3) | 전체 |
| ⏳ 대기 | 웹캠 캘리브레이션값 측정 (마감 5/14) | 실기 담당 |
| ⏳ 대기 | SO-ARM101 실측 무게/마찰 측정 (마감 5/21) | 실기 담당 |
| ⏳ 대기 | LeKiwi vs XLeRobot 결정 | Phase 4 (차년도) |

**상세**: [`agent/external-dependencies.md`](./agent/external-dependencies.md)

---

## 🆕 변경 이력

| 날짜 | 변경 내용 | 변경자 |
|------|-----------|--------|
| 2026-05-01 | **시뮬레이터 결정 변경**: Isaac Lab → MuJoCo 3.x (Mac M5 호환). 보고용/실제 연구 트랙 분리. Phase 0~5 로드맵 (5~10월). 4개 크론 prompt 전부 재작성 (시뮬 단계별). 메일 [4-A] 외부 의존 섹션 신설. | Hermes Agent (Mac M5) |
| 2026-04-29 | **OpenClaw → Hermes Agent 마이그레이션 완료**. 로컬 Mac (24/7) + Gemini Flash 무료로 전환. 4개 cron 정상 가동 확인. fcc-proxy 배제. | Claude Code (Mac M5) |
| 2026-04-21 | 최초 작성. 레포 구조화, 크론 3종 + 주간검수 설정 | AI Agent (OpenClaw) |
| 2026-04-21 | 리서치 drafts/latest-tech 2단계 구조 추가 | AI Agent (OpenClaw) |
| 2026-04-21 | SAMPLE_STATUS.md, CONTRIBUTING.md, AGENT_PROCESS.md 추가 | AI Agent (OpenClaw) |
| 2026-04-21 | 메일 템플릿 전면 개편 — ASCII 특수문자 제거, plain text 메거진 형식으로 통일. 코드 리뷰 포인트, 경로 변경사항 섹션 추가. 템플릿 파일: docs/01_overview/mail-template.md | AI Agent (OpenClaw) |

---

## 💬 다른 AI 툴에서 이어받을 때

1. 이 파일(`AGENT_PROCESS.md`) 먼저 읽기
2. `CONTRIBUTING.md` 품질 기준 숙지
3. `samples/SAMPLE_STATUS.md` 로 현재 샘플 완성도 파악
4. `research/decisions/README.md` 로 미결 결정 사항 파악
5. `docs/05_data-collection/TRACKING.md` 로 진행률 확인
6. GitHub 최신 커밋 이력으로 마지막 작업 확인
7. **크론 스케줄은 Hermes Agent (로컬)에서 자동 관리됨** — `hermes cron list`로 확인 가능
