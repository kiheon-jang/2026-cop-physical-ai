# 🕐 크론 작업 페이로드 (cron-jobs.md)

> **Hermes Agent (Mac Mini M5) 의 크론 4개 완전 서술**
> 다른 환경으로 이전 시 이 파일의 페이로드를 참고하여 재등록.
> **최종 업데이트**: 2026-05-01 (시뮬 트랙 전환)

---

## 🌐 환경

- **플랫폼**: Hermes Agent (로컬 Mac Mini M5, 24/7 운영)
- **시간 기준**: KST (Asia/Seoul)
- **저장소**: GitHub `kiheon-jang/2026-cop-physical-ai` + Obsidian Vault
- **이전**: OpenClaw → Hermes (2026-04-29 완료), 시뮬 트랙 전환 (2026-05-01)
- **레거시 ID**: dc257031, b2e623a4, dcbf84a5, ed5aff22, 20ee15d4 (모두 폐기)

---

## 📋 크론 1 — 시뮬 환경 단계별 구축 (MuJoCo)

```
ID       : 9ad85007cf27
이름     : CoP Physical AI — 시뮬 환경 단계별 구축 (MuJoCo)
스케줄   : 0 23 * * *  (매일 23:00 KST)
타임아웃 : 600초
스킬     : terminal, file, web
```

### 페이로드 (전체)

```text
CoP Physical AI 시뮬 환경 단계별 구축 작업을 수행해주세요.

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
git pull origin main

## 컨텍스트 파악
1. AGENT_PROCESS.md 확인 — 현재 Phase/주차 식별
2. research/simulation/PHASE_ROADMAP.md 확인 — 오늘 단계 식별
3. agent/research-log/{어제 날짜}.md 확인 — 진척 상태
4. agent/external-dependencies.md 확인 — 차단 항목 있는지

## 환경
- Mac Mini M5 16GB, Apple Silicon ARM64
- 시뮬레이터: MuJoCo 3.x (네이티브)
- 모델: TheRobotStudio SO-ARM100/101 MJCF
- Python 3.12 + uv + LeRobot 이미 설치됨
- 실기 카메라 없음 (시뮬 가상 카메라만 사용)

## 작업 순서
1. 오늘 단계 작업 정의 (PHASE_ROADMAP.md 기준)
2. 작업 수행:
   - MuJoCo 설치/설정 (uv 사용)
   - MJCF 파일 다운로드/수정
   - 시뮬 코드 작성 (samples/)
   - viewer 또는 mujoco.Renderer로 동작 검증
3. research/simulation/<단계명>.md 에 결과 기록
4. ~/Documents/second-brain/00_AI_Wiki/CoP_PhysicalAI/2026-05/ 에 복사
5. 외부 의존 발견 시 agent/external-dependencies.md 추가
6. git add/commit/push (커밋: "🛠 [시뮬] <단계명> — YYYY-MM-DD")

완료 후 결과 요약.
```

---

## 📋 크론 2 — 시뮬 테스트 + 메트릭 수집

```
ID       : 85d322d3b37c
이름     : CoP Physical AI — 시뮬 테스트 + 메트릭 수집
스케줄   : 30 23 * * *  (매일 23:30 KST)
타임아웃 : 600초
스킬     : terminal, file
```

### 페이로드 (요약)

```text
CoP Physical AI 시뮬 테스트 + 메트릭 수집 작업을 수행해주세요.

## 사전 준비
cd /Users/markmini/Documents/dev/2026-cop-physical-ai && git pull origin main

## 작업 순서
1. 오늘 23:00에 구축한 시뮬 환경 실행 테스트 (5~10회 반복)
2. 메트릭 측정 (해당하는 것만):
   - 시뮬 동작 성공률
   - 추론 속도 (ms/step, ms/episode)
   - 시뮬-실기 관절각 오차 (Phase 1+ 이후)
   - 학습 손실 (학습 시작 이후)
3. agent/research-log/YYYY-MM-DD.md 작성
4. Obsidian Vault에 미러
5. 보고용 증거 후보 → agent/report-evidence/2026-MM/INDEX.md
6. 외부 의존 발견 시 agent/external-dependencies.md 추가
7. git add/commit/push (커밋: "📊 [로그] YYYY-MM-DD 시뮬 테스트 — <한줄 요약>")

완료 후 핵심 메트릭 요약.
```

---

## 📋 크론 3 — 아침 보고 메일

```
ID       : fb6d7cb26650
이름     : CoP Physical AI — 아침 보고 메일
스케줄   : 0 7 * * *  (매일 07:00 KST)
타임아웃 : 600초
스킬     : terminal, file, web, send_message
스크립트 : scripts/daily-report/generate_daily_report.py
```

### 동작

- `scripts/daily-report/generate_daily_report.py` 실행
- 어제 GitHub 커밋 + agent/research-log/ + agent/external-dependencies.md 수집
- `docs/01_overview/mail-template.md` 형식으로 메일 작성
- **[4-A] 외부 의존 / 사용자 수동 작업 섹션** 포함 (사용자 매일 노출)
- 3명 발송: xaqwer@gmail.com, insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com

> **TODO (2026-05-02 이후)**: generate_daily_report.py + mail-template.html 시뮬 트랙으로 전면 갱신 필요. 현재는 OpenClaw 시대 코드 일부 잔존.

---

## 📋 크론 4 — 주간 정리 + 보고용 증거 식별

```
ID       : 0b1d4a7b2bf7
이름     : CoP Physical AI — 주간 정리 + 보고용 증거 식별
스케줄   : 0 22 * * 0  (매주 일요일 22:00 KST)
타임아웃 : 600초
스킬     : terminal, file, web
```

### 페이로드 (요약)

```text
CoP Physical AI 주간 정리 + 보고용 증거 식별 작업을 수행해주세요.

## 작업 1: 일주일치 진행 종합
- agent/research-log/ 의 7일치 파일에서 핵심 메트릭/완료 항목 추출
- agent/report-evidence/2026-MM/<주차>_summary.md 작성

## 작업 2: 보고용 증거 식별
- 이번 주 결과 중 월별 보고서에 인용 가능한 항목 식별
- agent/report-evidence/2026-MM/INDEX.md 갱신

## 작업 3: external-dependencies.md 정리
- 7일 지난 [v] 완료 항목을 "완료 이력" 섹션으로 이동

## 작업 4: SAMPLE_STATUS.md 갱신
- samples/ 디렉토리의 모든 .py 파일 확인, 실행 결과 기록

## 작업 5: PHASE_ROADMAP.md 다음주 단계 명확화

## 커밋
git add -A && git commit -m "🔄 [주간정리] YYYY-MM-DD W주차 — 보고용 증거 X건"
git push origin main
```

---

## 🔧 새 환경에서 크론 재등록 방법

다른 머신/플랫폼으로 이전 시:

### Hermes Agent 환경 (권장)

```bash
# jobs.json 위치
~/.hermes/cron/jobs.json

# 위 4개 작업의 JSON을 직접 추가하거나
# hermes cron add 명령으로 등록 (CLI 지원 시)
```

### 다른 스케줄러 (crontab, GitHub Actions, n8n 등)

각 페이로드를 message/prompt 필드에 그대로 삽입하고 스케줄 적용:
- `0 23 * * *` → 시뮬 환경 구축
- `30 23 * * *` → 시뮬 테스트
- `0 7 * * *` → 아침 보고 메일
- `0 22 * * 0` → 주간 정리

---

## 📜 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-04-21 | 최초 작성 (OpenClaw 크론 4개 + 1회성 1개) — 레거시 |
| 2026-04-22 | Isaac Sim 1회성 크론 추가 — 완료 후 자동 삭제됨 |
| 2026-04-29 | OpenClaw → Hermes Agent 마이그레이션. 크론 ID 전부 변경 |
| 2026-05-01 | **시뮬 트랙 전환**. 4개 크론 prompt 전체 재작성. 요일별 주제 순환 폐기. PHASE_ROADMAP.md 기반 단계별 점진 구축으로 전환 |
