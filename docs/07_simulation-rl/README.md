# Phase 3: 시뮬레이션 강화학습 — 사전 조사

> **조사 일자**: 2026-04-22
> **조사 범위**: Isaac Sim/Lab 시스템 요구사항, Orin Nano Super 호환성, 시뮬레이터 비교, LeIsaac/GR00T 연동, 클라우드 대안

---

## 1. NVIDIA Orin Nano Super 스펙 vs Isaac Sim 요구사항

### 1.1 Orin Nano Super 스펙 요약

| 항목 | 스펙 |
|------|------|
| **GPU** | NVIDIA Ampere 아키텍처, **1024 CUDA cores**, 32 Tensor Cores |
| **메모리** | **8GB LPDDR5 (CPU+GPU 공유)**, 128-bit, 102 GB/s |
| **AI 성능** | 67 INT8 TOPS |
| **CPU** | 6-core Arm Cortex-A78AE, 1.5GHz |
| **최대 전력** | 25W |
| **아키텍처** | ARM64 (x86_64 아님) |
| **가격** | ~$250 USD |

> ⚠️ 메모리가 CPU/GPU 통합 공유 방식이므로 실질적인 GPU 전용 VRAM은 설정에 따라 제한됨

### 1.2 Isaac Sim 4.x 시스템 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| **OS** | Ubuntu 22.04 / Windows 11 (x86_64) | Ubuntu 22.04 (x86_64) |
| **GPU** | GeForce RTX 3070 | GeForce RTX 4080 |
| **VRAM** | 8GB | 16GB |
| **RAM** | 32GB | 64GB |
| **Storage** | 50GB SSD | 500GB SSD |
| **GPU 아키텍처** | Turing+ (RTX 20xx 이상) | Ada Lovelace |

> 📌 Isaac Sim 5.x 기준으로는 최소 요구사항이 GeForce RTX 4080 / 16GB VRAM으로 상향됨

### 1.3 호환성 평가: ❌ Orin Nano Super에서 Isaac Sim 구동 불가

**불가 이유:**
1. **아키텍처 불일치**: Isaac Sim은 x86_64 전용. Orin Nano Super는 ARM64 (JetPack OS 기반)
2. **VRAM 부족**: Isaac Sim 최소 8GB VRAM 필요, Orin의 8GB는 CPU/GPU 공유 통합 메모리
3. **GPU 성능 부족**: Isaac Sim은 RTX 3070급 이상 필요. Orin GPU는 임베디드 AI 추론용으로 설계됨
4. **Isaac Lab의 GPU 병렬 시뮬레이션**: 수천 개 병렬 환경을 위해 데스크톱급 GPU 필수

**결론**: Orin Nano Super는 **학습된 정책 배포(Deployment/Inference) 전용** 타겟 하드웨어로 사용해야 함.
실제 RL 학습은 별도 환경에서 수행 후 Sim-to-Real 전이 필요.

---

## 2. 시뮬레이터 비교

| 항목 | Isaac Sim | Isaac Lab | MuJoCo | 비고 |
|------|-----------|-----------|--------|------|
| **최소 GPU** | RTX 3070 (8GB VRAM) | RTX 3070 (8GB VRAM) | CPU 가능 (GPU 선택) | Isaac Lab은 Isaac Sim 위에서 동작 |
| **최소 RAM** | 32GB | 32GB | 8GB | |
| **SO-ARM 지원** | ✅ URDF/OpenUSD 임포트 가능 | ✅ [공식 외부 프로젝트 존재](https://github.com/MuammerBay/isaac_so_arm101) | ✅ [gym-so100-c MuJoCo 환경](https://www.tinystruggles.com/posts/building_robotics_playground/) | |
| **LeRobot 연동** | ✅ (LeIsaac 경유, API Standalone) | ✅ (LeIsaac, Isaac Lab-Arena) | ✅ (gym-so100-c, LeRobot 데이터셋 직접 활용) | |
| **RL 학습** | ⚠️ 가능하나 Isaac Lab 권장 | ✅ GPU 병렬화, PPO/SAC 최적화 | ✅ 경량, 빠른 단일 환경 | |
| **병렬 환경** | 제한적 | ✅ 수천 개 GPU 병렬 | ⚠️ 기본 단일, MJX(JAX)로 병렬화 가능 | |
| **라이선스** | NVIDIA 개인 무료 / Enterprise $4,500+/GPU/년 | ✅ BSD-3-Clause (완전 오픈소스) | ✅ Apache 2.0 (구 MIT) | |
| **렌더링 품질** | ✅ 포토리얼리스틱 (Omniverse RTX) | ✅ (Isaac Sim 기반) | ⚠️ 기본 렌더러 (MuJoCo 3.x 개선) | |
| **설치 난이도** | 높음 (50GB+, NVIDIA 전용) | 높음 (Isaac Sim 필요) | 낮음 (pip install mujoco) | |
| **추천 대상** | 시각/센서 데이터 포함 복잡한 환경 | **강화학습 대규모 학습** | 경량·빠른 프로토타이핑 | |

### 2.1 Isaac Sim vs Isaac Lab 관계 정리

```
Isaac Sim (NVIDIA Omniverse 기반 물리 시뮬레이터)
    └── Isaac Lab (RL/IL 학습 프레임워크 — Isaac Sim 위에서 동작)
            └── LeIsaac (SO-ARM + LeRobot 연동 레이어)
```

- **Isaac Sim**: 3D 시뮬레이션 엔진 자체 (OpenUSD, 포토리얼리스틱 렌더링, 물리 엔진)
- **Isaac Lab**: Isaac Sim 위에서 동작하는 RL/IL 학습 프레임워크. GPU 병렬 환경 핵심

### 2.2 Phase 3 권장 선택

| 시나리오 | 권장 시뮬레이터 | 이유 |
|----------|----------------|------|
| 대규모 RL 학습 (Phase 3 메인) | **Isaac Lab** | GPU 병렬화, SO-ARM101 공식 지원, LeIsaac 연동 |
| 빠른 프로토타이핑 / 리소스 부족 | **MuJoCo** | 경량, LeRobot 직접 연동, 클라우드 GPU 불필요 |
| 시각 센서 포함 복잡 환경 | Isaac Sim | 포토리얼리스틱 렌더링 필요 시 |

---

## 3. LeIsaac / GR00T 연동 가능성

### 3.1 LeIsaac

- **GitHub**: https://github.com/LightwheelAI/leisaac
- **라이선스**: Apache-2.0
- **상태**: 활발히 개발 중 (2026년 4월 기준 v0.4.0, 원격 텔레오퍼레이션 추가)

**핵심 기능:**
- SO-101 Follower/Leader를 IsaacLab에서 텔레오퍼레이션
- HDF5 → LeRobot Dataset 변환 스크립트 제공
- GR00T N1.5 / N1.6 파인튜닝 및 배포 지원
- LeRobot EnvHub 공식 통합 (Isaac-based 시뮬레이션 환경)
- `datagen` 모듈: State machine으로 모션 궤적 프로그래매틱 생성

**LeIsaac 데이터 파이프라인:**
```
Isaac Lab 시뮬레이션 (SO-101 환경)
    → HDF5 데이터 수집 (텔레오퍼레이션 or datagen)
    → LeRobot Dataset 변환
    → GR00T N1.5/N1.6 파인튜닝
    → 실제 로봇 배포 (Orin Nano Super)
```

### 3.2 SO-ARM101 URDF/OpenUSD 파일

| 리소스 | 경로/링크 |
|--------|-----------|
| SO-ARM101 Isaac Lab 외부 프로젝트 | https://github.com/MuammerBay/isaac_so_arm101 |
| Isaac Lab URDF → OpenUSD 변환 | NVIDIA Omniverse Livestream 튜토리얼 (2025-04) |
| MuJoCo SO-101 환경 | gym-so100-c (2025-08 기준 MuJoCo 기반 SO101 포함) |
| LeIsaac SO-101 환경 정의 | lightwheelai/leisaac 내 포함 |

> ✅ SO-ARM101 URDF는 공식적으로 존재하며, Isaac Lab / MuJoCo 모두 환경이 구현되어 있음

### 3.3 GR00T N1.5 연동

- LeRobot 텔레오퍼레이션 데이터 (so101-table-cleanup 등) → GR00T N1.5 파인튜닝 가능
- **파인튜닝 VRAM 요구**: 기본 ~25GB VRAM (`--no-tune_diffusion_model` 플래그로 절약 가능)
- SO-101은 GR00T 사전훈련에 포함되지 않아 `new_embodiment` 태그로 파인튜닝 필요
- LeIsaac를 통해 시뮬레이션 수집 데이터 → GR00T 파인튜닝 → 실제 로봇 배포 파이프라인 완성

---

## 4. 클라우드 대안 검토

### 4.1 Isaac Sim / Isaac Lab 클라우드 배포

| 옵션 | 플랫폼 | 비용 | 비고 |
|------|--------|------|------|
| **Isaac Automator** | AWS / GCP / Azure / Alibaba Cloud | 인프라 비용만 (Isaac 소프트웨어 무료) | NVIDIA 공식 클라우드 배포 도구 |
| **AWS Marketplace** | AWS EC2 (G5 인스턴스) | GPU 인스턴스 비용 + $0 소프트웨어 | `NVIDIA Isaac Sim Development Workstation` AMI 무료 제공 |
| **Azure Marketplace** | Azure NC-series | GPU 인스턴스 비용 + $0 소프트웨어 | Microsoft Marketplace에서 무료 제공 |
| **Google Cloud** | GCP A2 / G2 인스턴스 | GPU 인스턴스 비용 | Isaac Lab 공식 지원 |

> ✅ Isaac Sim/Lab 소프트웨어 자체는 **개인 비상업적 용도 무료** (Enterprise 라이선스 $4,500+/GPU/년은 상업적 서비스용)

### 4.2 비용 에스티메이트 (AWS 기준)

| 인스턴스 | GPU | VRAM | 시간당 비용 | 8시간 학습 | 비고 |
|----------|-----|------|------------|-----------|------|
| g5.xlarge | A10G | 24GB | ~$1.01/hr | ~$8 | Isaac Lab 소규모 학습 |
| g5.2xlarge | A10G | 24GB | ~$1.21/hr | ~$10 | 권장 최소 사양 |
| g5.4xlarge | A10G | 24GB | ~$1.62/hr | ~$13 | 병렬 환경 확장 |
| p3.2xlarge | V100 | 16GB | ~$3.06/hr | ~$24 | Isaac Lab 가능하나 구형 |

> 💡 **CoP 권장**: g5.2xlarge로 Isaac Lab 실험 시작 → 병렬 환경 수에 따라 스케일업

### 4.3 Google Colab에서 Isaac Lab

- **❌ 직접 실행 불가**: Isaac Sim/Lab은 Colab 환경(제한된 시스템 접근, 비지속성)에서 동작하지 않음
- Isaac Lab은 시스템 레벨 NVIDIA 드라이버 및 Omniverse 설치 필요
- Colab은 MuJoCo, PyBullet 등 경량 시뮬레이터 학습에 적합

### 4.4 MuJoCo 클라우드 (경량 대안)

- **Google Colab**: MuJoCo + LeRobot 조합 완전 지원 (무료 T4 GPU)
- **Hugging Face Spaces**: LeRobot 학습 환경 구성 가능
- Isaac Lab 대비 병렬 환경 수는 적지만, 초기 프로토타이핑 및 알고리즘 검증에 적합

---

## 5. 결론 및 Phase 3 권장 방향

### 5.1 핵심 결론

```
❌ Orin Nano Super → Isaac Sim/Lab 직접 구동 불가
   (ARM64 아키텍처 + 공유 메모리 구조, x86_64 전용 Isaac Sim)

✅ 권장 파이프라인:
   클라우드 GPU (AWS g5.x / 로컬 RTX GPU)
       → Isaac Lab + LeIsaac (SO-ARM101 환경)
       → RL 학습 (PPO/SAC)
       → 학습된 정책
       → Sim-to-Real 전이
       → Orin Nano Super 배포

✅ 경량 대안:
   MuJoCo (gym-so100-c) → 클라우드/Colab에서 빠른 프로토타이핑
```

### 5.2 단계별 실행 계획

| 단계 | 내용 | 환경 | 예상 기간 |
|------|------|------|---------|
| **3-1** | Isaac Lab + LeIsaac 설치 및 SO-ARM101 환경 셋업 | 로컬 RTX GPU or AWS g5 | 1주 |
| **3-2** | SO-ARM101 Reach/Pick 태스크 RL 학습 (PPO) | AWS g5.2xlarge | 1-2주 |
| **3-3** | LeRobot 데이터 → GR00T N1.5 파인튜닝 | AWS g5.4xlarge (24GB) | 1주 |
| **3-4** | Sim-to-Real 전이 및 Orin 배포 테스트 | Orin Nano Super | 2주 |

### 5.3 리스크

| 리스크 | 수준 | 대응 |
|--------|------|------|
| Sim-to-Real gap | 높음 | Domain randomization 적극 활용 |
| 클라우드 비용 | 중간 | Spot 인스턴스 활용, MuJoCo 프로토타이핑 선행 |
| GR00T 파인튜닝 VRAM 부족 | 중간 | `--no-tune_diffusion_model` 플래그 사용 |
| Isaac Lab 설치 복잡도 | 중간 | NVIDIA Isaac Automator로 클라우드 자동화 |

---

## 참고 링크

- [Isaac Sim 요구사항 (공식)](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/requirements.html)
- [Isaac Lab 공식 문서](https://isaac-sim.github.io/IsaacLab/)
- [Isaac Lab 클라우드 배포](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/cloud_installation.html)
- [LeIsaac GitHub](https://github.com/LightwheelAI/leisaac)
- [SO-ARM101 Isaac Lab 프로젝트](https://github.com/MuammerBay/isaac_so_arm101)
- [GR00T N1.5 SO-101 파인튜닝 튜토리얼](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning)
- [LeIsaac x LeRobot EnvHub 문서](https://huggingface.co/docs/lerobot/envhub_leisaac)
- [AWS Isaac Lab 워크샵](https://aws.amazon.com/blogs/spatial/gpu-accelerated-robotic-simulation-training-with-nvidia-isaac-lab-in-vams/)
