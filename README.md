# 🤖 2026 CoP Physical AI — 첫걸음

> **사내 CoP(Community of Practice)** — Physical AI / Embodied AI 기술 내재화 프로젝트  
> SO-ARM101 로봇팔을 기반으로 모방학습 → 강화학습 → 모바일 매니퓰레이터까지 단계적으로 진행

---

## 📌 프로젝트 목표

> 상세 주차별 계획: [research/simulation/PHASE_ROADMAP.md](research/simulation/PHASE_ROADMAP.md)

| 단계 | 목표 | 상태 |
|------|------|------|
| **Phase 0 (5월)** | MuJoCo 시뮬 환경 셋업 + 자동 데이터셋 | ✅ 완료 |
| **Phase 1 (6월)** | 시뮬 데이터 합성 + ACT 사전학습 파이프라인 | ✅ 92% (Orin 배포만 시연 단계로 보류) |
| **Phase 2 (7월)** | Sim2Real 검증 — sim pick&place **4-seed 1.0 결착** | 🔄 71% (실기 검증은 Phase 3 W4 이관) |
| **Phase 3 (8월)** | **S1 리셋버튼 시뮬 (실기 트랙 정렬)** — 합성 데이터 + LED 자동판정 | 🔄 진행중 |
| **Phase 4 (9월)** | RS232 케이블 연결 + 1차 기능 완성 | ⏳ 예정 |

**투 트랙 체제 (2026-08-05~)**: 시뮬 트랙(이 레포, Mac) ↔ **실기 트랙**([deois/soarm_lerobot](https://github.com/deois/soarm_lerobot), omen · RTX 2080 Ti) — 실기가 S1 리셋버튼을 실물로 진행, 시뮬이 합성 데이터·성공판정 검증으로 지원.

### 최종 학습 목표 태스크
- 🎯 **1단계**: 물체 이동 (Pick & Place) — **시뮬 결착 (4-seed 1.0)**
- 🎯 **2단계**: PCB 제품의 리셋 & DIP S/W 조정 — **S1 리셋버튼 진행 중 (시뮬 + 실기)**
- 🎯 **3단계**: PCB의 RS232 포트에 HHT(Hand Held Terminal) 꽂기

---

<!-- AUTO_STATUS_START -->
## 📊 시뮬레이션 트랙 현황

> 매일 07:00 자동 업데이트 (generate_daily_report.py)
> **현재 Phase** = 달력 기준 구간 · **실제 진척** = PHASE_ROADMAP.md 체크박스 기준

| 항목 | 내용 |
|------|------|
| **현재 Phase (달력)** | Phase 3 — 8월 S1 리셋버튼 시뮬 (실기 정렬) |
| **실제 진척** | Phase 3 — S1 리셋버튼 시뮬 (실기 정렬) · 진척 66% · 시간 경과 72% |
| **마지막 업데이트** | 2026-08-19 |
| **다음 마일스톤** | 오늘 2026-08-19 · Phase 종료 8/31 |
| **최근 작업** | 📊 [로그] 2026-08-18 시뮬 테스트 — W2 종료일 S1 hold 독립 재검증(pcb 4/4·6do |
<!-- AUTO_STATUS_END -->

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
