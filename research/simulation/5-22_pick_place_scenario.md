# 🛠 [시뮬] Pick-Place 시나리오 (큐브 1개) 시뮬 동작 — 2026-05-23

## 오늘 진행 단계
Phase 0 - W4 - Pick-Place 시나리오 (큐브 1개) 시뮬 동작

## 작업 내용
- `models/SO-ARM100/Simulation/SO101/so101_new_calib.xml` 파일에 50mm 정육면체 큐브 (질량 50g, 초기 위치 `pos="0.15 0 0.025"`) 추가. `body` 태그의 `mass` 속성 대신 `inertial` 태그를 사용하여 질량 정의.
- `samples/training/sim_pick_place.py` 파일 작성:
  - MuJoCo 3.x API 변경 사항 반영 (`mujoco.MjModel.from_xml_path`, `model.jnt().id`, `model.actuator().id`, `model.body().id`, `model.site().id`).
  - `imageio` 라이브러리를 사용하여 시뮬레이션 결과를 MP4 비디오로 저장.
  - Pick-Place 시나리오 로직 구현 (그리퍼 접근, 잡기, 들어 올리기, 놓기).

## 검증 결과
- `sim_pick_place.py` 실행 결과, `research/simulation/video/pick_place_demo.mp4` 파일에 시뮬레이션 비디오가 성공적으로 저장됨.
- 비디오를 통해 로봇팔이 큐브에 접근하여 잡고 들어 올리는 기본적인 Pick-Place 동작을 확인.

## 관찰 / 이슈
- MuJoCo 3.x 버전의 API 변경 사항으로 인해 여러 차례 코드 수정이 필요했음.
- 그리퍼의 제어 범위와 실제 동작 간의 미세 조정 필요.

## 다음 단계
- 5/25~27: 자동 데이터 수집 스크립트 (`samples/training/sim_data_collector.py`) 작성 및 50 에피소드 목표 달성.
