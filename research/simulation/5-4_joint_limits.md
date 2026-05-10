# 🛠 [시뮬] Joint limits 적용 — 2026-05-10

## 무엇을 했는지
SO-ARM101 MJCF 파일인 `models/SO-ARM100/Simulation/SO101/so101_new_calib.xml`에 STS3215 서보 모터의 사양에 따라 관절 한계를 360도 회전(`-3.1415926535 3.1415926535` 라디안)으로 적용했습니다. `gripper` 조인트는 물리적 한계를 고려하여 기존 범위인 `-0.17453297762778586 1.7453291995659765`를 유지했습니다.

수정된 조인트 목록:
- `shoulder_pan`: `range` 및 `ctrlrange` 업데이트
- `shoulder_lift`: `range` 및 `ctrlrange` 업데이트
- `elbow_flex`: `range` 및 `ctrlrange` 업데이트
- `wrist_flex`: `range` 및 `ctrlrange` 업데이트
- `wrist_roll`: `range` 및 `ctrlrange` 업데이트
- `gripper`: `ctrlrange` 업데이트 (range는 기존 유지)

## 어떻게 검증했는지
파일의 각 조인트에 대한 `range` 및 `actuator` 섹션의 `ctrlrange` 속성을 수동으로 확인하여 변경 사항이 올바르게 적용되었는지 확인했습니다.

## 다음 단계로 어떻게 이어지는지
다음 단계는 그리퍼를 추가하고 그리퍼 동작을 확인하는 것입니다. 이후 단순 동작 시연 스크립트를 작성하여 viewer로 동작을 검증할 예정입니다.
