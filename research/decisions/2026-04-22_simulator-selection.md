# [결정] 시뮬레이터 선택 — Phase 0~5 전체 로드맵

- **날짜**: 2026-04-22 (사전 조사) / **2026-05-01 최종 확정**
- **결정**: ✅ 채택
  - **Phase 0~5 (메인)**: MuJoCo 3.x (Apple Silicon 네이티브)
  - **Phase 3+ (차년도, 대규모 RL)**: Isaac Lab (NVIDIA GPU 별도 서버)
- **결정자**: Hermes Agent (AI 조사) + 사용자 (확정)
- **적용 시기**: Phase 0 (2026-05) 시작, 진행 중

> **2026-05-01 변경 사유**: Mac Mini M5 (Apple Silicon)에서 Isaac Lab 미지원 확인 → MuJoCo로 메인 시뮬레이터 변경. Isaac Lab은 차년도 별도 GPU 서버 도입 시 사용.

---

## 배경

Phase 3에서 SO-ARM101을 시뮬레이션 강화학습(RL)으로 학습하기 위한 시뮬레이터를 선택해야 함.
초기 가정은 NVIDIA Orin Nano Super에서 Isaac Sim을 구동하는 것이었으나, 하드웨어 제약으로 검토 필요.

---

## 검토 내용

### Orin Nano Super 호환성

- **❌ Isaac Sim/Lab 직접 구동 불가**
  - Isaac Sim은 x86_64 전용 (ARM64 미지원)
  - 8GB 공유 메모리는 Isaac Sim 최소 VRAM 요구사항(8GB 전용 VRAM) 미달
  - Orin Nano Super는 임베디드 AI 추론 전용 설계 (학습 아님)
- **결론**: Orin Nano Super = **배포 전용** 타겟 (Sim-to-Real 전이 후 정책 추론만)

### 시뮬레이터별 장단점

#### Isaac Lab (✅ Phase 3 메인 선택)
- 장점:
  - SO-ARM101 공식 외부 프로젝트 존재 ([isaac_so_arm101](https://github.com/MuammerBay/isaac_so_arm101))
  - GPU 병렬 환경으로 빠른 RL 학습 (수천 개 환경 동시)
  - LeIsaac를 통한 LeRobot 완전 연동 (텔레오퍼레이션 → 데이터 수집 → GR00T 파인튜닝)
  - BSD-3-Clause 오픈소스
  - AWS/GCP/Azure 클라우드 자동 배포 (Isaac Automator)
- 단점:
  - 설치 복잡 (Isaac Sim 기반, 50GB+ 스토리지)
  - 최소 RTX 3070 / 8GB VRAM 필요
  - ARM64 (Orin) 미지원 → 로컬 or 클라우드 별도 필요
- 비용/복잡도: 중-높음

#### MuJoCo (✅ 프로토타이핑 대안)
- 장점:
  - pip install mujoco로 즉시 설치
  - SO-101 MuJoCo 환경 존재 (gym-so100-c, 2025-08)
  - LeRobot 데이터셋 직접 활용 가능
  - Google Colab / 낮은 사양 GPU에서 동작
  - Apache 2.0 라이선스
- 단점:
  - 병렬 환경 확장은 MJX(JAX) 필요
  - 포토리얼리스틱 렌더링 없음 (시각 센서 테스트 제한)
- 비용/복잡도: 낮음

#### Isaac Sim (⏸️ 보류 — 필요 시 검토)
- 포토리얼리스틱 렌더링, 복잡한 씬 필요할 때만 사용
- Isaac Lab의 상위 플랫폼으로 현재는 오버킬

---

## 결정 근거

1. **SO-ARM101 + LeIsaac + GR00T 파이프라인**이 이미 검증된 end-to-end 경로로 확립됨
2. Isaac Lab이 Phase 3 RL 학습 및 Sim-to-Real 전이에 가장 적합한 프레임워크
3. MuJoCo는 팀 내 GPU 리소스 제약 시 빠른 알고리즘 검증용으로 병행 활용
4. 클라우드(AWS g5.2xlarge ~$1.21/hr)로 Isaac Lab 실행 가능 → 로컬 RTX GPU 없어도 진행 가능

---

## 최종 결정

| 용도 | 선택 |
|------|------|
| Phase 3 메인 RL 학습 | ✅ **Isaac Lab** (LeIsaac 연동) |
| 빠른 알고리즘 프로토타이핑 | ✅ **MuJoCo** (gym-so100-c) |
| GR00T 파인튜닝 | ✅ **LeIsaac pipeline** (Isaac Lab 수집 데이터 활용) |
| 최종 배포 타겟 | ✅ **Orin Nano Super** (추론 전용) |
| 클라우드 환경 | ✅ **AWS g5.2xlarge** (Isaac Automator 활용) |

---

## 다음 액션

- [ ] **담당**: 팀원 → Isaac Lab + LeIsaac 설치 환경 구성 (로컬 RTX GPU or AWS g5)
- [ ] **담당**: 팀원 → [isaac_so_arm101](https://github.com/MuammerBay/isaac_so_arm101) SO-ARM101 Reach 태스크 실행 검증
- [ ] **담당**: 팀원 → LeIsaac 텔레오퍼레이션 데이터 수집 파이프라인 테스트
- [ ] **담당**: 팀원 → AWS g5.2xlarge Isaac Automator 배포 테스트 (비용 모니터링)
- [ ] **담당**: 팀원 → GR00T N1.5 파인튜닝 환경 요구사항 확인 (~25GB VRAM 또는 `--no-tune_diffusion_model`)

---

## 관련 리서치

- `docs/07_simulation-rl/README.md` — 전체 사전 조사 결과
- [LeIsaac GitHub](https://github.com/LightwheelAI/leisaac)
- [SO-ARM101 Isaac Lab 프로젝트](https://github.com/MuammerBay/isaac_so_arm101)
- [GR00T N1.5 SO-101 튜토리얼](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning)
- [Isaac Lab 클라우드 배포](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/cloud_installation.html)
