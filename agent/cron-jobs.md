# 🕐 크론 작업 페이로드 (cron-jobs.md)

> **Hermes Agent (Mac Mini M5) 의 크론 4개 완전 서술**
> 다른 환경으로 이전 시 이 파일의 페이로드를 참고하여 재등록.
> **최종 업데이트**: 2026-05-22 (스킬 필드 수정 + 크론 3 동작 설명 갱신)

---

## 🌐 환경

- **플랫폼**: Hermes Agent (로컬 Mac Mini M5, 24/7 운영)
- **시간 기준**: KST (Asia/Seoul)
- **저장소**: GitHub `kiheon-jang/2026-cop-physical-ai` + Obsidian Vault
- **이전**: OpenClaw → Hermes (2026-04-29 완료), 시뮬 트랙 전환 (2026-05-01)
- **레거시 ID**: dc257031, b2e623a4, dcbf84a5, ed5aff22, 20ee15d4 (모두 폐기)

---

## 🔁 시뮬 파이프라인 드라이버 (2026-06-24 신규 — 핵심)

야간 cron 의 본업 = **시뮬 파이프라인을 매일 한 칸씩 전진**. 이걸 LLM(self-heal) 판단에 맡기면
"고칠 것 없음 → 침묵"으로 멈춘다(2026-06-24 실제 발생: 밤 잡 SILENT → 아침 메일 빔).
그래서 **결정론적 드라이버**가 전진을 담당하고, LLM self-heal 은 "진짜 에러"만 보조한다.

```
scripts/cop_pipeline_advance.sh   ← 야간 cron(self-heal 스킬 §0)이 매 실행 첫 액션으로 호출
```
상태머신(1회 1단계, 장시간작업은 nohup 백그라운드):
1. 수집 진행중 → 보고   2. 학습 진행중 → check_act_train.sh
3. 데이터<50ep → `cop_start_data_collect.sh`(closed-loop 수집)
4. 데이터 준비 & 미학습 → `start_act_train.sh`(COP_DATASET_ROOT=data/episodes_cl)
5. 학습완료 & 미측정 → `render_act_rollout.py`
6. 측정완료 → 수렴 판정

- **S1(episodes_s1) 분기 추가(2026-08-06, W3 후)**: `DS_BASE==episodes_s1` 이면 IS_S1=1 →
  ckpt=`checkpoints/act_s1_sim`(규칙상 act_s1 아님·수동 학습 경로), 측정=`render_act_rollout_s1.py`
  (LED latch 4-seed), 학습 env=COP_CAMERA_KEYS=top,closeup + COP_DATASET_REPO_ID=local/pcb_reset_sim,
  수집 스테이지=보류(합성 데이터 고정 100ep — pick-place 수집기로 채우면 오염). S1 은 데이터·모델이
  이미 완성이라 정상 흐름 = **stage5 측정 1회 → stage6 완료/유지**(마커 `episodes_s1:<sig>` 사전 세팅으로
  재학습 방지 = epoch_0029 보호). 실측 = 4-seed 공정추정 0.925.
- 네이밍: 전부 `cop_` 접두(다른 프로젝트 잡과 격리). pid/log: `logs/cop_*`.
- 데이터: **현재 타겟 `data/episodes_s1`(S1 리셋버튼, 2026-08-06 전환)**. 이전 `episodes_cl`/`episodes_floor` 보존.
- **연결(2026-06-24 통합)**: 23:00 CoP 작업 크론(`--no-agent`, script=`cop_sim_env.py`)이 **git_pull 직후 이 드라이버를 직접 호출**한다. Claude 위임은 그 결과 문서화/보고/self-heal 만(파이프라인 재실행 X). 별도 크론·스킬 없음 → 충돌 0.
  검증(`cop_sim_env.py --pipeline-only`): git_pull_ok → STAGE=학습시작 → 학습 진행(loss 하강) 확인됨.
- 출력 `STAGE=...` 상태블록 → research-log + 아침 메일에 append → "메일 빔" 재발 방지.

> **실제 CoP 크론 (라이브 jobs.json, 2026-06-24 확인)** — 본 문서의 옛 ID(9ad85007cf27 등)는 stale:
> - `76b3cd4eb4fc` 23:00 "시뮬 환경 구축" (script `cop_sim_env.py`, --no-agent) ← 작업 본진
> - `f88b3198c9b6` 23:30 "시뮬 테스트 + 메트릭"
> - `b76453176bb4` 01:00 "야간 잡 실패 재시도"   · `fb6d7cb26650` 07:00 "아침 보고 메일"
> - 04:30(7adc5a1b580d)은 **Hermes Common(타 프로젝트)** — CoP 아님.
>
> **"메일 빔" 진짜 원인(2026-06-24)**: cop_sim_env.py 의 `git pull` 이 로컬↔origin **분기(divergent)** 로
> exit 1 → 매일 그 자리서 종료. **수정**: `git config pull.rebase false` + autoStash → 분기 시 자동 머지.
>
> **아침 메일 안 옴(2026-06-25) 2중 버그 + 수정**:
> 1. 메일 잡(fb6d7cb26650)이 **toolset 없는 agent** 라 gemini 가 보고 스크립트를 못 돌림(tool_turns=0) → 발송 0.
>    **수정**: `no_agent` 결정론 스크립트로 전환 — `~/.hermes/scripts/cop_daily_report.py`(git pull→generate_daily_report.py).
>    `hermes cron edit fb6d7cb26650 --no-agent --script cop_daily_report.py`. (23:00 cop_sim_env.py 와 동일 패턴.)
> 2. `generate_daily_report.py::_check_upstream_failures` 가 **23:00 야간잡을 "오늘 실행" 아니라고 오판**(어젯밤 실행이라)
>    → 보고 대신 알림 발송. **수정(커밋)**: 최근 30h 내 성공이면 정상.
> ⚠ **발송 대상**: `~/.hermes/.env` `EMAIL_TEST_MODE=false` → **3명 전체 발송**. 본인만 원하면 `true`.
>
> ⚠ **후속(측정 스테이지 5)**: `render_act_rollout.py` 정합은 학습 후처리(위 측정기 커밋으로 코드는 정합 완료, 실측 대기).

---

## 📋 크론 1 — 시뮬 환경 단계별 구축 (MuJoCo)

```
ID       : 9ad85007cf27
이름     : CoP Physical AI — 시뮬 환경 단계별 구축 (MuJoCo)
스케줄   : 0 23 * * *  (매일 23:00 KST)
타임아웃 : 600초
스킬     : cop-physical-ai-self-heal
변경이력 : terminal/file/web → cop-physical-ai-self-heal (2026-05-22, Hermes v0.13.0 이후 오탐 수정)
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
스킬     : cop-physical-ai-self-heal
변경이력 : terminal/file → cop-physical-ai-self-heal (2026-05-22)
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
스킬     : (없음 — 스크립트 방식)
스크립트 : scripts/daily-report/generate_daily_report.py
변경이력 : terminal/file/web/send_message 스킬 제거 (2026-05-22), 스크립트 직접 실행 방식
```

### 동작 (2026-05-22 현재)

- `scripts/daily-report/generate_daily_report.py` 실행 (`.venv/bin/python3`)
- 어제 GitHub 커밋 + `agent/research-log/` + `agent/external-dependencies.md` 수집
- Gemini API로 비전공자 친화적 `오늘의 한 줄` 자동 생성
- HTML 이메일 생성 → **4명 발송**: xaqwer@gmail.com, insoo.kum@hyundaielevator.com, giheon.jang@hyundaielevator.com, kimeun091473@gmail.com
- **메일 발송 후 자동**: `research/CHANGELOG.md` 어제 커밋 항목 추가 + `README.md` 현황 업데이트 + git push

---

## 📋 크론 4 — 주간 정리 + 보고용 증거 식별

```
ID       : 0b1d4a7b2bf7
이름     : CoP Physical AI — 주간 정리 + 보고용 증거 식별
스케줄   : 0 22 * * 0  (매주 일요일 22:00 KST)
타임아웃 : 600초
스킬     : (없음)
변경이력 : terminal/file/web 제거 (2026-05-22)
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

## 2026-07-06 — rebuild_dashboard_data 풀빌드 전환 (R4 인터랙티브 보고)

`~/.hermes/scripts/cop_common.py::rebuild_dashboard_data` 변경 (hermes 업데이트로 유실 시 재적용):
- `["python3", build.py, "--json-only"]` → **레포 `.venv/bin/python3` 로 `build.py` 풀빌드**(HTML+JSON), cwd=`dashboard/`, timeout 60→180.
- 사유: R4 빌더(`build_web3d`/`build_dr_gallery`)가 pyarrow/PIL(.venv 전용) 사용 + 오프라인 단일파일(dashboard.html)도 매일 신선해야 함.
- 파이프라인 데이터셋 타겟은 `logs/cop_dataset_target` 파일 (**현재 `data/episodes_s1`**, 2026-08-06 S1 전환). 마커 형식 `"<ds>:<sig>"` — 상세 `research/simulation/2026-07-06_phase2-w1-pipeline-audit-dr-retrain-trigger.md`.
