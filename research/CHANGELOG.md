# 리서치 갱신 이력 (CHANGELOG.md)

> 리서치 파일의 생성, 검수 통과, 갱신, 삭제 이력을 추적합니다.

---

## 형식

```
### YYYY-MM-DD
- ✅ [확정] <파일명> — drafts/ → latest-tech/ 이동
- 🔄 [갱신] <파일명> — 내용 최신화
- 🗑️ [삭제] <파일명> — 이유
- 📋 [초안] <파일명> — drafts/ 생성
```

---

## 이력

































### 2026-07-09
- 📊 [로그] 2026-07-09 시뮬 테스트 — 우선순위 4종 회귀 PASS(3/3·3/3·데모0/3·수집2/2 yield100%) + floor 재학습 pid21661 ep5 관찰(무결성 무손상)
- 🛠 [시뮬] floor 재학습 재시도 + DataLoader FD 누수 자가치유(persistent_workers) — 2026-07-09
- 📝 [히스토리] 2026-07-08 작업 기록 + README 현황 업데이트 — 2026-07-09

### 2026-07-08
- 📊 [로그] 2026-07-08 시뮬 테스트 — 우선순위 4종 회귀 PASS + floor 재학습 in-flight 관찰(무결성 무손상)
- 🛠 [시뮬] Phase2 W2 진입 — 배치 다양성(floor) 사이클 ACT 재학습 착수(in-flight) — 2026-07-08
- 📝 [히스토리] 2026-07-07 작업 기록 + README 현황 업데이트 — 2026-07-08

### 2026-07-07
- 📊 [로그] 2026-07-07 시뮬 테스트 — 우선순위 4종 회귀 PASS + DR-trained W1 종료 증거 인덱싱
- 🛠 [시뮬] DR-trained 측정 + 다중시드 공정추정 비교 — Phase2 W1 종료 — 2026-07-07
- 💄 [대시보드] 3D 리플레이 선명도 — 안개 제거로 뿌연 기 해소 + 채도/대비 강화 — 2026-07-07
- 💄 [대시보드] 3D 리플레이 색감 2차 — 그림자+골든 옐로로 포스터와 일치 — 2026-07-07
- 💄 [대시보드] 3D 리플레이 색감 강화 — 홈 포스터처럼 쨍하게 — 2026-07-07

### 2026-07-06
- 📊 [로그] 2026-07-06 시뮬 테스트 — DR 재학습 완료 감지(23:02, loss 0.00498) + 우선순위 4종 회귀(수집 100% yield, 운영 무결성)
- 🛠 [시뮬] Phase 2 W1 DR 재학습 진행중(STAGE=학습중) 문서화 + 무결성 확인 — 2026-07-06
- ✨ [대시보드] 발표용 Overview 재디자인 — 관제탑 게이지 히어로 + 3D 포스터 브릿지, 뉴스 삭제 — 2026-07-06
- 🐛 [대시보드] 3D 리플레이 '허탕/파고듦' 표시 결함 수정 — 큐브 실좌표+회전 기록(사이드카) + 바닥 50ep 재수집 — 2026-07-06
- 🛠 [시뮬+대시보드] 바닥(받침대 없음) 사이클 예약 — 씬-데이터셋 정합 배선 + 바닥 50ep 수집(yield 98%) + 뷰어 바닥씬 대응 — 2026-07-06

### 2026-07-05
- 🛠 [시뮬] Phase 2 W1 — DR 재학습 대기(STAGE 완료/유지 0.7) + 무결성 전수 감사 8종 회귀0 — 2026-07-06
- 📊 [로그] 2026-07-05 시뮬 테스트 — 우선순위 4종 실행회귀(6dof/camera PASS, pick_place open-loop 0/3 baseline, data_collector CL 2/2) + episodes_cl·episodes_cl_dr·0.70 무결성 불변
- 🛠 [시뮬] Phase 2 W1 — DR 50ep 데이터셋 합성 완료(episodes_cl_dr 50/3350, yield 86%, 운영 불변) — 2026-07-05

### 2026-07-03
- 🛠 [시뮬] Phase 2 W1 — 실패집합 seed 강건성 검증(모방격차 가설 실증) — 2026-07-04
- 📊 [로그] 2026-07-03 시뮬 테스트 — 우선순위 4종 실행회귀(6dof/camera PASS, pick_place open-loop 0/2, data_collector CL스모크 2/2) + episodes_cl·0.70 무결성 불변
- 🛠 [시뮬] Phase 2 W1 — 23:00 드라이버 STAGE=완료/유지 문서화 + 축별 DR 무결성 재확인(light/friction/camera 각 0.70·실패집합 {2,5,8} 불변) — 2026-07-03
- 📝 [히스토리] 2026-07-02 작업 기록 + README 현황 업데이트 — 2026-07-03

### 2026-07-02
- 🛠 [시뮬] Phase 2 W1 — DR 축별 ablation(light/friction/camera 각 0.70, 실패집합 불변 → 지배 섭동축 없음·정책 축별 강건) — 2026-07-03
- 📊 [로그] 2026-07-02 시뮬 테스트 — 우선순위 3종 회귀 재확인(6dof/camera PASS, pick_place open-loop 0/3 기준선) + DR프록시 0.70→0.80 무결성 유지
- 🛠 [시뮬] Phase 2 W1 — 23:00 드라이버 STAGE=완료/유지 문서화 + 무결성 재확인(50ep·0.7 불변) — 2026-07-02

### 2026-07-01
- 🛠 [시뮬] Phase 2 W1 — DR on/off 프록시 측정(DR-on 8/10 vs off 7/10, 정책 섭동 강건) — 2026-07-02
- 📊 [로그] 2026-07-01 시뮬 테스트 — 우선순위 4종 회귀 실행 12/12 성공(6dof/camera 100%, collector 스모크 yield 3/3, pick_place open-loop 0% 기준선), 운영 데이터 무손상
- 🛠 [시뮬] Phase 2 W1 — DR 를 수집기/측정기 reset 훅에 연결(opt-in --dr) — 2026-07-01

### 2026-06-30
- 🛠 [시뮬] Phase 2 W1 Domain Randomization 기반 모듈 착수 (조명/마찰/카메라노이즈 3축, 8샘플 검증) — 2026-07-01
- 📊 [로그] 2026-06-30 시뮬 테스트 — W4 종료일 우선순위 4종 회귀 통과(6dof/camera 100%, collector smoke 2/2 yield 100%), 운영 데이터 무손상
- 🛠 [시뮬] closed-loop 1사이클 완료/유지 — 6/30 STAGE 문서 자가치유(stray markup 제거) — 2026-06-30

### 2026-06-28
- 🛠 [시뮬] closed-loop 1사이클 완료/유지 검증·문서화 — 2026-06-29
- 📊 [로그] 2026-06-28 시뮬 테스트 — 우선순위 4종 실제 실행(headless/camera 100%, collector yield 100%, 레거시 pick_place 0% 기준선), closed-loop 1사이클 완료/유지
- 📄 [리포트] 2026-06-28 일일 리포트 HTML 커밋 — 2026-06-28
- 📝 [히스토리] 2026-06-27 작업 기록 + README 현황 업데이트 — 2026-06-28

### 2026-06-27
- 🛠 [시뮬] closed-loop 1사이클 완료/유지 검증·문서화 — 2026-06-28
- 📊 [로그] 2026-06-27 시뮬 테스트 — 우선순위 4종 실제 실행(headless/camera/collector 100%, collector yield 100%, 레거시 pick_place 0% 기준선), 1사이클 완료/유지 70%
- 📄 [리포트] 2026-06-27 일일 리포트 HTML 커밋 — 2026-06-27
- 📝 [히스토리] 2026-06-26 작업 기록 + README 현황 업데이트 — 2026-06-27

### 2026-06-26
- 🛠 [시뮬] closed-loop 1사이클 완료/유지 검증·문서화 — 2026-06-27
- 📊 [로그] 2026-06-26 시뮬 테스트 — 우선순위 4종 실행(headless/camera/collector 100%, pick_place 레거시 0%), 1사이클 70% 유지
- Merge pull request #6 from kiheon-jang/feat/site-docs-viewer-adaptive
- feat(site-docs): 뷰어 image_layout 적응형 레이아웃 포팅
- Merge pull request #5 from kiheon-jang/feat/site-docs-slide-redesign

### 2026-06-25
- 🛠 [시뮬] closed-loop 1사이클 완료/유지 — 성공률 70%(목표 90% 간극) 문서화 + 환경 무결성 재검증 — 2026-06-26
- 📊 [로그] 2026-06-25 시뮬 테스트 — 우선 4종 회귀 통과(6dof/camera/pickplace/collector), closed-loop 1사이클 70% 디스크 검증
- 🛠 [시뮬] closed-loop 자동수집 1사이클 완주 — rollout 70%(7/10) — 2026-06-25
- 📝 [메일] 아침 보고 크론 no_agent 전환 + false-positive 수정 문서화 — 2026-06-25
- 🐛 [메일] 아침 보고 false-positive 수정 — 23:00 야간잡 '어제 성공'을 정상 인정

### 2026-06-24
- 🛠 [시뮬] closed-loop 1사이클 학습 스테이지 문서화(epoch85/100) + 데이터셋·체크포인트 정합 검증 — 2026-06-25
- 📊 [로그] 2026-06-24 시뮬 테스트 — headless 3종 스모크 정상(6dof/듀얼카메라/pick-place), closed-loop 학습 epoch69/100 진행
- 🛠 [시뮬] closed-loop 자동수집 1사이클 진척(수집✓→학습 64/100→측정대기) — 2026-06-24
- 🎬 [측정] render_act_rollout closed-loop 정합 + 견고화 — 2026-06-24
- 📝 [크론] 파이프라인 드라이버를 cop_sim_env.py 로 통합 + 실제 크론ID/git_pull 원인 기록 — 2026-06-24

### 2026-06-21
- 📊 [로그] 2026-06-22 시뮬 테스트 — 우선순위 3종 회귀 1.00, ACT 학습 epoch 34/100 병행 정상
- 🛠 [시뮬] W4 D1 ACT 학습 진행률 (epoch 34/100, loss 0.00272) — 2026-06-22
- 📊 [로그] 2026-06-21 시뮬 테스트 — 학습 가동 중 회귀 3종 1.00 통과 (sandbox 해소 후 첫 정상 회차)
- 🛠 [시뮬] W3 D7 ACT 학습 진행률 (epoch 28/100, loss 0.0033) — 2026-06-21
- 🔧 [자동화] 야간 크론 권한 allowlist (.claude/settings.json) — sandbox 차단 영구 해소

### 2026-06-20
- 📝 [히스토리] 2026-06-19 작업 기록 + README 현황 업데이트 — 2026-06-20

### 2026-06-19
- 📝 [히스토리] 2026-06-18 작업 기록 + README 현황 업데이트 — 2026-06-19

### 2026-06-15
- 📝 [히스토리] 2026-06-14 작업 기록 + README 현황 업데이트 — 2026-06-15

### 2026-06-14
- 📝 [히스토리] 2026-06-13 작업 기록 + README 현황 업데이트 — 2026-06-14

### 2026-06-11
- UX: 사이드바 서브 'AI 연구 및 기술 내재화를 위한'
- UX: 사이드바 서브 두 줄 — '2026 사내 CoP' / '활동 대시보드'
- UX: 사이드바 서브 'Sim · Phase Roadmap' → '2026 사내 CoP · 활동 대시보드'
- fix: pptx 다운로드 — 사진 없는 보고서가 옛 5월 사진 끌고 나가는 버그
- UX: 서브 텍스트 = AI 자동화 운영 cron 4건 요약 + title/sub 간격 조정

### 2026-06-08
- ✏️ [대시보드] "운영자" → "CoP 담당자" + "수동 개입 없이" 적용
- ✏️ [대시보드] AI 자동화 운영 문구 다듬기 + 사양/내부 표현 제거
- 🤖 [대시보드] Overview CoP 설명 + AI 자동화 운영 메뉴 신규 + CoP 리뷰 문구 정리
- ✏️ [대시보드] 기술 가이드 메뉴 → "CoP 리뷰" 로 리네임 + Overview 밑으로 이동
- 🎓 [대시보드] 기술 가이드 메뉴 신규 추가 (비전공자용)

### 2026-06-02
- 📊 [로그] 2026-06-03 시뮬 테스트 —  실행 테스트 및 메트릭 수집
- 🛠 [시뮬] 데이터 합성 — 2026-06-03
- 📊 [로그] 2026-06-02 시뮬 테스트 — 200 에피소드 데이터 수집 및 형식 검증 완료
- 📝 [히스토리] 2026-06-01 작업 기록 + README 현황 업데이트 — 2026-06-02

### 2026-06-01
- 📊 [로그] 2026-06-02 시뮬 테스트 — 환경 건전성 테스트 및 데이터 수집 스크립트 동작 확인
- 📊 [로그] 2026-06-01 시뮬 테스트 — 200 에피소드 데이터 수집 및 형식 검증, 누락 파일 재생성
- 📝 [히스토리] 2026-05-31 작업 기록 + README 현황 업데이트 — 2026-06-01

### 2026-05-31
- 📊 [로그] 2026-06-01 시뮬 테스트 — LeRobot Dataset 포맷 검증 및 이슈 해결
- 🛠 [시뮬] 시뮬에서 200 에피소드 자동 생성 — 2026-06-01
- 📊 [로그] 2026-05-31 시뮬 테스트 — 시뮬레이션 스크립트 실행 및 50 에피소드 수집 확인
- chore(self-heal): 자가치유 기록 추가
- 🔄 [주간정리] 2026-05-31 W4주차 — 보고용 증거 17건

### 2026-05-30
- 📊 [로그] 2026-05-31 시뮬 테스트 및 Phase 0 완료 보고서 업데이트
- 🛠 [시뮬] Phase 0 완료 리포트 + 6월 Phase 1 준비 — 2026-05-31
- chore(self-heal): 자가치유 기록 추가 - 50 에피소드 데이터 수집 재실행 반영
- 📝 [히스토리] 2026-05-29 작업 기록 + README 현황 업데이트 — 2026-05-30

### 2026-05-29
- chore(self-heal): research-log 2026-05-30 업데이트 - Phase 0 완료 리포트 작성 기록
- 🛠 [시뮬] Phase 0 완료 리포트 작성
- 📊 [로그] 2026-05-30 시뮬 테스트 — 50 에피소드 데이터 수집 및 자가치유 기록
- chore(self-heal): 자가치유 기록 추가 - research-log 2026-05-30 소급 작성
- 📊 [로그] 2026-05-29 시뮬 테스트 — 50 에피소드 수집 및 Phase 0 완료 리포트 (자가치유 포함)

### 2026-05-28
- 📊 [로그] 2026-05-29 시뮬 테스트 — 50 에피소드 데이터 수집 및 시뮬 테스트
- 🛠 [시뮬] 50 에피소드 데이터셋 수집 — 2026-05-29
- chore(self-heal): 자가치유 기록 추가
- 🛠 [시뮬] Phase 0 완료 리포트 작성 — 2026-05-28
- 📝 [히스토리] 2026-05-27 작업 기록 + README 현황 업데이트 — 2026-05-28

### 2026-05-27
- 🛠 [시뮬] LeRobot Dataset 포맷으로 50 에피소드 합성 — 2026-05-28
- chore(self-heal): 자가치유 기록 추가 (research-log 2026-05-28 소급 작성)
- 📊 [로그] 2026-05-27 시뮬 테스트 — 데이터 수집 및 시뮬 스크립트 실행
- 🛠 [시뮬] 자동 데이터 수집 스크립트 실행 — 2026-05-27
- chore(submodule): Update SO-ARM100 submodule reference with cube additions

### 2026-05-25
- chore(self-heal): 자가치유 기록 추가
- 📝 [히스토리] 2026-05-24 작업 기록 + README 현황 업데이트 — 2026-05-25

### 2026-05-24
- chore(self-heal): 자가치유 기록 추가
- 🔄 [주간정리] 2026-05-24 W4 — 보고용 증거 4건

### 2026-05-23
- 📊 [로그] 2026-05-23 시뮬 테스트 — Pick-Place 시뮬 동작 및 로그 기록
- 🛠 [시뮬] Pick-Place 시나리오 (큐브 1개) 시뮬 동작 — 2026-05-23
- 📝 [히스토리] 2026-05-22 작업 기록 + README 현황 업데이트 — 2026-05-23

### 2026-05-22
- 🔧 [자동화] Hermes cron 4개 `--clear-skills` 처리 — terminal/file/web 오탐 경고 제거
- 🛠 [스킬] `cop-physical-ai-self-heal` 신설 — cron 자가진단+복구 프로토콜
- 📝 [보고] `generate_daily_report.py` — `research/CHANGELOG.md` + `README.md` 자동 업데이트 추가 (메일 발송 후 git push)
- 📋 [인수인계] 전체 문서 소급 업데이트 (CHANGELOG, AGENT_PROCESS, cron-jobs, decisions, HANDOVER)

### 2026-05-21
- 📋 [로그] 2026-05-19~21 research-log 소급 작성 (크론 실패 복구)
- ✅ [로드맵] W1~W3 완료 항목 `[v]` 체크 — 크론 혼선 방지

### 2026-05-19
- 🛠 [시뮬] W3 마찰계수 튜닝 — `samples/training/sim_friction_tuning.py` 작성, frictionloss 파라미터 동적 조정

### 2026-05-18
- 🛠 [시뮬] W3: 동일 명령 시뮬 vs 실기 관절각 비교 (시뮬 결과) — `W3_joint_angle_comparison_2026-05-18.md`

### 2026-05-17
- 🛠 [시뮬] W3: 관절 각도 비교 스크립트 준비 — `sim_joint_angle_comparison_script.py` 작성

### 2026-05-16
- 🛠 [시뮬] W3: 시뮬 무게/관성 조정 — MJCF inertial 값에 CAD 기본값 주석 추가, `sim_mass_inertia_adjustment_2026-05-16.md`

### 2026-05-15
- 🔧 [환경] Hermes Agent v0.10.0 → v0.13.0 업그레이드 (3481 커밋, 22개 신규 스킬)
- 🔧 [환경] Hermes gateway launchd plist 갱신 (`hermes gateway install`)
- 🔧 [환경] `generate_daily_report.py` 파싱 버그 3개 수정 (외부의존 `\n` 리터럴, 이슈/진척 헤더 패턴 멀티-폴백)
- 📝 [의존] SO-ARM100 로컬 커밋 완료 — `so101_new_calib.xml` (오버헤드 카메라 추가 + 관절 range 조정)
- 📋 [계획] 웹캠 캘리브레이션값 / SO-ARM101 실측값 → **옵션으로 재분류** (없어도 시뮬 진행 가능, 기본값 사용)

### 2026-05-14
- 🛠 [시뮬] W2 5/14: 카메라 동기화 검증 — 오버헤드+그리퍼 카메라 동시 캡처 검증

### 2026-05-12
- 🛠 [시뮬] W2 5/12: `mujoco.Renderer` RGB 이미지 추출 검증 (차단됐다가 5/15 해제)
- 🛠 [시뮬] W2: 오버헤드 카메라 셋업 보고서

### 2026-05-11
- 🛠 [시뮬] W2: 카메라 2대(오버헤드+그리퍼) 시뮬 셋업 및 RGB 이미지 추출 검증

### 2026-05-10
- 🛠 [시뮬] W2: Joint limits 재적용 (W1 이어서 — MJCF forcerange 조정)

### 2026-05-06
- 🛠 [시뮬] W1: 단순 동작 시연 스크립트 — sin파 패턴 6-DoF 관절 제어

### 2026-05-05
- 🛠 [시뮬] W1: 그리퍼 추가 + 단순 동작 시연 (`Claude CLI 인증 오류`로 claude -p 우회)

### 2026-05-04
- 🛠 [시뮬] W1: Joint limits 적용 — STS3215 사양 (360° / 1.5Nm)
- 📧 [메일] 일일 보고 시스템 시뮬 트랙으로 전면 재작성 (`generate_daily_report.py` v3)
- 📧 [메일] `오늘의 한 줄` 섹션 추가 (Gemini API 자동 생성, 비전공자 친화)
- 📧 [메일] 모바일 반응형 + `오늘의 결과물` 미디어 카드 섹션 추가
- 📧 [메일] 수신자 추가 — kimeun091473@gmail.com (총 4명)

### 2026-05-03
- 🛠 [시뮬] W1: 6-DoF 동작 확인 — viewer로 SO-ARM101 관절 동작 검증
- 📊 [로그] 2026-05-03 research-log 작성

### 2026-05-01
- 🛠 [의사결정] 시뮬레이터 최종 확정: **MuJoCo 3.x** (Phase 0~2 메인) + Isaac Lab (Phase 3+, 차년도 별도 GPU 서버)
  - 사유: Mac Mini M5 (Apple Silicon)에서 Isaac Lab 미지원
- 🤖 [구조] 자동화 플랫폼: OpenClaw → Hermes Agent (로컬 Mac Mini, 2026-04-29 마이그레이션 후 시뮬 트랙으로 재구성)
- 🔄 [구조] 크론 4개 prompt 전체 재작성 (요일별 주제 순환 폐기 → PHASE_ROADMAP.md 기반 단계별 점진 구축)
  - 신규 ID: 9ad85007cf27, 85d322d3b37c, fb6d7cb26650, 0b1d4a7b2bf7
  - 폐기 ID: dc257031, b2e623a4, dcbf84a5, ed5aff22, 20ee15d4
- 📁 [구조] 신규 폴더: research/simulation/, agent/research-log/, agent/report-evidence/, ~/Obsidian/00_AI_Wiki/CoP_PhysicalAI/
- 📋 [신설] research/simulation/PHASE_ROADMAP.md — Phase 0~5 단계별 로드맵 (5월~10월)
- 📋 [신설] research/simulation/00_kickoff.md — Phase 0 W1 킥오프
- 📋 [신설] agent/external-dependencies.md — 외부 의존 / 사용자 수동 작업 누적
- 📧 [개편] 메일 [4-A] 외부 의존 섹션 신설 (사용자 수동 작업 매일 노출)
- 🗂️ [구조] 보고용 트랙 ↔ 실제 연구 트랙 분리 (월별 계획서는 그대로 유지, 시뮬은 선행)

### 2026-04-29
- 🤖 [마이그레이션] OpenClaw → Hermes Agent (Mac Mini M5 24/7 로컬 운영) 완료
- 🔧 [정리] fcc-proxy 배제, NVIDIA NIM 직결 라우팅
- 📝 [업데이트] AGENT_PROCESS.md 플랫폼 표기 (OpenClaw → Hermes)

### 2026-04-22
- 📋 [초안] 2026-04-22_sim2real-gap-techniques.md — Sim2Real 격차 해소 최신 기법 (Digital Cousins, Sim2Real-VLA, RL Co-Training, PACE, lerobot-sim2real)

### 2026-04-21
- 📁 [구조] research/drafts/ 폴더 신설 (초안 보관용)
- 📁 [구조] research/latest-tech/ 확정본 전용으로 용도 명확화
- 📁 [구조] research/decisions/ 결정 로그 폴더 신설
- 📋 [초안] 리서치 자동화 시작 — 매일 23:00 크론으로 drafts/ 에 초안 생성 예정
- 📋 [초안] 2026-04-21_isaac-lab-sim-rl-trends.md — Isaac Lab/Isaac Sim 강화학습 최신 동향 (v2.3.x → 3.0, Isaac Sim 6.0 EAR)
