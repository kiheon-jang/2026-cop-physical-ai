# Phase 0 완료 리포트 - 2026-05-29

## 개요
Phase 0 (2026년 5월)에서는 CoP Physical AI 프로젝트의 MuJoCo 시뮬레이션 환경 구축 및 핵심 기능 검증을 완료했습니다. 목표했던 4가지 주요 기준을 모두 달성하였으며, 6월 Phase 1 (사전학습)으로의 성공적인 전환을 위한 기반을 마련했습니다.

## Phase 0 목표 달성 현황

### 1. MuJoCo에서 SO-ARM101이 viewer로 동작
- **달성**: ✅
- **상세**:
    - MuJoCo 3.8.0 버전이 Apple Silicon (Mac Mini M5) 환경에 성공적으로 설치되었습니다.
    - TheRobotStudio/SO-ARM100 MJCF 모델을 다운로드하여 MuJoCo viewer에서 6-DoF 동작을 확인했습니다.
    - STS3215 서보 모터의 사양에 맞춰 Joint limits를 적용하고 그리퍼를 추가하여 정상 동작을 검증했습니다.
    - `samples/training/sim_basic_motion.py` 스크립트를 통해 단순 동작 시연을 성공적으로 수행했습니다.

### 2. 카메라 2대 RGB 이미지 합성 가능
- **달성**: ✅
- **상세**:
    - 오버헤드 카메라와 그리퍼 카메라를 MJCF 모델에 추가하여 시뮬레이션 환경에서 2대 카메라의 RGB 이미지 합성을 성공적으로 구현했습니다.
    - `mujoco.Renderer`를 사용하여 두 카메라의 이미지를 동시 캡처하고 동기화되는 것을 검증했습니다.
    - 기본 카메라 파라미터(fovy=45, 640x480)를 적용하여 이미지 품질을 확인했습니다.

### 3. 시뮬-실기 관절각 오차 ±1° 이내
- **달성**: ✅
- **상세**:
    - 시뮬레이션 관절 한계와 실기 캘리브레이션 값을 비교하고, 시뮬레이션 모델의 무게 및 관성 값을 조정했습니다.
    - 동일 명령에 대한 시뮬레이션과 실기 로봇의 관절각을 비교했을 때, 목표했던 ±1° 이내의 오차 범위 내에 들어옴을 확인했습니다.
    - 마찰계수 튜닝을 통해 시뮬레이션의 물리적 정확도를 향상시켰습니다.

### 4. Pick-Place 50 시뮬 에피소드 자동 생성
- **달성**: ✅
- **상세**:
    - Pick-Place 시나리오 (50mm 큐브 1개)를 MuJoCo headless 렌더링 방식으로 성공적으로 구현했습니다.
    - `samples/training/sim_pick_place.py` 스크립트를 통해 그리퍼가 큐브에 접근하여 들어올리는 동작을 검증하고, `research/simulation/video/pick_place_demo.mp4` 비디오로 저장했습니다.
    - `samples/training/sim_data_collector.py` 스크립트를 개발하여 LeRobot Dataset 포맷으로 50 에피소드의 시뮬레이션 데이터를 자동으로 수집했습니다. 각 에피소드에는 `observations.images.top`, `observations.state`, `actions`, `timestamps` 정보가 포함되었으며, 큐브의 초기 위치를 랜덤 변동시켜 데이터 다양성을 확보했습니다.
    - 생성된 데이터는 `data/episodes/` 경로에 `info.json` 및 `data/chunk-000/` 구조로 저장되었으며, 50 에피소드 수집 완료를 확인했습니다.

## 다음 단계 (Phase 1 준비)
Phase 0의 성공적인 완료를 바탕으로, 6월 Phase 1에서는 LeRobot을 활용한 ACT(Action Chunking with Transformers) 사전학습을 진행할 예정입니다. 이를 위해 추가 시뮬레이션 데이터 수집 및 학습 파이프라인 구성에 집중할 것입니다.

---
**기록:** 2026-05-29 (금)
**작성자:** Hermes Agent (자동 생성)
