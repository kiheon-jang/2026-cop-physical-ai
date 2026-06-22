---
doc: spec
id: overview
title: "프로젝트 개요 — CoP Physical AI 대시보드"
order: 90
screenshot: ""
---
## 프로젝트 목적

CoP Physical AI는 정비현장의 PCB 작업(픽앤플레이스, RS232 HHT 결선)을 로봇팔에 자동화하는 것을 목표로 하는 사내 커뮤니티 오브 프랙티스(CoP) 프로젝트다. Physical AI / Embodied AI 기술을 내재화하기 위해 2026년 4월~10월(6개월 + 시연)로 진행된다.

## 대시보드의 역할

이 대시보드는 프로젝트의 진척 상황을 한 화면에서 확인·검색·추적하기 위한 도구다. 다음 세 가지 용도로 설계되었다:
- **가시성**: Phase 0~4 6개월(다수의 시뮬 작업)의 진척을 폴더 트리 없이 한눈에 확인
- **의존 추적**: 사용자·실기팀·외부 머신 수동 처리 대기 항목을 마감일·담당자별로 관리
- **증거 큐레이션**: 일일 진척에서 보고용 증거 후보를 자동 추출해 월말 보고서 작성 지원

## 로봇팔 하드웨어

**SO-ARM101** (TheRobotStudio, CC-BY-SA): 6자유도(6-DoF) 오픈소스 로봇팔. Leader + Follower 2대 구성. 서보 모터: Feetech STS3215(12V/7.4V). MJCF 파일(`so101_new_calib.xml`)로 MuJoCo 시뮬과 실기가 동일한 캘리브레이션 공유. 실기 검증은 Phase 2(2026-07) 이후 진행 예정이며, 현재(2026-06)는 시뮬 단계다.

## 시뮬레이션 환경

**MuJoCo 3.8** (DeepMind, Apache 2.0): Apple Silicon(ARM64) 네이티브 지원. SO-ARM101 MJCF 모델을 헤드리스 렌더링으로 실행해 천장 카메라 RGB 영상과 6축 관절 상태를 수집한다. IK(역기구학) 기반 자동 동작 생성으로 Pick-Place 시나리오 200 에피소드를 합성한다(큐브 위치 ±20mm 랜덤 변동).

## 모방학습 파이프라인

1. MuJoCo 시뮬에서 IK로 정답 액션 자동 생성
2. LeRobot Dataset v3.0 포맷(`data/episodes/`, parquet+mp4)으로 저장
3. ACT(Action Chunking Transformer) 학습: 입력 = 천장 카메라 + 6축 관절(과거 n_obs_steps 프레임), 출력 = chunk_size=100 미래 액션
4. 학습된 정책을 시뮬에서 검증, 이후 실기 로봇으로 전환(Sim-to-Real)

현재 기준(2026-06): Phase 1 사전학습 단계 진행 중. 실기 적용은 Phase 2(7월) 이후.

## 프로젝트 단계 요약

- **사전학습 / Kick-off** (4월, 완료): CoP 발족, 하드웨어 발주, ACT/DP 자료 학습
- **Phase 0** (5월): 시뮬 환경 셋업 — MuJoCo 설치, SO-ARM101 MJCF import, Pick-Place 구현
- **Phase 1** (6월): 사전학습 — 데이터 합성 200ep, ACT 학습 시작
- **Phase 2** (7월): Sim2Real 검증 — 실기 50ep 수집, 시뮬↔실기 비교
- **Phase 3** (8월): PCB 조정 — 실제 PCB 픽앤플레이스 학습
- **Phase 4** (9월): RS232 결선 + 1차 기능 완성 (PCB 70% / RS232 40% 목표)
- **시연** (10월): 통합 시연 + 사내 발표
