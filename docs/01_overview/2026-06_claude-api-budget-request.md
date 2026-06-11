# 「CoP Physical AI — 자율 운영 트랙」 LLM API (Claude) 예산 집행 기안

> CoP 자율트랙(AX) — 「Physical AI 기술 내재화 — SO-ARM101 기반 정비현장 자동화」
> 기획·개발 및 24시간 자율 운영 시스템

작성일: 2026-06-08

---

## 1. 요청 내역

| 항목 | 내용 |
|------|------|
| **신청자** | 장기헌 (R&D전략기획) |
| **용도** | CoP 자율트랙(AX) — 「Physical AI 기술 내재화」 PoC 개발 + 자율 운영 시스템 |
| **사용 모델** | Claude (Sonnet 4.5 / Opus · `claude -p` 위임) |
| **운영 기간** | 2026-04 ~ 2026-10 (사전학습 + Phase 0~4 작업 9월 완료 + 10월 시연, 7개월) · 차년도 Phase 3+ 연장 검토 |

**프로젝트 개요**

SO-ARM101 (오픈소스 6-DoF 로봇팔) 기반 모방학습으로 정비현장 PCB 작업 자동화 1차 기능 완성을 목표로 함. 데이터 수집은 MuJoCo 시뮬 합성으로 진행 (200 에피소드 / 12,400 프레임 완료), ACT (Action Chunking Transformer) 모방학습 알고리즘으로 2026-06-15부터 모델 학습 착수. 10월까지 PCB 픽앤플레이스 70% / RS232 부분 성공 40% 목표.

상시 라이브 대시보드: https://cop-physical-ai.hermesmark.site/

---

## 2. Claude 필요 사유

### (1) 자율 운영 인프라의 복잡 추론 백엔드 — 핵심 사유

- 로컬 Mac Mini 1대가 24시간 가동되며, **Hermes Agent (로컬 AI 에이전트, Gemini 2.5 Flash 무료 백엔드)** 가 cron 4건을 자동 실행
- 일상 작업은 Gemini, **복잡한 시뮬 코드 작성 / 학습 파이프라인 구현 / 의사결정 분석 / 이슈 복구는 Claude (`claude -p`) 위임**
- 수동 개입 없이 자율 운영 — 매일 23:00 시뮬 환경 구축, 23:30 시뮬 테스트 + 메트릭 수집, 07:00 일일 보고 메일 (4명 자동 발송), 일요 22:00 주간 정리 + 보고용 증거 식별

사내 표준 도구 (단일 LLM 인터페이스) 로는 cron 자동 실행 + 멀티파일 자율 편집 + 자가치유 기록까지 통합 수행 어려움. **Claude `claude -p` 위임 패턴이 자율 운영 가능성의 핵심**.

### (2) 별도 개발 인력 미배정 — Claude Code 활용 자동 코드 생성

본 CoP 는 별도 개발 인력 배정 없이 PM 1인 단독 트랙으로 진행됨. **Claude Code (터미널 기반 agentic 코딩 도구)** 가 자연어 지시만으로 시뮬 / 학습 / 검증 코드를 다중 파일 편집 + 명령 실행 + 테스트 반복까지 자동 수행하므로 별도 개발 인력 투입 없이 CoP 마일스톤 준수 가능.

5~6월 진행 결과 (Claude Code 활용 자동 생성된 자산):

- MuJoCo 3.8 + SO-ARM101 MJCF 시뮬 환경 셋업
- 카메라 시뮬 (천장 + 그리퍼 시점), 관절 캘리브레이션, 마찰계수 튜닝
- Pick-Place 시나리오 (큐브 50mm, IK 기반)
- 자동 데이터 합성 200 에피소드 / 12,400 프레임 (LeRobot Dataset v3.0 포맷)
- ACT 학습 파이프라인 (`scripts/train_act.py`) — 2026-06-15 학습 착수 예정
- 진척 시각화 대시보드 (라이브 갱신, 외부 도메인 노출)

사내 표준 도구로는 동등 수준의 자동 코드 생성 / 디버깅 / 다중파일 일괄 수정 기대 어려움.

### (3) 멀티모델 교차검증 — 의사결정 신뢰성

시뮬레이터 선택 (MuJoCo vs Isaac Lab), 학습 알고리즘 (ACT vs Diffusion Policy vs π0), 데이터 수집 방식 (시뮬 합성 vs 텔레오퍼레이션) 등 핵심 의사결정 시 **Gemini · Claude 병렬 분석 후 일치 결과만 채택**. 단일 모델 환각 / 편향 리스크 회피.

결정 근거는 `research/decisions/` 폴더에 문서화 → 차년도 인수인계 / 외부 보고 / 감사 대응 자료로 활용.

### (4) 비정형 한국어 처리 + 보고서 자동 작성

Hermes cron 이 매일 작성하는 **research-log / 일일 보고 메일 / 월간 활동보고서 초안** 의 한국어 long-context 의미 보존 요약에 Claude 강점 활용.

정비 현장 용어 (RS232, HHT, DIP S/W 등) + 시뮬·학습 전문 용어 (ACT, MJCF, qpos, chunk_size 등) 혼재 환경에서 정확한 요약 필요. CoP 담당자는 초안 위에 의사결정 + 외부 보고 톤 보완만 담당 (작성 부담 ↓).

### (5) Artifacts / Claude Code 활용 즉시 시각화

**실시간 진척 시각화 대시보드** (https://cop-physical-ai.hermesmark.site/) 를 Claude Code 단기간 구현. 7개 메뉴 (Overview · CoP 리뷰 · AI 자동화 운영 · Phase 로드맵 · 시뮬 영상 · 활동 타임라인 · 보고용 자료) 통합 노출. chokidar + WebSocket 라이브 갱신. Obsidian 월간 보고서 풀 임베드.

시뮬 영상 · 하드웨어 사진 · 200 에피소드 학습 데이터셋 영상 통합 노출 → 현업·임원 보고 시 화면 한 장으로 진척 가시화. 사내 시스템화 의사결정 단계 단축.

---

## 3. 보안 운영 원칙

- **원본 데이터 직접 입력 금지** — 비식별화·마스킹 샘플만 활용
- **Claude 유료 플랜의 No-Train 정책 적용** (입력 데이터 모델 학습 미사용)
- **로컬 처리 우선** — 로컬 Mac Mini 에서 시뮬·학습 처리, 외부 전송은 LLM API 호출 시에만. 학습 데이터 / 시뮬 영상 / 보고서 원본은 외부 송신 없음
- **사내 GitHub 조직 계정 한정** — 코드/로그 git push 는 사내 계정 (`kiheon-jang/2026-cop-physical-ai`) 한정
- **자가치유 메커니즘** — 권한 차단 / API 오류 발생 시 외부 인프라 미사용, 다음 cron 에서 자동 재시도. 모든 실패 기록은 `chore(self-heal)` commit 으로 추적 가능

---

## 4. 비용

- **CoP 자율트랙(AX) 예산 내 집행**
- Claude API 호출 패턴:
  - cron 1 (매일 23:00, 시뮬 환경 구축) — Gemini 1차 처리 + 복잡 코드 작성 시 Claude 위임
  - cron 2 (매일 23:30, 시뮬 테스트) — 동일 패턴
  - cron 3 (매일 07:00, 보고 메일) — Gemini 단독 (한국어 요약은 Claude 위임 옵션)
  - cron 4 (일요 22:00, 주간 정리) — Claude 위임 비중 높음 (의사결정 분석 / 보고서 작성)
  - Self-heal / 의사결정 분석 / 대시보드 개선 — 비주기적 추가 호출
- **모델**: Claude Sonnet 4.5 (일반 작업) + Opus (복잡 추론 / 의사결정 분석)
- **월 예상 사용량**: 5~6월 실측 기준 별도 산정 (첨부 자료 참조)

---

## [첨부]

### 1. CoP Physical AI 7개월 로드맵 (사전학습 + Phase 0~4 + 시연)

| Phase | 기간 | 내용 | 상태 |
|-------|------|------|------|
| 사전학습 / Kick-off | 4월 | 하드웨어 발주 + ACT/DP 자료 학습 (phase 외부) | ✅ 완료 |
| Phase 0 | 5월 | 시뮬 환경 셋업 (MuJoCo + SO-ARM101) | ✅ 완료 |
| Phase 1 | 6월 | AI 모델 사전학습 (200ep 데이터 + ACT 학습) | 🔄 진행 (W3 6/15 학습 착수) |
| Phase 2 | 7월 | 실기 검증 — Sim2Real (실기 50ep 수집) | ⏳ 예정 |
| Phase 3 | 8월 | PCB 부품 픽앤플레이스 학습 | ⏳ 예정 |
| Phase 4 | 9월 | RS232 통신 학습 + DP 비교 + **1차 기능 완성** (PCB 70% / RS232 40%, 작업 완료) | ⏳ 예정 |
| 시연 | 10월 | 통합 시연 + 사내 발표 (phase 외부) | ⏳ 예정 |
| 차년도 | 2027~ | Isaac Lab + LeIsaac + GR00T 대규모 RL (별도 GPU 서버) | 검토 |

### 2. 자율 운영 시스템 구성도

```
로컬 Mac Mini (24/7 가동)
  ├─ Hermes Agent (Gemini 2.5 Flash 백엔드, 무료)
  │   ├─ cron 1 · 매일 23:00 — 시뮬 환경 구축 (MuJoCo)
  │   ├─ cron 2 · 매일 23:30 — 시뮬 테스트 + 메트릭 수집
  │   ├─ cron 3 · 매일 07:00 — 아침 보고 메일 (4명 자동 발송)
  │   └─ cron 4 · 일요 22:00 — 주간 정리 + 보고용 증거 식별
  ├─ Self-heal (실패 시 chore(self-heal) commit + 다음 cron 재시도)
  ├─ Claude 위임 (복잡 추론은 `claude -p` 로 위임) ← 본 기안 대상
  ├─ Git auto-push (코드/로그/보고서 자동 commit)
  └─ hermes-mark (대시보드 서버, Fastify + Cloudflare Tunnel)
```

### 3. 현재 진척 증거

- 200 에피소드 / 12,400 프레임 학습 데이터셋 합성 완료 (`data/episodes/`)
- LeRobot Dataset v3.0 포맷 (parquet + mp4 분리 저장)
- MuJoCo 시뮬 영상 (Pick-Place, 6축 동작, 천장+그리퍼 카메라 시점)
- SO-ARM101 하드웨어 사진 (Leader/Follower, RealSense D405 마운트)
- Obsidian 월간 활동보고서 8건 (4~10월)
- 라이브 대시보드: https://cop-physical-ai.hermesmark.site/

### 4. 사용 기술 스택 (현행)

| 영역 | 도구 | 라이센스 |
|------|------|---------|
| 시뮬레이터 | MuJoCo 3.8 (Apple Silicon 네이티브) | Apache 2.0 |
| 로봇 모델 | TheRobotStudio SO-ARM101 MJCF | CC-BY-SA |
| 학습 프레임워크 | HuggingFace LeRobot | Apache 2.0 |
| 학습 알고리즘 | ACT (Action Chunking Transformer) | MIT |
| AI 에이전트 | Hermes Agent (자체 운영) | — |
| 백엔드 모델 (일상) | Google Gemini 2.5 Flash | 무료 |
| 백엔드 모델 (복잡 추론) | **Claude (본 기안 대상)** | 유료 |
| 추론 타겟 (차년도) | NVIDIA Orin Nano Super | — |
