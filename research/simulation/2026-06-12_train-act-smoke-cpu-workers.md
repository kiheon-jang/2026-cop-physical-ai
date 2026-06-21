# train_act smoke 경로 — CPU 강제 + num_workers=0 폴백

- 일자: 2026-06-12 (금)
- Phase: 1 - W3 사전 준비 D2 (정규 W3 윈도우: 6/15~6/21)
- 대상 파일: `scripts/train_act.py`

## 무엇을 했나

`scripts/train_act.py` 에 다음 3개 변경 적용 (6/11 next-step 항목 본 실행):

1. `ACTTrainingConfig.num_workers: int = 4` 신규 — DataLoader worker 수를 config 노출.
2. `load_dataset(config, num_workers=None)` 시그니처 확장 — None 이면 config 기본 사용,
   호출자가 정수 전달 시 그 값을 그대로 DataLoader 에 위임. 기존 하드코딩 `num_workers=4`
   제거.
3. `main()` `--smoke` 분기에서 `effective_device = args.device or "cpu"` 및
   `effective_workers = 0` 강제. 사용자가 `--device mps` 등 명시 지정 시 그대로 존중.

## 왜 (smoke 통과 가시성 최우선)

- Mac mini M5 MPS 환경에서 ACT 의 일부 op 가 MPS 미구현 → `PYTORCH_ENABLE_MPS_FALLBACK=1`
  으로 폴백되지만, smoke 1 epoch / 2 step 짜리 sanity check 가 폴백 워닝/지연으로
  통과 자체가 묻히는 사례 존재.
- macOS `fork`/`spawn` 멀티프로세싱이 LeRobot dataset worker 와 결합 시 데드락/segfault
  를 일으키는 보고가 LeRobot 이슈에 다수. smoke 단계에서는 0 워커가 항상 안전.
- 본 학습 (`--epochs 100`) 은 config 기본값 (num_workers=4, 자동 device) 그대로 사용 →
  성능 저하 없음.

## 어떻게 검증했나

- 정적: `Edit` tool 적용 성공. 파일 line count 증가 (452 → ~470).
- 런타임 (`.venv/bin/python3 scripts/train_act.py --smoke`): 본 세션 sandbox 차단 12일 연속
  (6/7~6/12). 실제 smoke 실행은 사용자 수동 또는 v3.2 harness allowlist 해제 후 6/15 D1 에 일괄.

## 다음 단계와의 연결

- 6/13~14: `scripts/start_act_train.sh` wrapper 신규 — nohup + pid 파일 + 
  `PYTORCH_ENABLE_MPS_FALLBACK=1` 명시 export + 자동 resume (latest checkpoint 탐색).
- 6/15 (Phase 1 W3 D1): `.venv/bin/python3 scripts/train_act.py --smoke` → 통과 시
  `--epochs 100` nohup 백그라운드 실행, `logs/act_train.pid` 기록. PHASE_ROADMAP W3 첫
  두 항목 (`scripts/train_act.py` 구성 + nohup 백그라운드 실행) `[v]` 체크.
