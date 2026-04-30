---
tags: [MuJoCo, Installation, SO-ARM100, Simulation, AppleSilicon, macOS]
---

# MuJoCo 및 SO-ARM100 모델 설치 보고서

**작성일**: 2026-05-01

## 1. MuJoCo Python 바인딩 설치

Mac mini M5 (Apple Silicon) 환경에 MuJoCo 3.8.0 Python 바인딩이 성공적으로 설치되었습니다.

*   **설치 위치**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/lib/python3.14/site-packages/mujoco`
*   **설치 명령**: `cd /Users/markmini/Documents/dev/2026-cop-physical-ai && uv venv && source .venv/bin/activate && uv pip install mujoco`
*   **검증 명령**: `python3 -c "import mujoco; print(f'version: {mujoco.__version__}'); m=mujoco.MjModel.from_xml_string('<mujoco/>'); print('OK')"`
*   **검증 결과**: `version: 3.8.0`, `OK` 출력 확인.

**특이사항**: MuJoCo 3.x 버전은 별도의 환경 변수 설정 (MUJOCO_PATH, DYLD_LIBRARY_PATH 등)이 필요 없으며, `uv`를 통해 프로젝트 가상 환경 내에 직접 바이너리가 내장되어 설치됩니다.

## 2. `.zshrc` 파일 정리

이전에 잘못 설정되었던 MuJoCo 관련 환경 변수 설정 8줄이 `.zshrc` 파일에서 성공적으로 삭제되었습니다.

*   **검증 명령**: `grep -c MUJOCO ~/.zshrc`
*   **검증 결과**: `0` 출력 확인.

## 3. SO-ARM100 MJCF 모델 다운로드

Phase 0 W1 D2 작업의 일환으로 SO-ARM100 MJCF 모델이 다음 경로에 성공적으로 다운로드되었습니다.

*   **저장 위치**: `/Users/markmini/dev/so-arm100-models`
*   **다운로드 명령**: `git clone https://github.com/TheRobotStudio/SO-ARM100.git /Users/markmini/dev/so-arm100-models`

## 4. 향후 작업 지침

모든 시뮬레이션 및 학습 명령은 반드시 `/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/activate` 가상 환경을 활성화한 후 실행되어야 합니다.
