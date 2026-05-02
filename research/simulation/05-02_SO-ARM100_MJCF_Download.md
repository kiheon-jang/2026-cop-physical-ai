# 🛠 [시뮬] SO-ARM100 MJCF 모델 다운로드 — 2026-05-02

## 무엇을 했는지
SO-ARM100 MJCF 모델을 GitHub 저장소에서 클론하여 로컬 프로젝트(`/Users/markmini/Documents/dev/2026-cop-physical-ai/SO-ARM100`)에 성공적으로 다운로드했습니다.

- **명령어**: `git clone https://github.com/TheRobotStudio/SO-ARM100.git`
- **위치**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/SO-ARM100`

## 어떻게 검증했는지 (스크린샷 또는 메트릭)
터미널 출력에서 `Cloning into 'SO-ARM100'...` 메시지와 성공적인 종료 코드 0을 확인했습니다. 현재 파일 시스템에서 `SO-ARM100` 디렉토리 존재 여부를 추가로 검증할 예정입니다.

## 다음 단계로 어떻게 이어지는지
다음 단계는 `PHASE_ROADMAP.md`에 따라 "5/3: viewer로 6-DoF 동작 확인 (`python -m mujoco.viewer --mjcf=...`)" 작업을 수행할 예정입니다. 이를 위해 다운로드된 MJCF 파일을 사용하여 MuJoCo viewer에서 로봇 모델이 정상적으로 로드되고 6-DoF 관절 동작이 가능한지 확인할 것입니다.
