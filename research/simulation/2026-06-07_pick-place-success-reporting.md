# Pick-Place 성공 여부 stdout 보고 추가

- 날짜: 2026-06-07 (일)
- 단계: Phase 1 - W1-2 마무리 (6/1~6/14 윈도우)
- 동기: 2026-06-06 research-log에서 식별된 다음 단계 — `sim_pick_place.py`가 성공/실패를 stdout으로 보고하지 않아 메트릭 수집이 어려운 문제 해결

## 변경 내용 (`samples/training/sim_pick_place.py`)

1. `json` import 추가.
2. 성공 기준 상수 도입 (PHASE_ROADMAP W4 5/22~24 기준).
   - `APPROACH_THRESHOLD_M = 0.005` — 그리퍼 ±5mm 접근
   - `LIFT_THRESHOLD_M = 0.050` — 큐브 Z+50mm 들어올리기
3. 시나리오 루프 내에서 다음 메트릭 추적:
   - `approach_ok` / `lift_ok` 불리언
   - `min_approach_dist` / `max_lift_height` 실측치
4. 시나리오 종료 시 한 줄 JSON 출력:
   ```json
   {"status": "success"|"fail",
    "approach_ok": bool,
    "lift_ok": bool,
    "min_approach_dist_m": float,
    "max_lift_height_m": float,
    "approach_threshold_m": 0.005,
    "lift_threshold_m": 0.050,
    "video_path": "..."}
   ```
5. 종료 코드 — 성공 시 `0`, 실패 시 `1` (`SystemExit`).

## 검증

- 정적 검토: 인접 코드 흐름과 변수 스코프 확인 완료. 기존 시뮬레이션 로직 (관절 제어, 큐브 위치 추적)에는 손대지 않음 — 메트릭 관측과 보고만 추가.
- 런타임 검증: 본 세션의 Bash 권한 제약으로 `.venv/bin/python3` 실행이 차단되어 보류. 다음 크론 (2026-06-08) 또는 사용자 수동 실행 시 JSON 출력 + exit code 확인 필요.

## 다음 단계 연결

- W3 (6/15~) ACT 학습이 사용할 데이터셋(이미 200 ep 수집됨)의 품질 메트릭으로 활용 가능.
- 향후 `sim_data_collector.py`에 동일 성공 기준을 적용해 에피소드별 성공 라벨을 부착하면 ACT 학습 시 필터링/가중치 부여에 사용 가능.
- W3 첫 항목 `scripts/train_act.py`는 이미 플레이스홀더로 작성되어 있음 (load_dataset / build_model / train TODO).
