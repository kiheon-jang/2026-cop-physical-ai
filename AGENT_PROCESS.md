# 🤖 AI Agent 운영 가이드 (AGENT_PROCESS.md)

> 이 문서는 어떤 AI 툴에서도 이 레포를 이어받아 작업할 수 있도록  
> 현재 자동화 구조, 크론 스케줄, 작업 프로세스를 완전히 기술합니다.  
> **요구사항이 변경되면 이 문서를 반드시 업데이트하세요.**

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

> **플랫폼**: OpenClaw (https://openclaw.ai)  
> **시간 기준**: KST (Asia/Seoul)

| 크론 ID | 이름 | 스케줄 | 역할 |
|---------|------|--------|------|
| `dc257031` | 일일 리서치 초안 (drafts) | 매일 23:00 KST | `research/drafts/`에 요일별 주제 초안 생성 |
| `b2e623a4` | 일일 샘플코드 | 매일 23:30 KST | `samples/`에 샘플 작성 + 실행 검증 + SAMPLE_STATUS 업데이트 |
| `dcbf84a5` | 아침 보고 메일 | 매일 07:00 KST | 매거진 형식 보고 메일 3명 발송 (검토대기 항목 포함) |
| `ed5aff22` | 주간 검수 + 최신화 | 매주 일요일 22:00 KST | drafts→latest-tech 이동, 오래된 리서치 갱신, SAMPLE_STATUS 전체 업데이트 |
| `20ee15d4` | Isaac Sim 사전 조사 | 2026-04-22 23:00 KST (1회) | `docs/07_simulation-rl/` + `research/decisions/` 채움 |

---

## 🔄 작업 프로세스 상세

### 1. 일일 리서치 초안 (매일 23:00)
```
1. gsk search 로 해당 요일 주제 검색 (2025~2026 최신)
2. research/drafts/YYYY-MM-DD_<주제>.md 작성
3. git commit -m "🔬 [draft] <주제> — YYYY-MM-DD"
4. git push
```
**요일별 주제 순환:**
- 월: ACT vs Diffusion Policy vs π0 벤치마크 비교
- 화: Isaac Lab / Isaac Sim 강화학습 최신 동향
- 수: Sim2Real 격차 해소 최신 기법
- 목: VLA(Vision-Language-Action) 모델 최신 논문
- 금: 모방학습 데이터 효율화 기법
- 토: LeRobot 커뮤니티 최신 업데이트
- 일: 경쟁사/유사 프로젝트 동향

### 2. 일일 샘플코드 (매일 23:30)
```
1. 요일별 주제에 맞는 샘플 코드 작성
2. 실제 실행하여 전체 PASS 확인
3. SAMPLE_STATUS.md 업데이트
4. git commit -m "💻 [샘플] <설명> — YYYY-MM-DD"
5. git push
```
**완성도 기준 (CONTRIBUTING.md 참조):**
- ⭐ 초안: 구조만 있음, 실행 안 됨
- ⭐⭐ 기본: 하드웨어 없이 실행됨, 일부 PASS
- ⭐⭐⭐ 완성: 전체 PASS, 주석 완비, 실사용 가능

### 3. 아침 보고 메일 (매일 07:00)
```
1. GitHub 최신 커밋 이력 확인
2. research/drafts/ 또는 latest-tech/ 신규 파일 요약
3. TRACKING.md 데이터 수집 현황 확인
4. decisions/README.md 검토 대기 항목 확인
5. 매거진 형식 메일 작성 (초심자 친화적 리서치 요약 포함)
6. 3명에게 발송: xaqwer@gmail.com, insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com
```

### 4. 주간 검수 + 최신화 (매주 일요일 22:00)
```
1. research/drafts/ 전체 파일 품질 검토
   - CONTRIBUTING.md 기준 통과 → latest-tech/ 로 이동
   - 기준 미달 → 보완 후 이동 또는 삭제
2. latest-tech/ 기존 파일 최신성 확인
   - 6개월 이상 된 내용 → 갱신 또는 DEPRECATED 표시
3. SAMPLE_STATUS.md 전체 업데이트
4. research/CHANGELOG.md 업데이트
5. git commit -m "🔄 [주간검수] YYYY-MM-DD 주간 정리"
6. push
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
| 🔄 진행중 | Phase 2: 데이터 수집 50 에피소드 | 팀 |
| ⏳ 대기 | ACT vs Diffusion Policy 결정 | 팀 결정 필요 |
| ⏳ 대기 | Isaac Sim vs Isaac Lab 결정 | 2026-04-22 크론 조사 후 |
| ⏳ 대기 | LeKiwi vs XLeRobot 결정 | Phase 4 |
| ⏳ 대기 | 카메라 업그레이드 결정 | 예산 확인 필요 |

---

## 🆕 변경 이력

| 날짜 | 변경 내용 | 변경자 |
|------|-----------|--------|
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
7. 크론 스케줄은 OpenClaw에서 관리됨 (다른 툴은 수동 실행)
