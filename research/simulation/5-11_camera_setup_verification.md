# 5/11: 카메라 2대 시뮬 셋업 및 RGB 이미지 추출 검증

## 🗓️ 오늘 진행한 단계
Phase 0, W2 (5/8 ~ 5/14)의 "그리퍼 카메라 시뮬 추가" 및 "mujoco.Renderer로 RGB 이미지 추출 검증" 단계를 진행했습니다.

## 🛠️ 작업 내용
1.  `models/SO-ARM100/Simulation/SO101/so101_new_calib.xml` MJCF 파일에 오버헤드 카메라와 그리퍼 카메라를 추가했습니다.
    -   **오버헤드 카메라**: `worldbody` 태그 안에 `name="overhead_camera", mode="fixed", pos="0 0 1.0", quat="1 0 0 0", fovy="45"` 속성으로 추가.
    -   **그리퍼 카메라**: `<body name="gripper">` 태그 안에 `name="gripper_camera", mode="fixed", pos="0 0 0.05", quat="1 0 0 0", fovy="60"` 속성으로 추가.
    -   XML 스키마 오류를 해결하기 위해 `width`, `height`, `contype`, `conaffinity` 속성은 제거했습니다.

2.  카메라 이미지 추출을 검증하기 위한 Python 스크립트 `samples/training/sim_camera_verification.py`를 작성했습니다.
    -   `mujoco.MjModel`을 로드하고 `mj.mj_name2id`를 사용하여 카메라 ID를 가져왔습니다.
    -   `mujoco.Renderer`를 사용하여 각 카메라(`overhead_camera`, `gripper_camera`)에서 RGB 이미지를 획득하도록 설정했습니다.
    -   시뮬레이션 1초 동안 30프레임의 이미지를 캡처하여 `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/` 디렉토리에 PNG 파일로 저장했습니다.

## ✅ 검증 결과
-   MJCF 파일에 카메라 정의가 성공적으로 추가되었습니다.
-   `sim_camera_verification.py` 스크립트가 오류 없이 실행되었으며, 지정된 디렉토리에 30프레임의 오버헤드 및 그리퍼 카메라 이미지가 성공적으로 저장되었습니다.
-   `mjpython` 관련 환경 오류 및 MJCF 카메라 태그의 잘못된 속성 사용 문제를 해결했습니다.

## ➡️ 다음 단계로 이어지는 방법
다음 단계는 W2 (5/8 ~ 5/14)의 남은 항목인 "카메라 캘리브레이션 파라미터 적용 (FOV, 해상도)" 및 "두 카메라 동시 캡처 + 동기화 검증"을 진행할 예정입니다. 특히 `mujoco.Renderer`에서 `height`와 `width`를 올바르게 설정하여 캘리브레이션 파라미터 적용의 기반을 마련할 것입니다.

## 🖼️ 산출물 (스크린샷 또는 메트릭)
-   **MJCF 파일 수정 Diff**: (Git Commit에 포함)
-   **생성된 이미지 파일**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/` 디렉토리 내 `overhead_frame_*.png`, `gripper_frame_*.png`

## 🔗 외부 의존성
-   현재 단계에서 새로운 외부 의존성은 발견되지 않았습니다.

## ⚠️ 특이사항
-   `claude` CLI의 인증 실패로 인해 MJCF 파일 수정은 `patch` 도구를 사용하여 수동으로 진행했습니다.
-   `mujoco.viewer.launch_passive` 함수가 macOS 환경에서 `mjpython`을 요구하는 문제를 피하기 위해 `mujoco.Renderer`를 통한 오프스크린 렌더링 방식으로 스크립트를 변경했습니다.
