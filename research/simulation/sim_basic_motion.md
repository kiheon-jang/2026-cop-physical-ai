# 🛠 [시뮬] 단순 동작 시연 — 2026-05-06

## 무엇을 했는지
- MuJoCo SO-ARM101 모델 (`so101_new_calib.xml`)을 로드하여 5초간 단순 Sine wave 패턴으로 관절을 움직이는 Python 스크립트 (`samples/training/sim_basic_motion.py`)를 작성했습니다.
- MuJoCo 뷰어를 통해 시뮬레이션을 시각화하려 했습니다.
- `so101_new_calib.xml` 파일 내의 정확한 관절 이름(`shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`)을 확인하고 스크립트에 반영했습니다.

## 어떻게 검증했는지 (스크린샷 또는 메트릭)
- `mjpython`을 사용하여 스크립트를 실행했지만, `Library not loaded: @executable_path/../lib/libpython3.14.dylib` 오류로 인해 MuJoCo 뷰어를 실행할 수 없었습니다.
- 시뮬레이션 동작 검증은 이 오류로 인해 수행하지 못했습니다.

## 다음 단계로 어떻게 이어지는지
- `mjpython`의 `libpython3.14.dylib` 로딩 문제를 해결해야 합니다.
- `claude -p` CLI가 `Invalid bearer token` 오류로 인해 현재 사용할 수 없는 상태이므로, 이 환경 문제는 Hermes Agent가 직접 해결하거나 사용자(장기헌)의 수동 개입이 필요할 수 있습니다.
- 이 문제가 해결되면 `sim_basic_motion.py` 스크립트의 시뮬레이션 동작을 시각적으로 확인하고, 다음 단계인 Joint limits 적용으로 넘어갈 수 있습니다.

## 오류 상세
```
failed to dlopen path '/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3': dlopen(/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3, 0x000A): Library not loaded: @executable_path/../lib/libpython3.14.dylib
  Referenced from: <4C4C44FF-5555-3144-A1EA-D9A84E365498> /Users/markmini/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14
  Reason: tried: '/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/lib/python3.14/site-packages/mujoco/MuJoCo_(mjpython).app/Contents/lib/libpython3.14.dylib' (no such file), '/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/../lib/libpython3.14.dylib' (no such file), '/usr/local/lib/libpython3.14.dylib' (no such file), '/usr/lib/libpython3.14.dylib' (no such file, not in dyld cache)
```
