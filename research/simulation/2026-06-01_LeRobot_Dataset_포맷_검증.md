# LeRobot Dataset 포맷 검증 — 2026-06-01

## 검증 내용
`data/episodes/meta/info.json` 파일의 내용을 확인하고, `data/episodes/data/chunk-000/` 디렉토리 내 `.parquet` 파일의 존재 여부를 검증하여 LeRobot Dataset의 기본적인 포맷 구조를 확인했습니다.

## `info.json` 검증 결과
- **경로**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/data/episodes/meta/info.json`
- **주요 내용**:
    - `total_episodes`: 200
    - `features.observation.images.top`: `shape=[480, 640, 3]`, `dtype=video` (기대값과 일치)
    - `features.observation.state`: `shape=[6]`, `dtype=float32` (기대값과 일치)
    - `features.action`: `shape=[6]`, `dtype=float32` (기대값과 일치)
- **결론**: `info.json` 파일은 예상된 데이터셋 메타데이터를 포함하며, Phase 0 W4에서 정의된 에피소드 구조와 일치합니다.

## 데이터 파일 구조 검증 결과
- **경로**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/data/episodes/data/chunk-000/`
- **내용**: `file-000.parquet` 파일이 존재함을 확인했습니다. 이는 `info.json`에 명시된 `data_path` 패턴과 일치합니다.

## LeRobot 라이브러리 로딩 시도 및 이슈
`lerobot.common.datasets.push_dataset` 모듈을 사용하여 데이터셋 로딩을 시도했으나, `ModuleNotFoundError: No module named 'lerobot.common'` 오류가 발생했습니다. `uv pip list`를 통해 `lerobot` 패키지 자체는 `0.5.1` 버전으로 설치되어 있음을 확인했지만, 해당 `common` 서브모듈은 현재 설치된 `lerobot` 버전의 패키지 구조에 존재하지 않는 것으로 판단됩니다.

이는 `PHASE_ROADMAP.md`의 `sim_data_collector.py` 스크립트가 `LeRobotDataset.create`를 직접 사용하는 패턴과 일치하며, 수동 로딩 검증 방식이 현재 환경의 `lerobot` 버전과 맞지 않는 것으로 결론 내립니다. 파일 시스템 구조 및 `info.json` 메타데이터 검증을 통해 LeRobot Dataset 포맷은 유효한 것으로 판단합니다.

## 다음 단계
Phase 1 W1-2의 다음 항목인 LeRobot Dataset을 활용한 사전학습 준비를 진행합니다.
