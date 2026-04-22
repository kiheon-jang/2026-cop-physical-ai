# 크론 작업 전체 명세 (Cron Jobs)

> 이 문서는 OpenClaw 플랫폼에 등록된 **CoP Physical AI 자동화 크론 전체**를 서술합니다.  
> 다른 플랫폼으로 이전 시 이 문서를 기준으로 재등록하세요.

---

## 전체 크론 목록

| ID | 이름 | 스케줄 (KST) | 목적 | 상태 |
|----|------|------------|------|------|
| `dc257031` | 일일 리서치 초안 | 매일 23:00 | research/drafts/ 에 초안 생성 | ✅ 활성 |
| `b2e623a4` | 일일 샘플코드 | 매일 23:30 | samples/ 에 코드 생성 + SAMPLE_STATUS 업데이트 | ✅ 활성 |
| `dcbf84a5` | 일일 보고 메일 | 매일 07:00 | HTML 메일 3명 발송 | ✅ 활성 |
| `ed5aff22` | 주간 검수 | 매주 일요일 22:00 | drafts→latest-tech 이동, 샘플 재검증 | ✅ 활성 |
| `20ee15d4` | Isaac Sim 조사 | 2026-04-22 23:00 (1회) | docs/07_simulation-rl/ 작성 | ✅ 1회성 |

---

## 크론 1 — 일일 리서치 초안

```
ID       : dc257031-a547-45e8-8d83-4c32447a79e1
이름     : CoP Physical AI — 일일 리서치 초안 (drafts)
스케줄   : 0 23 * * *  (KST, 매일 23:00)
타입     : agentTurn / isolated 세션
timeout  : 600초
딜리버리 : announce
```

### 페이로드 (전체)

```
CoP Physical AI 일일 리서치 초안 작업을 수행해주세요.

## GitHub 레포
https://github.com/kiheon-jang/2026-cop-physical-ai

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
git clone https://github.com/kiheon-jang/2026-cop-physical-ai.git /tmp/cop-repo || (cd /tmp/cop-repo && git pull)
cd /tmp/cop-repo

## 저장 위치
`research/drafts/` 폴더 (확정본 아님 — 주간 검수 후 latest-tech/로 이동)

## 요일별 주제 순환
- 월: ACT vs Diffusion Policy vs π0 최신 벤치마크 비교
- 화: Isaac Lab / Isaac Sim 강화학습 최신 동향
- 수: Sim2Real 격차 해소 최신 기법
- 목: VLA(Vision-Language-Action) 모델 최신 논문
- 금: 모방학습 데이터 효율화 기법
- 토: LeRobot 커뮤니티 최신 업데이트
- 일: 경쟁사/유사 프로젝트 동향 (SO-ARM, LeKiwi, XLeRobot)

## 파일 형식 (CONTRIBUTING.md 기준)
```
# [주제명]

> 작성일: YYYY-MM-DD | 상태: 초안 (검수 전)

## 💡 한 줄 요약
[핵심을 한 문장으로]

## 🔑 핵심 개념
1. [개념]: [쉬운 설명]
2. [개념]: [쉬운 설명]
3. [개념]: [쉬운 설명]

## 📊 왜 우리 프로젝트에 중요한가
[SO-ARM101/LeRobot 맥락에서 설명]

## 🔍 상세 내용
[gsk search 결과 기반 상세 내용]

## 🔗 출처
- [링크1]
- [링크2]
```

## 작업 순서
1. 오늘 요일 확인 후 해당 주제 선택
2. `gsk search`로 최신 정보 검색 (2025~2026 중심)
3. 위 형식으로 `research/drafts/YYYY-MM-DD_<주제-kebab>.md` 작성
4. research/CHANGELOG.md 에 `- 📋 [초안] <파일명>` 추가
5. git add/commit/push
   - 커밋: `🔬 [draft] <주제> — YYYY-MM-DD`

완료 후 결과 요약해주세요.
```

---

## 크론 2 — 일일 샘플코드

```
ID       : b2e623a4-bc6a-4f16-b53d-50437c2dc1ae
이름     : CoP Physical AI — 일일 샘플코드 (B)
스케줄   : 30 23 * * *  (KST, 매일 23:30)
타입     : agentTurn / isolated 세션
timeout  : 600초
딜리버리 : announce
```

### 페이로드 (전체)

```
CoP Physical AI 일일 샘플코드 작업을 수행해주세요.

## GitHub 레포
https://github.com/kiheon-jang/2026-cop-physical-ai

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
git clone https://github.com/kiheon-jang/2026-cop-physical-ai.git /tmp/cop-repo || (cd /tmp/cop-repo && git pull)
cd /tmp/cop-repo

## 요일별 샘플 순환
- 월: samples/training/test_act_training.py
- 화: samples/training/test_diffusion_training.py
- 수: samples/inference/test_inference_pipeline.py
- 목: samples/data-collection/test_episode_quality.py
- 금: samples/motor-control/test_torque_limit.py
- 토: samples/training/test_hyperparameter_search.py
- 일: samples/inference/test_camera_pipeline.py

## 작성 방침 (CONTRIBUTING.md 기준)
- 하드웨어 없이 실행 가능한 단위테스트 중심
- lerobot 미설치 시 명확한 에러 메시지 출력
- 코드 실제 실행하여 전체 PASS 확인
- 함수/클래스 docstring 작성
- 실행 방법 주석 작성

## SAMPLE_STATUS.md 업데이트
코드 작성 후 samples/SAMPLE_STATUS.md 에 해당 파일 상태 업데이트:
- 전체 PASS → '✅ 완성 | ⭐⭐⭐ | YYYY-MM-DD'
- 일부 PASS → '✅ 기본완성 | ⭐⭐ | YYYY-MM-DD'

## 작업 순서
1. 오늘 요일 확인 후 해당 샘플 선택
2. 해당 파일이 이미 있으면 기능 보완, 없으면 신규 작성
3. `python3 <파일>` 실행하여 PASS 확인
4. SAMPLE_STATUS.md 업데이트
5. git add/commit/push
   - 커밋: `💻 [샘플] <설명> — YYYY-MM-DD`

완료 후 결과 요약해주세요.
```

---

## 크론 3 — 일일 보고 메일

```
ID       : dcbf84a5-16f7-498a-b925-2e8e46b6ad75
이름     : CoP Physical AI — 일일 보고 메일
스케줄   : 0 7 * * *  (KST, 매일 07:00)
타입     : agentTurn / isolated 세션
timeout  : 600초
딜리버리 : announce → genspark-im (owner uid: 3474cd39-6c36-44d5-aaaa-f0d18fc56155)
```

### 수신자

| 이름 | 이메일 |
|------|--------|
| 장기헌 | xaqwer@gmail.com |
| 금인수 | insoo.kum@hyundaielevator.com |
| 장기헌(현대) | giheon.jang@hyundaielevator.com |

### 페이로드 (전체)

```
CoP Physical AI 일일 보고 HTML 메일을 작성해서 3명에게 발송해주세요.

## 수신자
- xaqwer@gmail.com
- insoo.kum@hyundaielevator.com
- giheon.jang@hyundaielevator.com

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
cd /home/work/.openclaw/workspace/2026-cop-physical-ai
git pull origin main

## Vol 번호 계산
- 프로젝트 시작일: 2026-04-21 (Vol.001)
- 오늘 날짜 기준으로 자동 계산: Vol.N = (오늘 KST날짜 - 2026-04-20)일수
- 예) 2026-04-22 → Vol.002, 2026-04-23 → Vol.003

## 수집할 정보
# 어제 커밋 이력 (최근 10개)
gh api "repos/kiheon-jang/2026-cop-physical-ai/commits?per_page=10" --jq '.[].commit.message'
# 샘플 현황
cat samples/SAMPLE_STATUS.md
# 데이터 수집 현황
cat docs/05_data-collection/TRACKING.md
# 결정 대기 항목
cat research/decisions/README.md
# 오늘 리서치 초안 (있으면)
ls research/drafts/ | tail -3

## 메일 본문 생성 방법
1. `/home/work/.openclaw/workspace/2026-cop-physical-ai/docs/01_overview/mail-template.html` 파일을 읽어서 기반으로 사용
2. 아래 항목을 실제 데이터로 교체:
   - Vol.XXX → 계산된 Vol 번호
   - YYYY-MM-DD (요일) → 오늘 KST 날짜
   - [1] 어제 완료한 작업 → 실제 커밋 목록 (없으면 "어제 작업 없음")
   - [3] 데이터 수집 현황 → TRACKING.md 실제 수치
   - [5] 오늘의 기술 리서치 → research/drafts/ 신규 파일 내용 (없으면 "오늘 리서치 결과 없음")
   - [6] 샘플코드 현황 → SAMPLE_STATUS.md 실제 현황
   - [7] 경로 및 구조 변경사항 → 오늘 커밋의 파일 변경 (없으면 "변경 없음")
   - [8] 내일 예정 → 내일 요일 기준 크론 스케줄
3. 결정 대기 항목: research/decisions/ 파일 기준으로 결정된 항목은 ✅ 결정완료, 나머지는 ⏳ 대기중
4. 결정 폼 링크 고정: https://ookixght.gensparkclaw.com/decisions.html

## 발송 명령어
SUBJECT="[CoP Physical AI] 일일 연구 보고 Vol.XXX | YYYY-MM-DD"

gsk vm_email send "xaqwer@gmail.com" -s "$SUBJECT" -b "$HTML_BODY" -f $OPENCLAW_VM_NAME
gsk vm_email send "insoo.kum@hyundaielevator.com" -s "$SUBJECT" -b "$HTML_BODY" -f $OPENCLAW_VM_NAME
gsk vm_email send "giheon.jang@hyundaielevator.com" -s "$SUBJECT" -b "$HTML_BODY" -f $OPENCLAW_VM_NAME

3명 모두 발송 성공 여부를 확인하고 결과를 알려주세요.
```

---

## 크론 4 — 주간 검수

```
ID       : ed5aff22-b927-4655-9dfd-cb659a116067
이름     : CoP Physical AI — 주간 검수 + 최신화
스케줄   : 0 22 * * 0  (KST, 매주 일요일 22:00)
타입     : agentTurn / isolated 세션
timeout  : 900초
딜리버리 : announce
```

### 페이로드 (전체)

```
CoP Physical AI 주간 검수 + 최신화 작업을 수행해주세요.

## GitHub 레포
https://github.com/kiheon-jang/2026-cop-physical-ai

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
git clone https://github.com/kiheon-jang/2026-cop-physical-ai.git /tmp/cop-repo || (cd /tmp/cop-repo && git pull)
cd /tmp/cop-repo

## 작업 1: research/drafts/ 검수
1. drafts/ 전체 파일 목록 확인
2. 각 파일에 대해 CONTRIBUTING.md 기준으로 품질 판단:
   - ✅ 통과: latest-tech/로 이동 (git mv)
   - ❌ 미달: 상단에 `> ⚠️ 보완 필요: [이유]` 주석 추가 후 유지
3. 파일 이동 시 내부 `상태: 초안 (검수 전)` → `상태: 확정본` 수정

## 작업 2: latest-tech/ 최신성 확인
1. latest-tech/ 전체 파일 목록 확인
2. 작성일이 6개월 이상 된 파일:
   - gsk search로 해당 주제 갱신 정보 수집
   - 갱신사항 없으면 상단에 `> ⚠️ DEPRECATED: YYYY-MM-DD 이후 내용 확인 필요` 표시
   - 갱신사항 있으면 내용 갱신 후 작성일 업데이트

## 작업 3: SAMPLE_STATUS.md 전체 업데이트
1. samples/ 의 모든 .py 파일 목록 확인
2. 각 파일 python3 실행 시도
3. SAMPLE_STATUS.md 업데이트 (실행 결과 + 날짜)
4. 실행 안 되는 파일 → 상태를 '❌ 실행오류'로 표시

## 작업 4: AGENT_PROCESS.md 확인
- '현재 미완료 / 진행 중 작업' 테이블 업데이트
- 변경 이력에 이번 주 주간검수 결과 추가

## 작업 5: research/CHANGELOG.md 업데이트
### YYYY-MM-DD (주간검수)
- ✅ [확정] <파일명> — drafts/ → latest-tech/
- 🔄 [갱신] <파일명> — 내용 최신화
- ⚠️ [DEPRECATED] <파일명> — 이유

## 커밋 & 푸시
git add -A
git commit -m '🔄 [주간검수] YYYY-MM-DD 주간 정리'
git push origin main

완료 후 주간 검수 결과 요약 (drafts 이동 수, DEPRECATED 수, 샘플 업데이트 수)를 알려주세요.
```

---

## 크론 5 — Isaac Sim 조사 (1회성)

```
ID       : 20ee15d4-be21-48a2-be33-2308339946f5
이름     : CoP Physical AI — Isaac Sim 사전 조사
스케줄   : 2026-04-22T14:00:00Z (KST 23:00, 1회 후 자동 삭제)
타입     : agentTurn / isolated 세션
timeout  : 900초
딜리버리 : announce
```

### 산출물

- `docs/07_simulation-rl/README.md` — 시뮬레이터 비교 조사 결과
- `research/decisions/YYYY-MM-DD_simulator-selection.md` — 시뮬레이터 결정 로그

### 페이로드 요약

Isaac Sim 4.x 시스템 요구사항 vs Orin Nano Super 스펙 비교, Isaac Lab/MuJoCo 대안 검토, LeIsaac/GR00T 연동 가능성, 클라우드 대안(비용) 조사.

---

## 새 플랫폼에서 크론 재등록 방법

다른 AI 에이전트 플랫폼으로 이전 시 아래 방식으로 재등록:

```bash
# OpenClaw 환경이라면
openclaw cron add \
  --name "CoP Physical AI — 일일 리서치 초안" \
  --schedule "0 23 * * *" \
  --tz "Asia/Seoul" \
  --message "<위 페이로드 전체>" \
  --timeout 600

# 또는 크론 표현식 직접 등록
# cron.add() API 사용 시 agent/cron-jobs.md 페이로드를 그대로 message 필드에 삽입
```

> ⚠️ OpenClaw 외 플랫폼에서는 별도 스케줄러(GitHub Actions, n8n, crontab 등)로 대체 필요.
