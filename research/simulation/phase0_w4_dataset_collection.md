# Phase 0 - W4: LeRobot Dataset 포맷으로 50 에피소드 합성

## 작업 내용
`samples/training/sim_data_collector.py` 스크립트를 실행하여 SO-ARM101 로봇팔의 Pick-Place 시뮬레이션 데이터를 수집하고, LeRobot 데이터셋 형식으로 저장했습니다. 큐브의 초기 위치는 각 에피소드마다 x, y 방향으로 ±20mm 랜덤하게 변동되었습니다. 총 50개의 에피소드를 수집하는 것을 목표로 했습니다.

## 검증 결과
- **총 소요 시간**: 87.5초 (1분 27.5초)
- **저장 경로**: `/Users/markmini/Documents/dev/2026-cop-physical-ai/data/episodes/`
- **수집된 에피소드 수**: 50개 (index 0~49)
- **총 프레임 수**: 3,100개 (에피소드당 62 프레임)
- **에피소드당 물리 시간**: 약 2.07초 (30 FPS × 62 프레임)
- **성공률**: 100% (스크립트에 별도 grasp 성공 판정 로직 없음, 모든 에피소드 오류 없이 완료)

### `info.json` 검증 (LeRobot v3.0)
```
codebase_version:  v3.0
robot_type:        so101
total_episodes:    50
total_frames:      3100
fps:               30
splits:            {"train": "0:50"}
features:
  - observation.images.top  (video, 480×640×3, H.264)
  - observation.state       (float32, 6DoF)
  - action                  (float32, 6DoF)
  - timestamp, frame_index, episode_index, index, task_index
```

### `data/chunk-000/` 구조
```
data/episodes/
├── data/
│   └── chunk-000/
│       └── file-000.parquet        (262 KB — 3,100 프레임)
├── meta/
│   ├── info.json
│   ├── stats.json
│   ├── tasks.parquet
│   └── episodes/chunk-000/
│       └── file-000.parquet        (165 KB — 50 에피소드 메타)
└── videos/
    └── observation.images.top/chunk-000/
        └── file-000.mp4            (6.4 MB — H.264 전체 영상)
```

## 관찰 / 이슈
- 실제 grasp 성공 여부를 측정하려면 큐브 최종 위치(z좌표 상승 여부 등)를 시뮬레이션 후 확인하는 로직을 추가해야 합니다.

## 다음 단계
- Phase 0 완료 리포트 + 6월 Phase 1 준비
