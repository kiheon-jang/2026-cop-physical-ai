# Phase 0, W2 (5/12): 오버헤드 카메라 시뮬 셋업

## 작업 내용
SO-ARM101 MJCF 모델 파일 (`/Users/markmini/Documents/dev/2026-cop-physical-ai/SO-ARM100/Simulation/SO101/so101_new_calib.xml`)에 오버헤드 카메라를 추가했습니다.

카메라 정의:
```xml
<camera name='overhead_camera' mode='fixed' pos='0 0 1' xyaxes='1 0 0 0 1 0'/>
```
이 카메라는 `<worldbody>` 태그 바로 아래에 추가되어 시뮬레이션 환경의 상단에서 로봇을 내려다보는 시점을 제공합니다.

## 검증 방법
MJCF 파일 내용 (`so101_new_calib.xml`)을 `read_file`로 확인하고, `<worldbody>` 태그 안에 `<camera>` 태그가 성공적으로 추가되었음을 확인했습니다.

## 다음 단계
다음 단계는 `PHASE_ROADMAP.md`에 따라 그리퍼 카메라 시뮬을 추가하고 `mujoco.Renderer`로 RGB 이미지 추출을 검증하는 것입니다.
