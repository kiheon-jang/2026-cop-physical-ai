# 🤖 2026 CoP Physical AI — 첫걸음

> **사내 CoP(Community of Practice)** — Physical AI / Embodied AI 기술 내재화 프로젝트  
> SO-ARM101 로봇팔을 기반으로 모방학습 → 강화학습 → 모바일 매니퓰레이터까지 단계적으로 진행

---

## 📌 프로젝트 목표

| 단계 | 목표 | 상태 |
|------|------|------|
| **Phase 1: Foundation** | SO-ARM101 조립 + LeRobot 환경 + 텔레오퍼레이션 | ✅ 완료 |
| **Phase 2: Intelligence** | 데이터 수집 → ACT/Diffusion Policy 모방학습 → 인퍼런스 | 🔄 진행중 |
| **Phase 3: Simulation** | Isaac Sim 강화학습 → Sim2Real | ⏳ 예정 |
| **Phase 4: Expansion** | LeKiwi / XLeRobot 모바일 매니퓰레이터 확장 | ⏳ 예정 |

### 최종 학습 목표 태스크
- 🎯 **1단계**: 물체 이동 (Pick & Place)
- 🎯 **2단계**: PCB 제품의 리셋 & DIP S/W 조정
- 🎯 **3단계**: PCB의 RS232 포트에 HHT(Hand Held Terminal) 꽂기

---

## 🔧 하드웨어 구성

| 장비 | 사양 | 역할 |
|------|------|------|
| **SO-ARM101** x2 | Leader + Follower (6-DoF) | 메인 로봇팔 |
| **Feetech STS3215** | 12V (Follower) / 7.4V (Leader) | 서보 모터 |
| **NVIDIA Orin Nano Super** | - | 온디바이스 인퍼런스 |
| **Raspberry Pi 5** | - | 임베디드 제어 |
| **Webcam** x2 | Top mount + Gripper | 시각 입력 |

---

## 📁 레포지토리 구조

```
2026-cop-physical-ai/
│
├── 📚 docs/                        # 단계별 실습 문서
│   ├── 01_overview/                # 프로젝트 개요 & 로드맵
│   ├── 02_hardware/                # 하드웨어 조립 & BOM
│   ├── 03_software-setup/          # LeRobot 환경 설치
│   ├── 04_teleoperation/           # 텔레오퍼레이션 설정
│   ├── 05_data-collection/         # 데이터 수집 가이드
│   ├── 06_imitation-learning/      # ACT / Diffusion Policy 학습
│   ├── 07_simulation-rl/           # Isaac Sim 강화학습
│   └── 08_expansion/               # LeKiwi / XLeRobot 확장
│
├── 🔬 research/                    # 기술 리서치
│   ├── papers/                     # 논문 정리
│   ├── benchmarks/                 # 성능 벤치마크
│   └── latest-tech/                # 최신 기술 동향
│
├── 💻 samples/                     # 단위 테스트용 샘플 코드
│   ├── motor-control/              # 모터 제어 샘플
│   ├── data-collection/            # 데이터 수집 스크립트
│   ├── training/                   # 학습 파이프라인 샘플
│   └── inference/                  # 인퍼런스 샘플
│
├── 🖼️ assets/
│   ├── images/                     # 사진, 스크린샷
│   └── 3d-models/                  # STL, 3MF 파일 (외형)
│
└── 📋 산출물/                      # 원본 Obsidian 노트 (단계별 실습 로그)
```

---

## 🚀 빠른 시작

### 1. LeRobot 환경 설치
```bash
conda create -n lerobot python=3.12 -y
conda activate lerobot
conda install -c conda-forge ffmpeg git-lfs -y
git clone https://github.com/huggingface/lerobot.git
cd lerobot
pip install -e ".[feetech]"
```

### 2. 포트 확인
```bash
lerobot-find-port
```

### 3. 텔레오퍼레이션 실행
```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port=/dev/tty.usbmodem5AE60573201 \
  --robot.id=hdel_iot_01_follower_arm \
  --teleop.type=so101_leader \
  --teleop.port=/dev/tty.usbmodem5AE60537131 \
  --teleop.id=hdel_iot_01_leader_arm
```

---

## 📖 문서 가이드

| 문서 | 내용 |
|------|------|
| [Step 01 조립](산출물/step01_조립.md) | SO-ARM101 하드웨어 조립 |
| [Step 02 LeRobot 환경](산출물/step02_lerobot%20환경%20만들기.md) | 개발환경 설치 |
| [Step 03 Follower 확인](산출물/step03_SO-ARM%20101_Follower%20확인.md) | Follower 모터 셋업 & 캘리브레이션 |
| [Step 04 Leader 확인](산출물/step04_SO-ARM%20101_Leader.md) | Leader 모터 셋업 |
| [Step 05 텔레오퍼레이션](산출물/step05_텔레스코픽%20제어.md) | 텔레오퍼레이션 60Hz 구동 |
| [Step 06 카메라 (Top)](산출물/step06_카메라%20연결%20(top%20mount).md) | 오버헤드 카메라 연결 |
| [Step 07 카메라 (Gripper)](산출물/step07_카메라%20연결%20(gripper).md) | 그리퍼 카메라 연결 |

---

## 🔗 참고 자료

- [HuggingFace LeRobot](https://github.com/huggingface/lerobot)
- [SO-ARM100/101 공식](https://github.com/TheRobotStudio/SO-ARM100)
- [LeKiwi](https://github.com/SIGRobotics-UIUC/LeKiwi)
- [XLeRobot](https://xlerobot.readthedocs.io/en/latest/index.html)
- [Isaac Sim](https://developer.nvidia.com/isaac/sim)
- [LeIsaac (LeRobot+Isaac)](https://velog.io/@choonsik_mom/Leisaac-LeRobot-Gr00t-IsaacSim으로-입문하는-VLA-Finetuning)

---

## 👥 CoP 역할 분담

| 역할 | 담당 영역 |
|------|-----------|
| **Hardware Specialist** | 3D프린팅, 조립, 모터 유지보수 |
| **Embedded Interface Engineer** | Raspberry Pi/Jetson 환경, 모터 드라이버 |
| **AI & Simulation Researcher** | 모델 학습, Isaac Sim, Sim2Real |
| **CoP Facilitator** | 문서화, 일정 관리, 데모데이 |

---

*이 레포는 CoP 활동의 모든 연구/실습/샘플코드를 관리하는 중앙 저장소입니다.*  
*작업 진행상황은 [Todos.md](Todos.md) 에서 확인하세요.*
