# 시뮬 진척 — 자동 데이터 수집 스크립트 — 2026-05-27

## 오늘 진행 단계
Phase 0 - W4: 자동 데이터 수집 스크립트 (`samples/training/sim_data_collector.py`) 구현 및 50 에피소드 데이터 수집.

## 실행 테스트 결과
- `samples/training/sim_data_collector.py` 스크립트가 성공적으로 실행되어 `data/episodes` 디렉토리에 50개의 Pick-Place 시나리오 에피소드 데이터셋을 생성했습니다.
- 각 에피소드는 큐브의 초기 위치(x,y)를 랜덤하게 변동시켰습니다.
- LeRobot 데이터셋 형식으로 저장되었음을 확인했습니다.

## 관찰 / 이슈
- `claude -p` 호출 시 `allowedTools` 파라미터 누락으로 인한 초기 파일 편집 권한 거부 문제가 있었습니다. `--allowedTools 'Read,Edit,Write,Bash'`를 포함하여 해결했습니다.
- `SO-ARM100` MJCF 모델 경로가 하위 모듈 경로에 맞게 수정되었습니다.
- `mujoco.MjModel.from_xml_path`에서 큐브를 동적으로 추가하기 위해 임시 MJCF scene 파일을 생성하는 로직이 추가되었습니다.
- `LeRobotDataset` 초기화 및 데이터 저장 로직이 성공적으로 구현되었습니다.

## 다음 단계
Phase 0 - W4 (5/28~30): LeRobot Dataset 포맷으로 50 에피소드 합성 및 `info.json` + `data/chunk-000/` 구조 검증.
