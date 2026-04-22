# Sim2Real 격차 해소 최신 기법

> 작성일: 2026-04-22 | 상태: 초안 (검수 전)

## 💡 한 줄 요약
2025~2026년 Sim2Real 격차 해소의 핵심 트렌드는 **생성형 고충실도 시뮬레이션(Digital Cousins)**, **VLA 전용 Sim2Real 파이프라인**, **시스템 식별 기반 물리 파라미터 매칭**으로 수렴하고 있으며, LeRobot + ManiSkill + Isaac Lab 조합이 오픈소스 표준으로 자리잡고 있다.

## 🔑 핵심 개념

1. **Digital Cousins (디지털 쌍둥이의 진화)**: 실제 환경의 파노라마 RGB 이미지 한 장에서 완전한 상호작용 가능한 디지털 환경을 자동 생성하는 파이프라인(WorldComposer). 기존 수동 에셋 제작 없이 다양성·현실감을 동시에 확보해 정책 일반화 성능을 끌어올림 (arXiv 2604.15805, April 2026).

2. **Sim2Real-VLA (도메인 필터링)**: VLA 모델이 시뮬레이션 특화 시각 정보에 과적합되는 문제를 해결하기 위해, 모션 임계 다이나믹스는 유지하고 환경 무관 시각 노이즈를 필터링하는 선택적 특징 주입 기법. 실물 실험에서 제로샷 Sim2Real 전이 성공률이 유의미하게 향상 (OpenReview ICLR 2025).

3. **RL-기반 Sim-Real Co-Training**: SFT(Supervised Fine-Tuning)로 실·시뮬 혼합 데모를 워밍업한 뒤 RL로 미세조정하는 2단계 파이프라인. VLA 정책의 시뮬 → 실환경 일반화에서 순수 모방학습 대비 최대 40%+ 성공률 향상 보고 (arXiv 2602.12628).

4. **PACE (데이터 기반 시스템 식별)**: ETH 취리히 Legged Robotics Lab이 공개한 오픈소스 프레임워크. 표준 조인트 엔코더만으로 액추에이터·관절 다이나믹스를 자동 식별해 물리 파라미터를 실제 로봇에 맞춤 설정함으로써 모델 불일치 문제를 원천 감소 (GitHub: leggedrobotics/pace-sim2real, 2025).

5. **Domain Randomization + 컨텍스트 배치**: 단순 무작위화보다 **컨텍스트 인식 오브젝트 배치** 전략이 효과적임이 입증. 조명·재질·위치를 완전 무작위화하면 시뮬 내 정책 품질이 저하되는 tradeoff가 있으므로 계층적 무작위화 적용이 권장됨.

6. **Real-to-Sim-to-Real (RialTo)**: 실제 환경을 먼저 디지털 트윈으로 복제한 뒤 그 안에서 RL 강화 → 다시 실물 배포하는 역방향 루프. 모방학습 정책을 디지털 트윈 RL로 강건화하는 접근 (real-to-sim-to-real.github.io).

## 📊 왜 우리 프로젝트에 중요한가

**SO-ARM101 + LeRobot** 기반 프로젝트에서 Sim2Real 격차는 두 가지 실용적 병목으로 나타남:

- **데이터 부족 문제**: 실물 데모 수집은 시간·비용이 크므로, 시뮬에서 대량 생성 후 실물 미세조정하는 전략이 핵심. `lerobot-sim2real` (ManiSkill + LeRobot 브릿지)가 이를 위한 오픈소스 파이프라인으로 주목받는 중.
- **물리 모델 불일치**: SO-ARM101의 서보 다이나믹스는 이상적 URDF 모델과 실제 마찰·백래시 간 차이가 크다. PACE 스타일 시스템 식별을 적용하면 시뮬 훈련 정책의 실물 성공률을 크게 높일 수 있음.
- **NVIDIA 공식 레퍼런스**: NVIDIA Isaac Lab 문서에 SO-101 전용 Sim2Real 튜토리얼(도메인 무작위화 + 실데이터 코트레이닝 2전략)이 공개돼 있어 직접 적용 가능.

## 🔍 상세 내용

### 1. Digital Cousins (WorldComposer) — April 2026 최신

arXiv 2604.15805 (2026-04-17 공개)는 파노라마 이미지 → 완전 상호작용 디지털 환경 자동 생성 시스템 **WorldComposer**를 소개. 주요 특징:
- 단일 RGB 파노라마만으로 물리 엔진 호환 씬 자동 재구성
- 실-시뮬 상관관계 실험으로 플랫폼 충실도 검증
- 대규모 데이터 스케일업 시 정책 일반화 성능 향상 확인
- RoboTwin 2.0 (강력한 도메인 무작위화 탑재 양팔 로봇 벤치마크)도 동시 주목

### 2. Sim2Real-VLA — 선택적 특징 주입

VLA 모델은 시뮬레이션 특화 시각 패턴(렌더링 아티팩트, 완벽한 조명 등)에 과적합되는 경향. Sim2Real-VLA는:
- 모션 임계(motion-critical) 다이나믹스 → 보존
- 환경 무관(environment-agnostic) 시각 노이즈 → 필터링
- 결과: 실물 제로샷 전이 성공률 유의미 향상

### 3. RL-기반 Sim-Real Co-Training (arXiv 2602.12628)

- **Stage 1**: 실+시뮬 혼합 시연으로 SFT 워밍업
- **Stage 2**: RL 미세조정으로 시뮬 → 실물 전이 최적화
- 순수 BC(행동복제) 대비 40%+ 성공률 향상 보고
- VLA 아키텍처에 범용 적용 가능한 2단계 설계

### 4. lerobot-sim2real (ManiSkill 브릿지)

GitHub `StoneT2000/lerobot-sim2real`: ManiSkill GPU 병렬 시뮬 → LeRobot 정책 → 실물 배포를 연결하는 오픈소스 파이프라인. SO-ARM 계열 로봇에 직접 적용 가능한 구조.

### 5. PACE 프레임워크 (ETH Zürich)

- 표준 조인트 엔코더로 액추에이터·관절 다이나믹스 자동 식별
- 진화 최적화 + 데이터 기반 시스템 식별 결합
- 다양한 족형 로봇에 적용 가능 (범용 설계)
- 2025년 9월 공개 후 빠른 커뮤니티 채택

### 6. NVIDIA Isaac Lab SO-101 공식 튜토리얼

NVIDIA 문서에서 SO-101 전용 Sim2Real 2전략 공개:
- **Strategy 1**: 도메인 무작위화 + 원격조작 시연
- **Strategy 2**: 실데이터 코트레이닝 (소량 실물 데이터로 시뮬 정책 보정)

## 🔗 출처

- [Digital Cousins (WorldComposer) — arXiv 2604.15805, April 2026](https://arxiv.org/abs/2604.15805)
- [Sim2Real-VLA — OpenReview](https://openreview.net/pdf?id=H4SyKHjd4c)
- [RL-based Sim-Real Co-Training — arXiv 2602.12628](https://arxiv.org/html/2602.12628v3)
- [lerobot-sim2real (ManiSkill + LeRobot)](https://github.com/StoneT2000/lerobot-sim2real)
- [PACE Sim2Real Framework — ETH Zürich](https://github.com/leggedrobotics/pace-sim2real)
- [NVIDIA Isaac Lab SO-101 Sim2Real Strategy 1](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/09-strategy1-dr-teleop.html)
- [NVIDIA Isaac Lab SO-101 Sim2Real Strategy 2](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/13-strategy2-cotraining.html)
- [NVIDIA Blog: Bridging Sim-to-Real Gap (Isaac Lab, May 2025)](https://developer.nvidia.com/blog/bridging-the-sim-to-real-gap-for-industrial-robotic-assembly-applications-using-nvidia-isaac-lab/)
- [Reducing Sim2Real Gap — NVIDIA GTC 2026](https://www.nvidia.com/en-us/on-demand/session/gtc26-ex82340/)
- [Abstract Sim2Real via Approximate Information States — arXiv 2604.15289](https://arxiv.org/html/2604.15289v1)
- [AwesomeSim2Real 큐레이션 리포](https://github.com/LongchaoDa/AwesomeSim2Real)
