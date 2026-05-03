# 🛠 [시뮬] 6-DoF 동작 확인 — 2026-05-03

## 무엇을 했는지
MuJoCo 시뮬레이터에서 TheRobotStudio SO-ARM101 MJCF 모델(`SO-ARM100/Simulation/SO101/so101_new_calib.xml`)의 6-DoF 관절 동작을 확인했습니다. 초기에는 `mujoco.viewer`를 사용하려 했으나 macOS 환경에서 `mjpython` 의존성 문제로 headless 렌더링 방식으로 전환했습니다.

`samples/training/sim_headless_6dof_video.py` 스크립트를 작성하여 모델을 로드하고, 각 관절에 5초 동안 사인파 형태의 움직임을 부여하여 30 FPS의 MP4 비디오(`research/simulation/video/sim_6dof_animation.mp4`)로 저장했습니다.

**주요 변경 사항:**
- `sim_viewer_6dof.py` 스크립트 작성 및 `mujoco.MjModel.from_xml_path()`, `mujoco.MjData()` API 수정.
- macOS `mjpython` 오류로 인해 `sim_headless_6dof_video.py` 스크립트 작성 및 `mujoco.mj_resetData()` API 수정.
- `imageio[ffmpeg]` 패키지 설치를 통해 MP4 비디오 저장 기능 활성화.

## 어떻게 검증했는지 (스크린샷 또는 메트릭)
스크립트 실행 시 콘솔 출력에서 "Video saved successfully." 메시지를 확인했습니다. 이는 5초 동안 6개 관절이 사인파 패턴으로 움직이는 시뮬레이션 영상이 `research/simulation/video/sim_6dof_animation.mp4` 경로에 성공적으로 생성되었음을 의미합니다.

*향후 시뮬레이션 비디오 링크 또는 스크린샷 추가 예정*

## 다음 단계로 어떻게 이어지는지
오늘 작업으로 SO-ARM101 모델의 기본 로드 및 6-DoF 관절의 애니메이션 구현이 가능함을 확인했습니다. 다음 단계(5/4)는 `research/simulation/PHASE_ROADMAP.md`에 명시된 "Joint limits 적용 (STS3215 사양: 360° 회전, 1.5Nm 토크)" 작업을 진행할 예정입니다. 이를 위해 MJCF 파일을 수정하고, 해당 제한이 시뮬레이션에 올바르게 반영되는지 검증할 것입니다.
