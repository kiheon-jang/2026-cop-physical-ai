# Phase 0 - W1: Joint Limits 적용 (2026-05-04)

## 무엇을 했는가
SO-ARM101 로봇팔의 MuJoCo MJCF 모델인 `SO-ARM100/Simulation/SO101/so101_new_calib.xml` 파일에 STS3215 서보 모터의 사양에 맞춰 관절 제한(joint limits)과 토크(torque) 값을 적용했습니다.

### 변경 내용 요약
- `sts3215` 기본 클래스의 `position` 액추에이터 `forcerange`를 `-2.94 2.94`에서 `-1.5 1.5`로 변경 (1.5Nm 토크 반영).
- `hinge` 타입의 모든 관절 (`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`)의 `range` 속성을 `-3.14159 3.14159`로 변경 (360도 회전 범위, 약 -180도 ~ +180도 라디안).
- 모든 `position` 액추에이터의 `forcerange`를 `-1.5 1.5`로, `ctrlrange`를 `-3.14159 3.14159`로 업데이트.

## 어떻게 검증했는가
`claude-code` 에이전트가 MJCF 파일을 수정하고, 변경된 파일 내용을 출력하여 관절 범위와 토크 값이 올바르게 적용되었음을 확인했습니다. (현재 단계에서는 MuJoCo 시뮬레이터에서 직접 로드하여 동작 검증하는 것은 다음 단계에서 진행될 예정입니다.)

## 다음 단계
그리퍼 추가 및 그리퍼 동작 확인 (PHASE_ROADMAP.md의 5/5일 작업).
