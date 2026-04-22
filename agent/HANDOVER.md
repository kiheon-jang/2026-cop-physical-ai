# 🤖 AI Agent 인수인계 가이드 (HANDOVER.md)

> **다른 AI 에이전트가 이 프로젝트를 이어받을 때 가장 먼저 읽는 파일입니다.**  
> 모든 설정, 크론, 스킬, 환경이 하위 파일에 완전히 서술되어 있습니다.

---

## 📌 프로젝트 요약

| 항목 | 내용 |
|------|------|
| **프로젝트명** | CoP Physical AI (현대엘리베이터 사내 CoP) |
| **목표** | SO-ARM101 로봇팔로 모방학습 → 강화학습 → 모바일 매니퓰레이터 |
| **GitHub** | https://github.com/kiheon-jang/2026-cop-physical-ai |
| **로컬 경로** | `/home/work/.openclaw/workspace/2026-cop-physical-ai` |
| **담당자** | 장기헌 (xaqwer@gmail.com) |
| **현재 단계** | Phase 2 — 데이터 수집 (0/50 에피소드) |

---

## 📂 인수인계 파일 구조

```
agent/
├── HANDOVER.md          ← 지금 이 파일 (인덱스)
├── env.md               ← VM/GitHub/이메일/하드웨어 환경 설정 전체
├── cron-jobs.md         ← 크론 5개 페이로드 완전 서술
├── skills/
│   ├── README.md        ← 스킬 목록 및 사용 패턴
│   ├── gsk-vm-email-send.md
│   ├── gsk-shared.md
│   ├── gsk-web-search.md
│   └── gsk-crawler.md
└── templates/
    └── README.md        ← 메일/결정폼 템플릿 경로 안내
```

---

## 🚀 인수인계 체크리스트 (새 에이전트 최초 실행 시)

### 1단계 — 환경 확인

```bash
# GitHub 인증 확인
gh auth status

# 레포 최신화
cd /home/work/.openclaw/workspace/2026-cop-physical-ai
git pull origin main

# gsk 동작 확인
gsk search "test" 2>&1 | head -3
```

### 2단계 — 현재 상태 파악

```bash
# 데이터 수집 현황
cat docs/05_data-collection/TRACKING.md

# 샘플 완성도
cat samples/SAMPLE_STATUS.md

# 결정 대기 항목
cat research/decisions/README.md

# 최근 크론 실행 결과 확인
ls research/drafts/ | sort | tail -5
ls samples/ -R | grep ".py$" | tail -10
```

### 3단계 — 크론 상태 확인 (OpenClaw 환경)

```bash
openclaw cron list
```

> ⚠️ OpenClaw 외 환경이면 크론이 없으므로 수동 실행 또는 재등록 필요  
> → [cron-jobs.md](./cron-jobs.md) 참조

### 4단계 — 웹 서비스 확인

- 결정 폼: https://ookixght.gensparkclaw.com/decisions.html
- 메일 미리보기: https://ookixght.gensparkclaw.com/mail-preview.html

---

## 📋 현재 자동화 파이프라인

```
매일 23:00 KST
  └─ [크론 dc257031] 리서치 초안 생성
       → research/drafts/YYYY-MM-DD_topic.md 저장
       → research/CHANGELOG.md 업데이트
       → GitHub push

매일 23:30 KST
  └─ [크론 b2e623a4] 샘플코드 생성
       → samples/카테고리/파일.py 저장
       → samples/SAMPLE_STATUS.md 업데이트
       → GitHub push

매일 07:00 KST
  └─ [크론 dcbf84a5] 보고 메일 발송
       → GitHub에서 최신 커밋/현황 수집
       → mail-template.html 기반 HTML 메일 생성
       → 3명 발송 (gsk vm_email send)

매주 일요일 22:00 KST
  └─ [크론 ed5aff22] 주간 검수
       → drafts/ → latest-tech/ 이동 (품질 통과 시)
       → latest-tech/ 파일 최신성 확인
       → 샘플 전체 재실행 검증
       → AGENT_PROCESS.md / CHANGELOG.md 업데이트
```

---

## 📊 프로젝트 단계 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | 환경 구축 (조립/LeRobot/텔레오퍼레이션/카메라) | ✅ 완료 |
| Phase 2 | 데이터 수집 (목표: 50 에피소드) | 🔄 진행중 (0/50) |
| Phase 3 | 강화학습 시뮬레이션 (Isaac Lab/Sim) | ⏳ 대기 |
| Phase 4 | 모바일 매니퓰레이터 (LeKiwi/XLeRobot) | ⏳ 대기 |

---

## 🗂️ 결정 대기 항목

| 항목 | 상태 | 결정 방법 |
|------|------|----------|
| ACT vs Diffusion Policy | ⏳ 대기중 | [결정 폼](https://ookixght.gensparkclaw.com/decisions.html) |
| Isaac Sim vs Isaac Lab | ⏳ 대기중 | [결정 폼](https://ookixght.gensparkclaw.com/decisions.html) |
| LeKiwi vs XLeRobot | ⏳ 대기중 | [결정 폼](https://ookixght.gensparkclaw.com/decisions.html) |
| 카메라 업그레이드 여부 | ⏳ 대기중 | [결정 폼](https://ookixght.gensparkclaw.com/decisions.html) |

> 결정 완료 시 `research/decisions/YYYY-MM-DD_항목.md` 파일이 자동 생성됩니다.

---

## 🔗 주요 파일 빠른 링크

| 파일 | 설명 |
|------|------|
| [env.md](./env.md) | VM/GitHub/이메일/하드웨어 환경 전체 |
| [cron-jobs.md](./cron-jobs.md) | 크론 5개 페이로드 완전 서술 |
| [skills/README.md](./skills/README.md) | 사용 스킬 목록 |
| [../docs/01_overview/mail-template.html](../docs/01_overview/mail-template.html) | 일일 보고 HTML 메일 템플릿 |
| [../docs/01_overview/decisions-form.html](../docs/01_overview/decisions-form.html) | 팀원 기술결정 폼 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 품질 기준 (리서치/샘플 등급) |
| [../samples/SAMPLE_STATUS.md](../samples/SAMPLE_STATUS.md) | 샘플코드 완성도 현황 |
| [../docs/05_data-collection/TRACKING.md](../docs/05_data-collection/TRACKING.md) | 데이터 수집 에피소드 현황 |
| [../research/decisions/README.md](../research/decisions/README.md) | 기술 결정 로그 |
| [../research/CHANGELOG.md](../research/CHANGELOG.md) | 리서치 업데이트 이력 |

---

## ⚠️ 중요 주의사항

1. **Git push 전 인증 갱신 필수**
   ```bash
   git remote set-url origin https://$(gh auth token)@github.com/kiheon-jang/2026-cop-physical-ai.git
   ```

2. **이메일 발송 시 `-f $OPENCLAW_VM_NAME` 필수**

3. **크론은 OpenClaw 플랫폼 전용** — 다른 AI 도구에서 자동 실행 안 됨

4. **메일 본문에 ASCII 박스 문자 금지** (`┌┐└┘━` 등 → 메일 클라이언트에서 깨짐)

5. **결정 폼 URL 항상 고정**
   ```
   https://ookixght.gensparkclaw.com/decisions.html
   ```

6. **이 파일(HANDOVER.md) 및 AGENT_PROCESS.md는 요구사항 변경 시 반드시 업데이트**

---

## 📝 변경 이력

| 날짜 | 내용 | 작성자 |
|------|------|--------|
| 2026-04-21 | 최초 인수인계 패키지 구성 | AI Agent (OpenClaw) |
| 2026-04-22 | HTML 메일 템플릿 + 결정 폼 추가, agent/ 폴더 구조화 | AI Agent (OpenClaw) |
