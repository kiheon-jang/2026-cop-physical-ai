CoP Physical AI 일일 보고 메일을 작성하고 발송해주세요.

## 수신자
- xaqwer@gmail.com
- insoo.kum@hyundaielevator.com
- giheon.jang@hyundaielevator.com

## GitHub 레포
https://github.com/kiheon-jang/2026-cop-physical-ai

## 사전 준비
git config --global url."https://$(gh auth token)@github.com/".insteadOf "https://github.com/"
cd /Users/markmini/Documents/dev/2026-cop-physical-ai && git pull origin main

## 수집할 정보
1. 최신 커밋 이력 (어제 날짜 기준): gh api repos/kiheon-jang/2026-cop-physical-ai/commits?per_page=10
2. agent/research-log/YYYY-MM-DD.md (어제 시뮬 진행 기록)
3. research/simulation/ 신규 파일 (단계별 환경 구축 기록)
4. agent/external-dependencies.md (외부 의존 항목 — [4-A] 섹션의 원천 데이터)
5. agent/report-evidence/2026-MM/INDEX.md (보고용 증거 후보)
6. samples/SAMPLE_STATUS.md (시뮬/학습 스크립트 현황)

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
    YYYY년 MM월 DD일 (요일)  |  Powered by Hermes Agent (Mac Mini M5)
============================================================

GitHub 바로가기:
https://github.com/kiheon-jang/2026-cop-physical-ai

------------------------------------------------------------
[0] 한 줄 요약
------------------------------------------------------------

[오늘의 핵심 진척을 한 문장으로]
예시: "MuJoCo 시뮬에 SO-ARM101 6-DoF 모델 import 완료, viewer 동작 확인."

------------------------------------------------------------
[1] 어제 완료한 작업
------------------------------------------------------------

[커밋 목록 + agent/research-log/ 기반으로 번호 매겨 작성. 없으면 "어제 작업 없음"]

예시:
  1. [시뮬] SO-ARM100 MJCF 모델 다운로드 + 뷰어 동작 확인
     파일: research/simulation/01_mujoco-setup.md
     커밋: a1b2c3d

  2. [샘플] 자동 데이터 수집 스크립트 v0.1
     파일: samples/training/sim_data_collector.py
     실행 결과: 10 에피소드 합성 성공 (평균 3.2초/에피소드)

------------------------------------------------------------
[2] 이슈 / 문제점
------------------------------------------------------------

[미해결 이슈 작성. 없으면 "현재 이슈 없음"]

예시:
  - MuJoCo viewer가 macOS에서 OpenGL 에러 발생
    원인: Apple Silicon Metal 드라이버 호환성
    해결 시도: mjpython 사용 (해결 완료) 또는 EGL backend
    영향: 하루 지연 가능

------------------------------------------------------------
[3] 시뮬 환경 진행도
------------------------------------------------------------

  현재 단계:  Phase X - [Phase 이름]
  주차:       WX (M/D ~ M/D)
  이번주 목표: [W 목표 한 문장]

  진행률:    [===>      ]  XX%  (X/10 작업 완료)

  완료:
    [v] [작업명]
    [v] [작업명]

  진행중:
    [ ] [작업명] - [현재 상태]

  다음 마일스톤:
    M/D — [마일스톤명]

  핵심 메트릭 (있으면):
    - 시뮬 Pick 성공률: XX%
    - 추론 속도: XX ms
    - 시뮬-실기 관절각 오차: ±X.X°
    - 학습 손실 (epoch X): X.XXX

  보고용 매핑:
    -> M월 보고서 [2.X] 섹션 증거로 활용 가능

------------------------------------------------------------
[4] 의사결정 대기 항목
------------------------------------------------------------

[research/decisions/ 의 미결 항목. 없으면 "결정 대기 항목 없음"]

  [보류] [결정 항목명]  ->  [선택지 요약]
         담당: [담당자]
         마감: YYYY-MM-DD

------------------------------------------------------------
[4-A] 외부 의존 / 사용자 수동 작업 필요  ★중요★
------------------------------------------------------------

  Mac Mini Hermes가 단독으로 처리할 수 없는 항목.
  실기 옆 작업자/다른 머신/사용자 수동 처리 필요.
  원천 파일: agent/external-dependencies.md

  [agent/external-dependencies.md 의 "진행중" 항목 전체를
   우선순위 + 담당 + 마감일 + 사유 포함하여 그대로 옮김]

  예시:
  [ ] [실기 담당] 웹캠 캘리브레이션값 측정
      마감: 2026-05-14 (Phase 0 W2 차단)
      필요 정보: 해상도, FOV, 작업대 대비 위치
      방법: docs/02_hardware/CAMERA_CALIBRATION.md 참조

  [ ] [전체] MuJoCo 사내 사용 라이선스 확인
      마감: 2026-05-03

  완료 처리 방법:
    agent/external-dependencies.md 에서 [ ] -> [v] 변경 후 commit

------------------------------------------------------------
[5] 오늘의 시뮬 진척
------------------------------------------------------------

[research/simulation/ 또는 agent/research-log/ 신규 파일 요약]
[없으면 "오늘 진척 없음 (내일 예정)"]

  주제: [작업명]
  단계: Phase X - WX

  한줄 요약:
    [핵심을 한 문장으로 — 비전공자도 이해 가능하게]

  핵심 작업 3가지:
    1. [작업명]
       [무엇을 했는지 + 왜 필요했는지]

    2. [작업명]
       [무엇을 했는지]

    3. [작업명]
       [무엇을 했는지]

  최종 목표(10월 시연)와의 연결:
    [PCB 조정 / RS232 결선 시연으로 어떻게 이어지는지 1~2문장]

  코드/문서:
    [GitHub 링크]

------------------------------------------------------------
[6] 시뮬/학습 스크립트 현황
------------------------------------------------------------

  [SAMPLE_STATUS.md 기준. 이번주 추가/변경 파일]

  완성 (별3 - 전체 PASS):
    - [파일명]    [기능 1줄 설명]

  기본완성 (별2 - 일부 PASS):
    - [파일명]    [기능 1줄 설명]

  작성중:
    - [파일명]    [현재 상태]

  코드 리뷰 포인트:
    [이번주 작성된 코드 중 주목할 패턴 또는 개선점 1~2개]

------------------------------------------------------------
[7] 경로 및 구조 변경사항
------------------------------------------------------------

[어제 커밋에서 파일 이동/추가/삭제 등 구조 변경. 없으면 "변경 없음"]

------------------------------------------------------------
[8] 내일 예정
------------------------------------------------------------

  23:00  [시뮬 구축]    [내일 단계 작업명]
  23:30  [시뮬 테스트]  [내일 테스트 항목]
  07:00  [보고]        일일 보고 메일 발송

------------------------------------------------------------
[9] 빠른 링크
------------------------------------------------------------

  전체 레포:
    https://github.com/kiheon-jang/2026-cop-physical-ai

  AGENT_PROCESS (운영 가이드):
    https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/AGENT_PROCESS.md

  시뮬 환경 구축 기록:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/research/simulation

  매일 진행 로그:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/agent/research-log

  외부 의존 항목:
    https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/agent/external-dependencies.md

  보고용 증거 인덱스:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/agent/report-evidence

  결정 로그:
    https://github.com/kiheon-jang/2026-cop-physical-ai/tree/main/research/decisions

  샘플코드 현황:
    https://github.com/kiheon-jang/2026-cop-physical-ai/blob/main/samples/SAMPLE_STATUS.md

============================================================
본 메일은 CoP Hermes Agent 가 Mac Mini M5에서 매일 오전 7시에 자동 발송합니다.
시뮬레이터: MuJoCo 3.x (Apple Silicon 네이티브)
문의: xaqwer@gmail.com (장기헌)
============================================================

---

## 발송 명령어

scripts/daily-report/generate_daily_report.py 실행 (Hermes가 자동 호출).
직접 발송 시:

```bash
cd /Users/markmini/Documents/dev/2026-cop-physical-ai
python3 scripts/daily-report/generate_daily_report.py
```

3명 모두 발송 후 결과 알려주세요.
