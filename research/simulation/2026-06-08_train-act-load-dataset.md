# Phase 1 W3 사전 작업 — `train_act.py` `load_dataset()` 구현

**날짜**: 2026-06-08 (월요일)
**대상 파일**: `scripts/train_act.py`
**연관 단계**: Phase 1 - W3 (6/15~6/21) ACT 학습 사전 준비

## 무엇을 했나

`scripts/train_act.py` 의 3개 플레이스홀더 함수(`load_dataset`/`build_model`/`train`)
중 첫 번째인 `load_dataset()` 을 실제 구현으로 교체했다.

### 핵심 결정
- **delta_timestamps**:
  - 관측(`observation.state`, `observation.images.<cam>`): `-t/fps`, `t∈[0, n_obs_steps)` — 과거 프레임 (LeRobot 규약: 음수 = 과거)
  - 액션(`action`): `+t/fps`, `t∈[0, chunk_size)` — 미래 프레임
- **camera_keys 매핑**: config 의 `camera_keys=["top"]` → 데이터셋 키 `observation.images.top` (info.json features 와 일치)
- **DataLoader**: `batch_size=8, shuffle=True, num_workers=4, pin_memory=True, drop_last=True`
- train/val 분할은 도입하지 않음 — 데이터 200 ep 기준 split 없는 LeRobot v3.0 info.json (`splits: {"train": "0:200"}`) 과 일치. val 도입은 6/15 W3 본격 작업으로 미룸.

## 어떻게 검증했나

- 정적 검토 (Read tool diff). `LeRobotDataset` import path 와 `delta_timestamps` 형식은 LeRobot 공식 API 그대로.
- `info.json` feature 키 (`observation.images.top`, `observation.state`, `action`, fps=30) 와 일치 확인.
- [자가치유] `.venv/bin/python3 scripts/train_act.py` 런타임 실행이 본 세션 sandbox 권한으로 차단됨 (어제 6/07 로그와 동일 패턴). 실행 검증은 6/15 W3 진입 시점에 build_model + train 구현과 함께 일괄 수행.

## 다음 단계로의 연결

- 6/15 W3 진입 시 `build_model()` 구현 → ACTConfig 파라미터 매핑 (lerobot 버전에 따라 `input_shapes`/`output_shapes` 키 형식 확인 필요).
- 그 다음 `train()` 루프 구현 → AdamW + cosine schedule + checkpoint 저장.
- W3 첫날(6/15) 에는 `nohup .venv/bin/python3 scripts/train_act.py --epochs 100 &` 백그라운드 실행 + `logs/act_train.pid` 기록 패턴 적용 (PHASE_ROADMAP W3 가이드 참조).

## 미수정 (의도적)

- `scripts/train_act.py` 상단의 stale path (`/Users/markmini/Documents/...`): 심볼릭 링크로 동작하며 본 작업 범위 외이므로 미수정 (어제 6/07 로그에서도 동일 결정).
- `sim_pick_place.py` 런타임 재검증: 동일 sandbox 차단으로 보류. 사용자 수동 또는 권한 확장 후 재시도.
