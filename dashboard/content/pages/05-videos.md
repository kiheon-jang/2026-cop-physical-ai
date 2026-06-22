---
id: videos
title: "시각자료 · 진척 현황"
order: 5
menu_route: videos
screenshot: videos.png
category: 핵심
---
## 기능명세

시각자료 화면(`view-videos`)은 학습 진척 증거, 시뮬 동작 영상, 카메라 시점 프레임, 하드웨어 사진, 학습 데이터셋 영상을 통합해 보여주는 화면이다. 진척 관점으로 구성되어 있으며, 영상/이미지는 모두 `build.py`가 레포지토리 파일을 스캔해 `data.json`에 경로를 포함시킨다.

**컨텍스트 설명 박스 (video-explainer)**
- `video-explainer-now`: 현재 학습 단계 상태를 동적으로 표시 (예: "ACT 학습 시작 대기 중" 또는 학습 진행 중 상태).
- `video-explainer-caveat`: "이 영상들은 학습 전 단계 시뮬 결과(IK 기반)이며 ACT 학습 결과 영상이 아님"이라는 주의 문구 동적 표시.

**학습 진척 섹션 (training-progress-wrap)**
학습이 시작된 경우에만 표시되는 섹션. 두 부분:
1. **ACT 학습 메트릭 차트**: `build_training_metrics()`가 `outputs/train/*/metrics.jsonl` 또는 `logs/act_train_metrics.jsonl`에서 읽은 epoch별 loss/lr/success_rate 데이터를 SVG 선 차트로 렌더링. 현재 epoch, 현재 loss, best loss, 학습 상태(running/paused/pending) 표시.
2. **inference 진척 영상 carousel**: `build_inference_progress()`가 `research/simulation/inference_progress/*.mp4`를 스캔. 파일명 패턴 `inference_epoch_{NN}_{date}.mp4` 기준 epoch별 정렬. 학습 없으면 이 섹션 미표시.

**시뮬 동작 영상 섹션 (video-grid)**
`build_videos()`가 `research/simulation/video/*.mp4`를 스캔한 영상 카드 목록. 수정 시각 역순 정렬. 각 카드:
- 파일명 기반 비전공자용 설명(`_VIDEO_DESCRIPTIONS` 키워드 매칭):
  - pick_place → "픽앤플레이스 시나리오 시뮬 — 데이터 수집용 (학습 전, IK 기반. 큐브 실패가 정상)"
  - 6dof → "6축 로봇팔 기본 움직임 — 시뮬 환경 동작 검증"
  - 기타 → "시뮬레이션 결과 영상"
- kind 태그: pick-place / 6dof / sim
- preload: "metadata" (클릭 전 메타데이터만 로드)
- poster: `overhead_frame_0000.png` (있을 경우)
- 파일 크기(size_bytes), 수정 일시(modified) 표시

**학습 입력 카메라 시점 (frame-strips-wrap)**
`build_videos()`가 `research/simulation/video/overhead_frame_*.png` (최대 30장)와 `gripper_frame_*.png` (최대 30장)를 스캔. 각 카메라 시퀀스를 strip 형태로 렌더링:
- 천장 카메라(overhead): 480×640 RGB, ACT 학습 주 입력
- 그리퍼 손목 카메라(gripper): 두 번째 입력 시점

**하드웨어 시각자료 섹션 (hardware-grid-wrap)**
`build_hardware_photos()`가 `models/SO-ARM100/media/`에서 4장을 큐레이션:
- Leader_And_Follower_SO100.jpg: Leader + Follower 로봇팔 (텔레오퍼레이션 페어)
- SO101_Leader.webp: SO-ARM101 Leader
- SO101_Follower.webp: SO-ARM101 Follower
- d405_mount_sample_observation.jpg: RealSense D405 카메라 마운트 (그리퍼 시점 학습 입력)

**학습 데이터셋 영상 (dataset-hero-wrap)**
`build_videos()`가 `data/episodes/videos/observation.images.top/chunk-000/file-000.mp4`를 확인. 존재하면 "학습 데이터셋 영상" 섹션 맨 아래에 노출. `data/episodes/meta/info.json`에서 total_episodes/total_frames를 읽어 표시(기본값: 200ep / 12,400 프레임). preload="none"(27MB 이상으로 클릭 시 로드).

**데이터 출처**: `build_videos()`, `build_hardware_photos()`, `build_training_metrics()`, `build_inference_progress()`. 파일이 없는 섹션은 렌더링되지 않는다.

**상호작용**
- 영상 카드: HTML5 video 컨트롤러로 직접 재생.
- 프레임 시퀀스: 이미지 carousel (좌우 클릭).

## 사용가이드

시각자료 화면은 로봇 시뮬레이션이 어떻게 진행되고 있는지를 영상과 사진으로 확인하는 화면입니다.

**화면 구성 순서**
1. **컨텍스트 설명 박스** — 이 화면이 보여주는 것이 "현재 어떤 단계의 결과물"인지 설명합니다. 먼저 읽으세요.
2. **학습 진척 섹션** (학습 시작 후) — AI 모델 학습이 진행 중이라면 학습 곡선 차트와 진척 영상이 맨 위에 나타납니다.
3. **시뮬 동작 영상** — 시뮬에서 로봇팔이 실제로 움직이는 영상입니다. 재생 버튼을 눌러 확인할 수 있습니다.
4. **카메라 시점 이미지** — 로봇팔 위에서 내려다본 카메라(천장 카메라)와 손목 카메라 영상입니다. AI가 학습에 사용하는 바로 그 시점입니다.
5. **하드웨어 사진** — 실제 SO-ARM101 로봇팔 사진입니다. Leader(조작 측)와 Follower(작업 측) 두 대가 있습니다.
6. **학습 데이터셋 영상** — 맨 아래에 있으며, 200 에피소드 학습 데이터가 생성되었을 때만 표시됩니다.

**주의 사항**
시뮬 동작 영상은 AI가 학습한 결과 영상이 아닙니다. 학습 데이터를 만들기 위해 규칙 기반(IK)으로 로봇을 자동으로 움직인 영상입니다. 큐브를 잡는 데 실패하는 장면이 포함되어 있어도 정상입니다. 학습 결과 영상은 학습이 완료된 후 "학습 진척" 섹션에 따로 표시됩니다.
