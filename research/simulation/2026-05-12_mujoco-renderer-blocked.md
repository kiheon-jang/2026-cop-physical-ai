# 🛠 [시뮬] MuJoCo Renderer 검증 — 2026-05-12

## 무엇을 했는지
오늘의 시뮬 환경 구축 단계인 "`mujoco.Renderer`로 RGB 이미지 추출 검증" 작업을 시도했습니다.

## 진행 상황
- `mjpython` 실행 시 `Library not loaded: @executable_path/../lib/libpython3.14.dylib` 오류로 인해 MuJoCo 뷰어 및 `mujoco.Renderer`를 통한 이미지 추출 검증이 불가능합니다.
- 또한, 무거운 작업을 위임하는 `claude -p` 명령어에서도 `Invalid bearer token` 오류가 발생하여 Claude Code CLI를 사용할 수 없는 상황입니다.

## 어떻게 검증했는지
- `.venv/bin/python3 -c "import mujoco; print(mujoco.__version__)"` 명령을 통해 MuJoCo Python 패키지 설치 여부를 확인하려 했으나, 보안 정책으로 인해 직접 스크립트 실행이 차단되었습니다.
- `PHASE_ROADMAP.md` 상에는 MuJoCo 3.8.0이 설치되어 있다고 명시되어 있으나, `mjpython` 자체의 라이브러리 로딩 문제로 인해 런타임 환경에 문제가 있는 것으로 보입니다.

## 다음 단계로 어떻게 이어지는지
현재 `mjpython` 및 `claude -p` 관련 환경 설정 오류로 인해 시뮬레이션 환경 구축의 핵심 단계들이 차단된 상태입니다. 다음 단계인 "카메라 캘리브레이션 파라미터 적용" 등은 `mujoco.Renderer`가 정상 작동해야 진행 가능합니다.

이 문제는 사용자 개입을 통해 `agent/external-dependencies.md`에 명시된 `claude configure` 및 `mjpython` 라이브러리 로딩 문제 해결이 시급합니다.