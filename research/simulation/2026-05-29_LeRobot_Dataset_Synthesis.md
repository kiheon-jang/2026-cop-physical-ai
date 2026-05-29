# LeRobot 데이터셋 50 에피소드 합성 — 2026-05-29 (목)

## 개요
Phase 0, Week 4의 일환으로 LeRobot 데이터셋 포맷에 맞춰 Pick-and-Place 시뮬레이션 50 에피소드를 성공적으로 합성했습니다. `sim_data_collector.py` 스크립트를 사용하여 데이터 수집을 진행했습니다.

## 실행 결과
- 스크립트: `samples/training/sim_data_collector.py`
- 에피소드 수: 50
- 저장 경로: `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes`
- 주요 수집 항목: `observations.images.top` (640x480 RGB), `observations.state` (6DoF qpos), `actions` (6DoF ctrl), `timestamps`
- 큐브 초기 위치 랜덤 변동: x±20mm, y±20mm 적용됨.

## 관찰 / 이슈
- 50 에피소드 데이터 수집 성공.
- [자가치유] `research/simulation/` 경로 파일 누락 복구로 이 파일 생성됨.

## 다음 단계
- `info.json` 및 `data/chunk-000/` 구조 검증.
- Phase 0 완료 리포트 작성.