CoP Physical AI 일일 보고 메일을 작성하고 발송해주세요.

## 수신자
- xaqwer@gmail.com
- insoo.kum@hyundaielevator.com
- giheon.jang@hyundaielevator.com

## GitHub 레포
https://github.com/kiheon-jang/2026-cop-physical-ai

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"

## 수집할 정보
1. 최신 커밋 이력 (어제 날짜 기준): gh api repos/kiheon-jang/2026-cop-physical-ai/commits?per_page=10
2. research/drafts/ 또는 latest-tech/ 신규 파일 내용
3. samples/SAMPLE_STATUS.md 현황
4. docs/05_data-collection/TRACKING.md 수집 현황
5. research/decisions/README.md 검토 대기 항목 전체

## 메일 본문 규칙
- ASCII 특수문자(┌┐└┘━╌ 등) 절대 사용 금지 — 메일 클라이언트에서 깨짐
- 구분선은 반드시 하이픈(-)만 사용: ----------------------------------------
- 섹션 헤더는 대괄호+이모지: [섹션명]
- 들여쓰기는 스페이스 2칸
- 링크는 줄바꿈 후 별도 행에 단독 표시

## 메일 본문 형식 (아래 형식 그대로 작성)

---

제목: [CoP Physical AI] 일일 연구 보고 Vol.XXX | YYYY-MM-DD

============================================================
🤖  CoP Physical AI  |  일일 연구 보고  |  Vol.XXX
    YYYY년 MM월 DD일 (요일)  |  Powered by AI Research Agent
============================================================

GitHub 바로가기:
https://github.com/kiheon-jang/2026-cop-physical-ai

------------------------------------------------------------
[1] 어제 완료한 작업
------------------------------------------------------------

[커밋 목록 기반으로 번호 매겨서 작성. 없으면 "어제 작업 없음"]

예시:
  1. [리서치] ACT vs Diffusion Policy 벤치마크 초안 작성
     파일: research/drafts/2026-04-21_act-comparison.md

  2. [샘플] 모터 기본 제어 단위테스트 작성 (전체 PASS)
     파일: samples/unit/test_follower_basic.py

------------------------------------------------------------
[2] 이슈 / 문제점
------------------------------------------------------------

[미해결 이슈 작성. 없으면 "현재 이슈 없음"]

------------------------------------------------------------
[3] 데이터 수집 현황
------------------------------------------------------------

  목표:  50 에피소드
  현재:  XX 에피소드  (XX%)
  진행:  [===>      ]  (X/10 구간 표시, = 1칸 = 5 에피소드)

  다음 마일스톤: 10 에피소드 달성시 -> ACT 중간 학습 테스트

------------------------------------------------------------
[4] 팀 요청사항  (Action Required)
------------------------------------------------------------

[TRACKING.md 미완 항목 + decisions 검토대기 기반으로 작성. 반드시 담당자 명시]

  [ ] [장기헌] 데이터 수집 진행 필요 (현재 X/50)
  [ ] [전체]   ACT vs Diffusion Policy 학습 정책 결정 필요

  -- 결정 대기 항목 --
  [보류] ACT vs Diffusion Policy  ->  첫 학습 정책 선택
  [보류] Isaac Sim vs Isaac Lab   ->  시뮬레이터 선택
  [보류] LeKiwi vs XLeRobot      ->  모바일 플랫폼 선택
  [보류] 카메라 업그레이드 여부    ->  예산 확인 필요
  [research/decisions/ 에서 추가 항목 있으면 모두 나열]

------------------------------------------------------------
[5] 오늘의 기술 리서치
------------------------------------------------------------

[research/drafts/ 또는 latest-tech/ 신규 파일 내용을 아래 형식으로 요약]
[없으면 "오늘 리서치 결과 없음 (내일 예정)"]

  주제: [리서치 주제명]
  상태: 초안 / 확정본

  한줄 요약:
    [핵심을 한 문장으로 — 누구나 이해 가능하게]

  핵심 개념 3가지:
    1. [개념명]
       [쉬운 설명 — 초심자 기준]

    2. [개념명]
       [쉬운 설명]

    3. [개념명]
       [쉬운 설명]

  우리 프로젝트에서 왜 중요한가:
    [SO-ARM101 / LeRobot 맥락에서 1~2문장]

  더 읽어보기:
    [링크]

------------------------------------------------------------
[6] 샘플코드 현황
------------------------------------------------------------

  [이번주 추가/변경된 샘플 목록. SAMPLE_STATUS.md 기준]

  완성 (별3):
    - test_follower_basic.py     모터 6개 ID/각도 범위 검증
    - test_data_pipeline.py      데이터 수집 파이프라인 구조 검증

  기본완성 (별2):
    - run_connection_check.py    하드웨어 연결 상태 전체 확인

  작성중:
    - [해당 파일 목록. 없으면 생략]

  코드 리뷰 포인트:
    [이번주 작성된 샘플 중 주목할 구현 방식, 개선점, 초심자가 배울 수 있는 패턴 1~2개]

------------------------------------------------------------
[7] 경로 및 구조 변경사항
------------------------------------------------------------

[어제 커밋에서 파일 이동/추가/삭제 등 구조 변경이 있었으면 기술. 없으면 "변경 없음"]

예시:
  추가: research/drafts/  (초안 보관 폴더 신설)
  이동: 산출물/ -> archive/산출물/  (Obsidian 원본 아카이브)
  추가: AGENT_PROCESS.md  (AI 운영 가이드)

------------------------------------------------------------
[8] 내일 예정
------------------------------------------------------------

  23:00  [리서치]   [내일 요일 기준 주제명]
  23:30  [샘플]     [내일 요일 기준 샘플명]
  07:00  [보고]     일일 보고 메일 발송

------------------------------------------------------------
[9] 빠른 링크
------------------------------------------------------------

  전체 레포:
    https://github.com/kiheon-jang/2026-cop-physical-ai

  단계별 문서:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/docs

  샘플코드:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/samples

  리서치 확정본:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/research/latest-tech

  리서치 초안:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/research/drafts

  결정 로그:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/research/decisions

  데이터 수집 현황:
    https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/docs/05_data-collection/TRACKING.md

  샘플 완성도:
    https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/samples/SAMPLE_STATUS.md

  원본 노트:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/archive

============================================================
본 메일은 CoP AI Research Agent 가 매일 오전 7시에 자동 발송합니다.
문의: xaqwer@gmail.com (장기헌)
============================================================

---

## 발송 명령어
gsk vm_email send "xaqwer@gmail.com" \
  -s "[CoP Physical AI] 일일 연구 보고 Vol.XXX | YYYY-MM-DD" \
  -b "<본문>" \
  -f $OPENCLAW_VM_NAME

gsk vm_email send "insoo.kum@hyundaielevator.com" \
  -s "[CoP Physical AI] 일일 연구 보고 Vol.XXX | YYYY-MM-DD" \
  -b "<본문>" \
  -f $OPENCLAW_VM_NAME

gsk vm_email send "giheon.jang@hyundaielevator.com" \
  -s "[CoP Physical AI] 일일 연구 보고 Vol.XXX | YYYY-MM-DD" \
  -b "<본문>" \
  -f $OPENCLAW_VM_NAME

3명 모두 발송 후 결과 알려주세요.
