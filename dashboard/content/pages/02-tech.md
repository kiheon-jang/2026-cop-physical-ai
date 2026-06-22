---
id: tech
title: "CoP 리뷰 (기술 설명)"
order: 2
menu_route: tech
screenshot: tech.png
category: 핵심
---
## 기능명세

CoP 리뷰 화면(`view-tech`)은 이 프로젝트가 사용하는 기술 스택, 학습 방법, 의사결정 근거를 한 화면에 정리한 기술 참조 문서이다. 데이터는 `build.py`의 정적 값과 `build_business_kpi()`의 phase 상태에서 부분 동적으로 생성된다.

**한 줄 결론 박스 (tech-summary)**
"정비현장의 PCB 작업을 로봇에 가르치는 프로젝트"라는 비전공자용 요약 + 전체 흐름(시뮬 시연 데이터 → AI 학습 → 실제 로봇팔) 3단계 설명.

**전체 흐름 플로우차트 (flow-chart)**
6단계 흐름을 가로 카드 형태로 렌더링한다. JavaScript의 `flow-chart` 엘리먼트에 동적으로 생성된다 (현재 단계 하이라이트 포함). 각 단계: ① SO-ARM101 MJCF 모델 → ② MuJoCo 시뮬 → ③ IK 기반 Pick-Place → ④ 200 에피소드 합성 → ⑤ ACT 학습 → ⑥ 실기 전환(Phase 2+).

**사용 기술 카드 5개 (tech-grid)**
각 기술에 이름·라이선스·역할·"왜 선택?"·"어떻게 사용?" 섹션을 포함한 확장형 카드:
1. **MuJoCo 3.8** (Apache 2.0) — 가상 로봇팔 시뮬 엔진. Apple Silicon 네이티브 지원. `sim_pick_place.py`로 IK 기반 Pick-Place 동작 생성, `sim_data_collector.py`로 큐브 위치 ±20mm 랜덤 변동 200 에피소드 합성.
2. **SO-ARM101** (CC-BY-SA) — 오픈소스 6-DoF 로봇팔. MJCF 모델(`so101_new_calib.xml`), 6관절(shoulder_pan/lift, elbow_flex, wrist_flex/roll, gripper), 서보 Feetech STS3215. 실기 검증은 Phase 2(7월) 예정.
3. **HuggingFace LeRobot** (Apache 2.0) — 로봇 학습 프레임워크. Dataset v3.0 포맷(`local/cop-pickplace`, root=`data/episodes/`), parquet(관절 상태)+mp4(카메라 영상) 분리 저장.
4. **ACT** (Action Chunking Transformer, MIT 2023) — 모방학습 알고리즘. `scripts/train_act.py`가 `ACTConfig`+`ACTPolicy` 호출. 입력: 천장 카메라+6축 관절(과거 n_obs_steps 프레임). 출력: chunk_size=100 미래 액션 시퀀스. 학습 진행 상황은 `id="act-status-text"` 요소에 동적 표시.
5. **모방학습 (Imitation Learning)** — 학습 방식. IK가 정답 액션 자동 생성 → 영상과 함께 200 에피소드 저장 → ACT가 매핑 학습.

**현재 학습 데이터셋 섹션 (dataset-stats)**
`build_training_metrics()` + `build_videos()`가 반환하는 데이터셋 메타(에피소드 수, 프레임 수)를 동적 표시. `id="dataset-context-label"`에 데이터셋 상태 레이블.

**AI 학습 1사이클 다이어그램 (cycle-diagram)**
4단계 카드: Step 1 관측(천장 카메라 RGB 480×640 + 6축 관절 qpos) → Step 2 ACT 추론(트랜스포머 인코더-디코더) → Step 3 액션 출력(6축 ctrl 명령, chunk_size 프레임) → Step 4 실행(시뮬=MuJoCo actuator / 실기=STS3215 서보) → 반복.

**의사결정 근거 (rationale)**
6개 항목(왜 시뮬 합성? / 왜 MuJoCo? / 왜 텔레오퍼 안 함? / 왜 ACT? / 왜 Pick-Place 부터? / 왜 Sim-to-Real 분리?). 기획 시점 2026-05 기준 결정 사항.

**차년도 계획 (future-box)**
Phase 3+ 이후 계획: 강화학습(Isaac Lab + LeIsaac), GR00T N1.5 파인튜닝, NVIDIA Orin Nano Super 배포, LeKiwi/XLeRobot 확장. 2027년 이후 로드맵이며 현재 진행 중이 아님.

**데이터 출처**: 대부분 `build.py` 정적 상수(`PHASE_META`, `PROJECT_VISION`). 일부 동적 값(`tech-progress`, `act-status-text`, `phase2-status-text`)은 `build_business_kpi()` 반환값에서 JavaScript가 채운다.

## 사용가이드

CoP 리뷰는 이 프로젝트의 기술적 내용을 비전공자도 이해할 수 있도록 설명하는 화면입니다. "왜 이 기술을 썼는지", "로봇이 어떻게 배우는지"를 한 페이지에 정리했습니다.

**전체 흐름 읽는 법**
상단의 6단계 카드를 왼쪽부터 순서대로 읽으세요. 로봇 팔의 가상 모델을 만들고 → 시뮬에서 자동으로 작업을 수행하고 → 그 데이터를 AI에 학습시키는 흐름입니다.

**사용 기술 카드**
각 기술 카드에는 "왜 선택?"과 "어떻게 사용?" 두 섹션이 있습니다.
- "왜 선택?"은 여러 후보 중 이 기술을 고른 이유(예: MuJoCo는 Isaac Lab이 우리 컴퓨터에서 안 돌아서 선택했다)를 설명합니다.
- "어떻게 사용?"은 실제로 이 기술이 어떤 파일로, 어떤 역할을 하는지 설명합니다.

**AI 학습 1사이클 다이어그램**
"로봇이 어떻게 배우는가"를 4단계로 보여줍니다. 카메라로 본 영상과 관절 위치를 보고 → AI가 다음 동작을 예측하고 → 로봇이 그대로 실행하고 → 다시 관찰하는 과정을 반복합니다.

**의사결정 근거**
"왜 이렇게 했나"에 대한 설명입니다. 예를 들어 "왜 사람이 직접 로봇을 조종하는 방식을 쓰지 않았냐"는 질문에 "시간 비용이 크기 때문에 시뮬 자동화를 먼저 했다"고 설명합니다. 보고 시 질문을 받을 때 이 섹션을 참고하세요.

**차년도 계획 박스**
하단의 녹색 박스는 2027년 이후 장기 계획입니다. 현재 진행 중인 내용이 아닙니다.
