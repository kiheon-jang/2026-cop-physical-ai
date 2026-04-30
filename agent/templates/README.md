# 템플릿 파일 안내 (Templates)

> **2026-05-01 갱신**: OpenClaw 시대 외부 호스팅(ookixght.gensparkclaw.com) 폐기. Hermes Agent (Mac Mini M5) 로컬 운영으로 전환.

---

## 일일 보고 메일 템플릿

| 항목 | 경로 |
|------|------|
| **메일 본문 형식 (Markdown)** | [`../../docs/01_overview/mail-template.md`](../../docs/01_overview/mail-template.md) |
| **HTML 템플릿 (script가 사용)** | [`../../docs/01_overview/mail-template.html`](../../docs/01_overview/mail-template.html) |
| **발송 스크립트** | [`../../scripts/daily-report/generate_daily_report.py`](../../scripts/daily-report/generate_daily_report.py) |
| **발송 시간** | 매일 07:00 KST (Hermes 크론 `fb6d7cb26650`) |

### 교체되는 동적 항목

매일 크론이 다음 데이터로 채움:

| 섹션 | 데이터 소스 |
|------|------------|
| `[0] 한 줄 요약` | 어제 진척에서 핵심 한 문장 |
| `[1] 어제 완료한 작업` | `git log --since=yesterday` |
| `[3] 시뮬 환경 진행도` | `research/simulation/PHASE_ROADMAP.md` |
| `[4] 의사결정 대기 항목` | `research/decisions/README.md` |
| `[4-A] 외부 의존 / 사용자 수동 작업` | `agent/external-dependencies.md` |
| `[5] 오늘의 시뮬 진척` | `agent/research-log/{어제 날짜}.md` |
| `[6] 시뮬/학습 스크립트 현황` | `samples/SAMPLE_STATUS.md` |
| `[7] 경로 및 구조 변경` | `git log --name-status` |
| `[8] 내일 예정` | `PHASE_ROADMAP.md` 다음 단계 |

---

## 기술 결정 폼 (Optional)

**파일**: [`../../docs/01_overview/decisions-form.html`](../../docs/01_overview/decisions-form.html)

> ⚠️ OpenClaw 시대에는 외부 URL(`https://ookixght.gensparkclaw.com/decisions.html`)에서 호스팅했으나, Hermes 전환으로 외부 호스팅 폐기됨. 현재는 로컬 HTML 파일로만 보존.
>
> 필요 시 사용자가 직접 브라우저로 열어 사용 가능. 자동 GitHub 커밋 기능은 동작 안 함.

### 대체 결정 방식 (현재)

1. 사용자가 직접 `research/decisions/YYYY-MM-DD_<주제>.md` 파일 생성
2. 또는 Hermes에게 "결정 항목 X에 대해 ✅ 채택으로 기록해줘" 요청 → 자동 커밋

---

## 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-04-21 | 최초 작성 (OpenClaw 외부 URL 호스팅 기준) |
| 2026-05-01 | OpenClaw 외부 URL 제거, Hermes 로컬 운영으로 전환. 시뮬 트랙 메일 섹션 반영. |
