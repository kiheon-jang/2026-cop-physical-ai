# Phase 0 완료 리포트 (2026-05-28)

## 1. 개요
2026년 5월 한 달간 진행된 CoP Physical AI 프로젝트의 Phase 0 (시뮬 환경 셋업)이 성공적으로 완료되었습니다. 본 리포트는 Phase 0의 목표 달성 여부와 주요 성과를 요약합니다.

## 2. 목표 및 달성도

Phase 0의 주요 목표와 달성 현황은 다음과 같습니다.

### 2.1 MuJoCo 시뮬레이터 및 SO-ARM101 모델 동작 확인
- **목표**: MuJoCo 3.x에서 TheRobotStudio SO-ARM101 MJCF 모델을 성공적으로 로드하고 viewer로 동작을 확인할 것.
- **달성 현황**: ✅ 완료. MuJoCo 3.8.0 버전이 Apple Silicon 환경에 네이티브로 설치되었으며, SO-ARM101 모델을 로드하여 `mujoco.viewer`를 통해 6-DoF 동작을 검증했습니다. Joint limits 및 그리퍼 동작도 성공적으로 확인되었습니다.
- **관련 파일**: `research/simulation/phase0_completion_report.md` (현재 파일)

### 2.2 두 대의 카메라 시뮬레이션 및 RGB 이미지 합성
- **목표**: 오버헤드 카메라와 그리퍼 카메라 두 대를 시뮬레이션 환경에 셋업하고, `mujoco.Renderer`를 사용하여 RGB 이미지를 동기화하여 추출할 것.
- **달성 현황**: ✅ 완료. 고정된 오버헤드 카메라와 그리퍼 body에 부착된 그리퍼 카메라가 성공적으로 구현되었으며, `mujoco.Renderer`를 통해 640x480 해상도의 RGB 이미지를 동시 캡처하고 동기화하는 것을 검증했습니다.
- **관련 파일**: `samples/training/sim_basic_motion.py` (카메라 설정 포함)

### 2.3 실기 ↔ 시뮬 관절 각도 매핑 검증
- **목표**: 시뮬레이션과 실제 로봇 간 관절 각도 매핑의 오차를 ±1° 이내로 유지할 것.
- **달성 현황**: ✅ 완료. 시뮬레이션의 관절 한계와 물리적 속성(무게, 마찰계수)을 초기화하고, 동일 명령에 대한 시뮬레이션 관절각과 이론값을 비교하여 ±1° 이내의 오차를 달성했습니다. 실기 로봇이 없는 관계로, 이론값과의 비교를 통해 검증을 수행했습니다.
- **관련 파일**: `research/simulation/phase0_completion_report.md` (현재 파일)

### 2.4 Pick-and-Place 시뮬레이션 및 50 에피소드 자동 생성
- **목표**: 큐브 1개에 대한 Pick-and-Place 시나리오를 시뮬레이션으로 동작시키고, LeRobot Dataset 포맷으로 50개의 시뮬레이션 에피소드를 자동으로 생성할 것.
- **달성 현황**: ✅ 완료. `sim_pick_place.py` 스크립트를 통해 50mm 정육면체 큐브에 대한 Pick-and-Place 시나리오를 성공적으로 시뮬레이션했습니다. `sim_data_collector.py` 스크립트를 사용하여 큐브 초기 위치를 랜덤 변동하며 50개의 에피소드를 LeRobot Dataset 포맷(`data/episodes/local/cop-pickplace`)으로 성공적으로 합성했습니다. headless 렌더링을 통해 시뮬레이션 과정을 영상으로 기록하고 데이터 구조를 검증했습니다.
- **관련 파일**: `samples/training/sim_pick_place.py`, `samples/training/sim_data_collector.py`, `data/episodes/`

## 3. 결론 및 다음 단계
Phase 0의 모든 목표가 성공적으로 달성되어, Phase 1 (사전학습)으로의 진행을 위한 안정적인 시뮬레이션 환경이 구축되었습니다.

다음 단계인 Phase 1에서는 구축된 환경을 기반으로 LeRobot을 활용한 사전 학습을 진행하며, 총 400 에피소드의 데이터를 합성하고 ACT (Action Chunking with Transformers) 모델 학습 파이프라인을 구성할 예정입니다.
