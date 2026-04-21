# Isaac Lab / Isaac Sim 강화학습 최신 동향 (2025–2026)

> 작성일: 2026-04-21 | 상태: 초안 (검수 전)

## 💡 한 줄 요약
Isaac Lab v2.3.x가 덱스트러스 조작·로코매니퓰레이션을 대폭 강화했고, Isaac Sim 6.0 Early Release는 Newton 멀티 물리 백엔드와 비동기 렌더링으로 RL 훈련 파이프라인을 근본적으로 재설계했다.

## 🔑 핵심 개념

1. **Isaac Lab 2.3.x (→ 3.0 예고)**: Isaac Sim 5.1 기반의 최신 안정 릴리스. DexSuite(덱스트러스 RL), SkillGen+cuRobo 통합(GPU 모션 플래닝), G1 로코매니퓰레이션 환경, Haply·Vive·Manus 텔레오퍼레이션 장치 지원 추가. v2.3.2가 현재 main 브랜치 최종 버전이며, 이후 개발은 `develop` 브랜치에서 Isaac Lab 3.0을 향해 진행됨.
2. **Isaac Sim 6.0 Early Developer Release (GTC'26, 2026-03-16)**: 멀티 물리 백엔드(PhysX + Newton) 지원, Warp 기반 Core Experimental API, 비동기 렌더링, Fabric 가속, 완전히 재작성된 URDF/MJCF 임포터, ROS2 Jazzy 네이티브 지원. PhysX에서 Newton으로의 에셋 전환이 자동화되어 RL 워크플로우와의 연계가 수월해짐.
3. **SO-ARM101 Sim-to-Real 파이프라인**: NVIDIA 공식 문서(`docs.nvidia.com/learning/physical-ai/sim-to-real-so-101`)에 Isaac Lab + Isaac GR00T + Cosmos + LeRobot를 결합한 SO-101 Sim-to-Real 가이드가 2026년 4월에 공개됨. 일반 사용자도 홈 로봇 랩을 구축할 수 있는 End-to-End 튜토리얼 제공.

## 📊 왜 우리 프로젝트에 중요한가

SO-ARM101/LeRobot 기반 프로젝트 입장에서 이번 업데이트는 세 가지 실질적 이점이 있다:

- **SkillGen + cuRobo 통합**: 시뮬레이션 내에서 GPU 기반 모션 플래닝으로 조작 시퀀스를 자동 세분화·데이터 생성 가능 → 데모 데이터 수집 비용 대폭 절감.
- **SO-ARM101 공식 Sim-to-Real 튜토리얼 등장**: Isaac Lab에서 학습한 정책을 실제 SO-101 암에 직접 배포하는 레퍼런스 파이프라인이 생겼다. CoP 프로젝트의 RL → 실기 검증 사이클에 직접 활용 가능.
- **Newton 멀티 물리 백엔드 (Isaac Sim 6.0)**: PhysX 단일 의존에서 벗어나 접촉이 많은 조작 태스크에서 더 현실적인 물리 시뮬레이션 가능 → Sim2Real 격차 축소 기대.

## 🔍 상세 내용

### Isaac Lab 2.3.0 ~ 2.3.2 주요 업데이트

**덱스트러스 조작 (DexSuite)**
- Kuka 암 + Allegro Hand 기반 두 가지 새 덱스트러스 환경 추가
- ADR(Automatic Domain Randomization) 및 PBT(Population-Based Training) 지원으로 정책 견고성 향상
- 시각 기반 촉각 센서(Visual-based Tactile Sensor) 추가로 접촉 감지 현실화

**Mimic 이미테이션 러닝 + SkillGen**
- cuRobo 통합: GPU 가속 모션 플래닝으로 스킬 분절 데이터 생성 자동화
- G1 휴머노이드의 로코매니퓰레이션 환경: RL 보행 + IK 기반 조작을 결합, pick-navigate-place 태스크 생성
- Haply 장치 API(포스 피드백) 및 Quest/Vive/Manus Glove 텔레오퍼레이션 지원 확대

**드론 지원 (v2.3.2 신규)**
- 멀티로터/추진기 액추에이터 및 ARL 드론 태스크 추가
- Wrench Composer API로 여러 힘/토크를 동일 바디에 합성 가능 (드론 공력 시뮬레이션에 활용)

**OpenArm 환경 (v2.3.2 신규)**
- OpenArm 환경 추가: 오픈소스 로봇 암 생태계와의 연계 확대

**Isaac Lab 3.0 예고**
- v2.3.2 이후 `main` 브랜치 개발 종료, `develop` 브랜치에서 대규모 구조 개편 예정
- 기여자는 PR 타겟 브랜치를 `develop`으로 변경 필요

### Isaac Sim 6.0 Early Developer Release (GTC'26)

**멀티 물리 백엔드**
- PhysX + Newton 동시 지원: 에셋을 Isaac Sim에서 제작하고 Isaac Lab RL로 전환 시 물리 백엔드 조정 불필요
- Asset Transformer: 레거시 로봇 에셋을 새 구조로 자동 변환

**성능 개선**
- 비동기 렌더링: 시뮬레이션과 렌더링을 별도 스레드에서 병렬 처리
- Fabric 전면 지원: USD 데이터의 벡터화 표현으로 런타임 시뮬레이션 성능 향상
- Kit 110.0: NVIDIA Omniverse NuRec 3D 가우시안 스플래팅, 중첩 강체 물리 GPU 가속

**로봇 저작 도구**
- Robot Inspector: 계층 구조·운동 체인 시각화, 자기 충돌 감지
- Robot Poser: 시뮬레이션 독립적인 조깅 도구 및 포즈 저장

**ROS2 통합 강화**
- ROS2 Jazzy 네이티브 소싱 (Python 3.12 완전 지원)
- H.264 압축 RGB 퍼블리싱(하드웨어 가속), RTX LiDAR 포인트클라우드 메타데이터(강도 등) 지원

**데이터 생성 (Isaac Sim Replicator)**
- Replicator Object: 물리 속성(질량, 마찰, 반발계수) 랜덤화, 피라미드 스태킹 등 배치 전략
- Chat IRO: Llama-4, ChatGPT-OSS, Qwen3 다중 생성 AI 모델로 복잡한 3D 씬 랜덤화를 자연어로 지시
- VLM 씬 캡셔닝: 시뮬레이션 레이블 기반 캡션으로 VLM 학습 데이터 품질 향상

### SO-ARM101 공식 Sim-to-Real 튜토리얼 (2026-04-17)

NVIDIA가 "It's Time to Build Your Home Robot Lab" 공식 가이드와 YouTube 영상을 공개하며, SO-101 + Isaac Lab + Isaac GR00T + Cosmos + LeRobot 조합의 Sim-to-Real 파이프라인을 단계별로 안내함. 공개 URL: `docs.nvidia.com/learning/physical-ai/sim-to-real-so-101`

### Isaac Lab-Arena + LeRobot 평가 프레임워크 (2026-01-05)

HuggingFace 블로그에서 NVIDIA가 Isaac Lab-Arena를 통해 일반 로봇 정책(Generalist Robot Policy)을 시뮬레이션에서 평가하는 방법을 발표. Isaac Sim 5.1.0 요건 공유, LeRobot과의 통합 평가 워크플로우 제시.

## 🔗 출처
- [Isaac Lab Release Notes (v2.3.0 ~ v2.3.2)](https://isaac-sim.github.io/IsaacLab/main/source/refs/release_notes.html)
- [Isaac Lab GitHub Releases](https://github.com/isaac-sim/IsaacLab/releases)
- [Isaac Sim 6.0 Early Developer Release — NVIDIA Forums](https://forums.developer.nvidia.com/t/announcement-isaac-sim-6-0-early-developer-release-for-gtc26/363709)
- [NVIDIA: Generalist Robot Policy Evaluation in Simulation (HuggingFace)](https://huggingface.co/blog/nvidia/generalist-robotpolicy-eval-isaaclab-arena-lerobot)
- [NVIDIA: Sim-to-Real with SO-101 (YouTube, Apr 2026)](https://www.youtube.com/watch?v=3TL3ALQxQX8)
- [Seeed Studio Wiki: Training SoArm101 Policy with IsaacLab](https://wiki.seeedstudio.com/training_soarm101_policy_with_isaacLab/)
- [Isaac Lab Documentation](https://isaac-sim.github.io/IsaacLab/)
