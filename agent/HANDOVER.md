# 🤖 AI Agent 인수인계 가이드 (HANDOVER.md)

> **다른 AI 에이전트가 이 프로젝트를 이어받을 때 가장 먼저 읽는 파일입니다.**
> 모든 설정, 크론, 스킬, 환경이 하위 파일에 완전히 서술되어 있습니다.
> **최종 업데이트**: 2026-05-01 (시뮬 트랙 전환)

---

## 📌 프로젝트 요약

| 항목 | 내용 |
|------|------|
| **프로젝트명** | CoP Physical AI (현대엘리베이터 사내 CoP) |
| **목표** | SO-ARM101 로봇팔로 PCB 조정 자동화 + RS232 HHT 결선 (10월 시연) |
| **GitHub** | https://github.com/kiheon-jang/2026-cop-physical-ai |
| **로컬 경로** | `/Users/markmini/Documents/dev/2026-cop-physical-ai` |
| **자동화 플랫폼** | Hermes Agent (Mac Mini M5, 24/7 로컬 운영) |
| **시뮬레이터** | MuJoCo 3.x (Apple Silicon 네이티브) — Phase 0~2 |
| **담당자** | 장기헌 (xaqwer@gmail.com) |
| **현재 단계** | **Phase 0 — 시뮬 환경 셋업 (5월)** |

---

## 📂 인수인계 파일 구조

```
agent/
├── HANDOVER.md              ← 지금 이 파일 (인덱스)
├── env.md                   ← Mac Mini/GitHub/이메일/하드웨어 환경 전체
├── cron-jobs.md             ← 크론 4개 페이로드 완전 서술
├── external-dependencies.md ← 외부 의존 / 사용자 수동 작업 누적
├── research-log/            ← 매일 시뮬 진척 기록 (자동)
├── report-evidence/         ← 보고용 증거 인덱스 (월별, 주간 정리 시 자동)
├── skills/
│   ├── README.md            ← 스킬 목록 및 사용 패턴
│   ├── gsk-vm-email-send.md (레거시 — 참고용)
│   ├── gsk-shared.md (레거시)
│   ├── gsk-web-search.md (레거시)
│   └── gsk-crawler.md (레거시)
└── templates/
    └── README.md            ← 메일/결정폼 템플릿 경로 안내
```

> ⚠️ `agent/skills/` 의 gsk-* 파일은 OpenClaw 시대 레거시. Hermes 환경에서는 미사용.

---

## 🚀 인수인계 체크리스트 (새 에이전트 최초 실행 시)

### 1단계 — 환경 확인

```bash
# GitHub 인증 확인
gh auth status

# 레포 최신화
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
git pull origin main

# Hermes 게이트웨이 동작 확인
launchctl list | grep hermes
```

### 2단계 — 현재 상태 파악

```bash
# 현재 Phase/주차 확인
cat research/simulation/PHASE_ROADMAP.md | head -80

# 어제 진척 확인
ls -lt agent/research-log/ | head -5
cat agent/research-log/$(ls agent/research-log/ | tail -1)

# 외부 의존 미해결 항목
cat agent/external-dependencies.md

# 결정 대기 항목
cat research/decisions/README.md

# 시뮬 단계별 기록
ls research/simulation/
```

### 3단계 — Hermes 크론 상태 확인

```bash
# 크론 목록 확인
hermes cron list

# 또는 jobs.json 직접 확인
cat ~/.hermes/cron/jobs.json | python3 -m json.tool
```

### 4단계 — Obsidian 동기화 확인

```bash
# Obsidian Vault에 미러된 파일 확인
ls ~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/
ls ~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/2026-05/
```

---

## 📋 현재 자동화 파이프라인 (Hermes Agent, 2026-05-01~)

```
매일 23:00 KST
  └─ [크론 9ad85007cf27] 시뮬 환경 단계별 구축 (MuJoCo)
       → research/simulation/PHASE_ROADMAP.md 기준 오늘 단계 식별
       → MJCF 수정 / 카메라 설정 / 매핑 검증 등
       → research/simulation/<단계명>.md 작성
       → Obsidian Vault에 미러
       → GitHub push

매일 23:30 KST
  └─ [크론 85d322d3b37c] 시뮬 테스트 + 메트릭 수집
       → 23:00에 구축한 환경 실행 테스트
       → 메트릭 측정 (성공률, 추론시간, 관절각 오차, 학습 손실)
       → agent/research-log/YYYY-MM-DD.md 작성
       → 보고용 증거 후보 식별 (agent/report-evidence/)
       → GitHub push

매일 07:00 KST
  └─ [크론 fb6d7cb26650] 아침 보고 메일
       → 어제 research-log + external-dependencies 수집
       → mail-template.md 형식으로 메일 작성
       → [4-A] 외부 의존 섹션에 사용자 수동 작업 매일 노출
       → 3명 발송 (xaqwer@gmail.com, insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com)

매주 일요일 22:00 KST
  └─ [크론 0b1d4a7b2bf7] 주간 정리 + 보고용 증거 식별
       → 일주일치 research-log 종합
       → agent/report-evidence/2026-MM/INDEX.md 갱신
       → external-dependencies.md 정리 (완료 항목 이동)
       → SAMPLE_STATUS.md 갱신
       → GitHub push
```

---

## 📊 프로젝트 단계 현황 (2026-05-01 기준)

| Phase | 기간 | 내용 | 상태 |
|-------|------|------|------|
| Phase 1 (구) | 2026-04 | 환경 구축 (조립/LeRobot/텔레오퍼레이션/카메라) | ✅ 완료 |
| **Phase 0** (신) | 2026-05 | 시뮬 환경 셋업 (MuJoCo + SO-ARM101 MJCF) | 🔄 **진행중** |
| **Phase 1** (신) | 2026-06 | 시뮬 사전학습 (200 ep + ACT) | ⏳ 대기 |
| **Phase 2** (신) | 2026-07 | Sim2Real 검증 (DR + ACT/DP 비교) | ⏳ 대기 |
| **Phase 3** (신) | 2026-08 | PCB 조정 시뮬 학습 | ⏳ 대기 |
| **Phase 4** (신) | 2026-09 | RS232 HHT 결선 시뮬 학습 | ⏳ 대기 |
| **Phase 5** (신) | 2026-10 | 통합 시연 + 사내 발표 | ⏳ 대기 |

> Phase 번호 체계는 2026-05-01에 재정의됨.
> 구 Phase 1(환경구축)은 완료, 신 Phase 0~5는 시뮬 트랙.
> 상세: [research/simulation/PHASE_ROADMAP.md](../research/simulation/PHASE_ROADMAP.md)

---

## 🗂️ 결정 대기 항목

| 항목 | 상태 | 비고 |
|------|------|------|
| **시뮬레이터 선택** | ✅ **결정 완료** (2026-04-22 / 확정 05-01) | MuJoCo (Phase 0~2) + Isaac Lab (Phase 3+, 차년도) |
| ACT vs Diffusion Policy | ⏳ 대기중 | Phase 2 (7월) 비교 후 결정 |
| LeKiwi vs XLeRobot | ⏳ 대기중 | Phase 4 (차년도) |
| 카메라 업그레이드 여부 | ⏳ 대기중 | 예산 확인 필요 |

> 결정 완료 시 `research/decisions/YYYY-MM-DD_항목.md` 파일이 자동 생성됩니다.

---

## 🔗 주요 파일 빠른 링크

| 파일 | 설명 |
|------|------|
| [env.md](./env.md) | Mac Mini/GitHub/이메일/하드웨어 환경 전체 |
| [cron-jobs.md](./cron-jobs.md) | 크론 4개 페이로드 완전 서술 (Hermes) |
| [external-dependencies.md](./external-dependencies.md) | 외부 의존 / 사용자 수동 작업 누적 |
| [../research/simulation/PHASE_ROADMAP.md](../research/simulation/PHASE_ROADMAP.md) | Phase 0~5 단계별 로드맵 |
| [../docs/01_overview/mail-template.md](../docs/01_overview/mail-template.md) | 일일 보고 메일 형식 |
| [../docs/01_overview/decisions-form.html](../docs/01_overview/decisions-form.html) | 팀원 기술결정 폼 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 품질 기준 |
| [../samples/SAMPLE_STATUS.md](../samples/SAMPLE_STATUS.md) | 샘플코드 완성도 현황 |
| [../research/decisions/README.md](../research/decisions/README.md) | 기술 결정 로그 |
| [../research/CHANGELOG.md](../research/CHANGELOG.md) | 리서치 업데이트 이력 |

---

## ⚠️ 중요 주의사항 (Hermes Agent 환경)

1. **Git push 전 인증 갱신 필수**
   ```bash
   git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
   ```

2. **이메일 발송**: `scripts/daily-report/generate_daily_report.py` (Hermes가 자동 실행)
   - 이전 `gsk vm_email send` (OpenClaw) 명령은 더 이상 사용하지 않음

3. **크론은 Hermes Agent (Mac Mini M5)에서 자동 관리**
   - jobs.json 위치: `~/.hermes/cron/jobs.json`
   - 변경 시 Hermes 재시작 또는 `hermes cron reload` 필요

4. **메일 본문에 ASCII 박스 문자 금지** (`┌┐└┘━` 등 → 메일 클라이언트에서 깨짐)

5. **GitHub + Obsidian 이중 동기화**
   - GitHub: `/Users/markmini/Documents/dev/2026-cop-physical-ai/`
   - Obsidian: `~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/`
   - Hermes 크론이 매일 자동으로 양쪽 갱신

6. **이 파일(HANDOVER.md), AGENT_PROCESS.md, PHASE_ROADMAP.md는 요구사항 변경 시 반드시 업데이트**

7. **레거시 폴더 (참고용 — 수정 금지)**:
   - `temp-robot-arm-project/` — 이전 OpenClaw 시대 구조
   - `archive/` — Obsidian 원본 노트 보존

---

## 📝 변경 이력

| 날짜 | 내용 | 작성자 |
|------|------|--------|
| 2026-04-21 | 최초 인수인계 패키지 구성 | AI Agent (OpenClaw, 레거시) |
| 2026-04-22 | HTML 메일 템플릿 + 결정 폼 추가 | AI Agent (OpenClaw, 레거시) |
| 2026-04-29 | OpenClaw → Hermes Agent 마이그레이션 완료 | Claude Code (Mac M5) |
| 2026-05-01 | **시뮬 트랙 전환**: Isaac Lab → MuJoCo, Phase 0~5 재정의, 크론 ID/기능 전부 갱신, [4-A] 외부의존 섹션 신설, Obsidian 동기화 추가 | Hermes Agent |
