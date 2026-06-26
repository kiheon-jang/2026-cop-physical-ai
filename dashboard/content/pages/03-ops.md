---
id: ops
title: "AI 자동화 운영 방법"
order: 3
menu_route: ops
screenshot: ops.png
category: 핵심
---
## 기능명세

<!-- slide title="AI 자동화 운영 방법 — 개요" -->

AI 자동화 운영 방법 화면(`view-ops`)은 이 프로젝트의 자동화 운영 구조 — cron 스케줄, 시스템 구성, 데이터 흐름, 역할 분담 — 를 정적 HTML로 상세히 문서화한다. 이 화면의 내용은 빌드 시점에 고정되며, 실시간 데이터 주입 요소는 `ops-act-status`(ACT 학습 시작 여부) 텍스트 하나다.

**한 줄 결론 박스 (ops-summary)**
"반복 작업은 자동으로 진행되며, 핵심 판단과 외부 의존 해결은 사람이 담당합니다"라는 프로젝트 운영 방침 요약.

<!-- slide title="시스템 구성도" screenshot="" -->

**시스템 구성도 (ops-tree)**
트리 형식 ASCII 다이어그램으로 구성:
- 루트: 로컬 Mac Mini (24/7 가동)
  - **Hermes Agent**: 로컬 AI 에이전트, Gemini 2.5 Flash 백엔드(무료)
    - cron 1 · 매일 23:00: 시뮬 환경 단계별 구축(MuJoCo)
    - cron 2 · 매일 23:30: 시뮬 테스트 + 메트릭 수집
    - cron 3 · 매일 07:00: 아침 보고 메일 자동 발송
    - cron 4 · 일요 22:00: 주간 정리 + 보고용 증거 식별
  - **Self-heal**: 실패 자동 기록 + 다음 cron 재시도
  - **Claude 위임**: 복잡 추론은 `claude -p`로 위임
  - **Git auto-push**: 코드/로그/보고서 자동 commit+push
  - **hermes-mark**: 대시보드 서버(Fastify + Cloudflare Tunnel)
    - chokidar(파일 변경 감지), WebSocket(브라우저 라이브 갱신), Cloudflare Tunnel(외부 도메인)

<!-- slide title="크론 작업 표 + 하루 흐름" screenshot="" -->

**크론 작업 표 (cron-table)**
4행 테이블(시각 / 잡 이름·설명 / 역할 / 결과물):

| 시각 | 역할 | 결과물 |
|------|------|--------|
| 매일 23:00 | 시뮬 환경 단계별 구축 (PHASE_ROADMAP 읽어 오늘 단계 식별 → MuJoCo 코드 작성/실행) | `research/simulation/*.md`, `samples/training/*.py` |
| 매일 23:30 | 시뮬 테스트 + 메트릭 (Pick-Place 성공률, 추론 시간, 200ep 데이터셋 정합성 검증) | `agent/research-log/YYYY-MM-DD.md` |
| 매일 07:00 | 아침 보고 메일 (`generate_daily_report.py` → 이메일 4명 발송, CHANGELOG/README 자동 갱신 후 git push) | 이메일(담당자+수신자), `CHANGELOG.md` |
| 일요 22:00 | 주간 정리 + 보고용 증거 (한 주 결과 정리 + 월별 보고서 후보 식별) | `agent/report-evidence/YYYY-MM/INDEX.md` |

**하루 자동화 흐름 (day-timeline)**
00:00~24:00 KST 타임라인 축에 4개 이벤트 마커를 배치한 시각적 타임라인. 텍스트 설명: "밤 시간대(23:00, 23:30) 시뮬·학습 작업 → 다음 날 07:00 메일로 결과 수신. 일요일 밤은 주간 정리 추가."

<!-- slide title="Hermes Agent 카드" screenshot="" -->

**Hermes Agent 카드 (hermes-card)**
에이전트 스펙 상세:
- 호스트: 로컬 Mac Mini
- 가동: 24/7 (재부팅 자동 복구)
- 백엔드 모델: Gemini 2.5 Flash(무료)
- 복잡 추론: Claude 위임(`claude -p`)
- 스킬: `cop-physical-ai-self-heal`
- 권한: gh CLI · git · file system · Python venv
- OpenClaw → Hermes 마이그레이션 2026-04-29 완료

자가치유(Self-heal) 설명: 매 cron 작업 끝에 실패/차단 항목 자동 기록 → `chore(self-heal)` commit → 다음 cron에서 자동 재시도. 활동 타임라인의 heal 점 표시가 발생 일수.

<!-- slide title="데이터 흐름 + 역할 분담" screenshot="" -->

**데이터 흐름 다이어그램 (dataflow)**
4개 행:
1. Hermes cron(23:00) → MuJoCo 시뮬 실행 → `data/episodes/` (LeRobot Dataset) → ACT 학습 (상태 동적, `ops-act-status`)
2. Hermes cron(23:30) → 메트릭 측정 → `research-log/*.md` → git push
3. 파일 변경 → hermes-mark chokidar → `build.py` 자동 실행 → WebSocket 푸시 → 브라우저 라이브 갱신
4. Obsidian 월별 보고서 → `build.py` 읽음 → renderMarkdown → 보고용 자료 메뉴 임베드

**역할 분담 표 (who-table)**
10개 영역 × 3열(AI/자동, 사람, 비고):
- 자동: 시뮬 코드 작성, 시뮬 실행+메트릭, 연구 로그 작성, 아침 보고 메일, 주간/월간 증거 식별, 대시보드 데이터+빌드
- 사람+AI 협업: 월별 보고서(AI 초안·사람 수정), 의사결정(AI 제안·사람 확정), 외부 의존 해결(AI 식별·사람 해결)
- 사람 전담: 디자인·톤·보고 방향, 대시보드 설계

**데이터 출처**: 이 화면은 대부분 정적 HTML. 유일한 동적 요소는 `ops-act-status` 텍스트(ACT 학습 진행 여부, JavaScript가 `training_metrics.status`에서 채움).

## 사용가이드

<!-- slide title="사용가이드 — 개요" -->

AI 자동화 운영 방법은 "이 프로젝트가 어떻게 자동으로 돌아가는지" 설명하는 화면입니다. 직접 조작할 버튼은 없습니다.

**읽는 순서**
1. **한 줄 결론 박스** — 먼저 이것만 읽어도 전체 구조가 파악됩니다.
2. **크론 작업 표** — 매일 언제 무슨 일이 자동으로 일어나는지 확인합니다.
3. **역할 분담 표** — 사람이 직접 해야 하는 일이 무엇인지 확인합니다.

<!-- slide title="표 보는 법 + 역할 분담" screenshot="" -->

**크론 작업 표 보는 법**
"크론(cron)"은 정해진 시각에 자동으로 실행되는 작업입니다. 이 프로젝트는 매일 밤 23시에 시뮬레이션이 자동으로 돌아가고, 23시 30분에 그 결과를 자동으로 테스트합니다. 다음 날 아침 7시에 이메일로 결과가 도착합니다.

**데이터 흐름 다이어그램**
화면 아래쪽의 → 화살표 다이어그램은 데이터가 어떤 순서로 흘러가는지 보여줍니다. "시뮬 실행 → 데이터 파일 생성 → 대시보드 자동 갱신"의 데이터 파이프라인 단계는 자동으로 진행됩니다. 단, 디자인·보고 방향 결정, 의사결정 확정, 외부 의존(부품·환경 등) 해결은 사람이 직접 담당합니다(역할 분담 표 참고).

**역할 분담 표**
"사람" 열에 체크된 항목만 직접 처리해야 합니다. 주로 외부 의존(부품 구매·3D 프린팅) 처리, 의사결정 확정, 월별 보고서 수정이 해당됩니다.
