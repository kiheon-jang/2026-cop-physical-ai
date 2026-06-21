# train_act.py::train() 학습 루프 구현 — 2026-06-10

## 단계
Phase 1 - W3 사전 준비 (정규 W3: 6/15~6/21).
어제(6/9) build_model() 구현 직후 명시한 다음 단계 — "2026-06-10~14: train_act.py::train() 루프 구현"
의 본 실행. W3 D1(6/15) `--smoke` 검증을 통과시킬 사전 준비.

## 변경 사항 (`scripts/train_act.py`)

### 1. `train()` 본구현 (placeholder → implemented)
- 시그니처 확장: `train(config, model, dataloader, max_epochs=None, max_steps_per_epoch=None)`
  - `max_epochs` / `max_steps_per_epoch` 는 smoke 테스트(6/15 D1) 용 축소 파라미터.
- LeRobot ACTPolicy API 매핑:
  - `policy.get_optim_params()` → AdamW 에 그대로 전달. ACTConfig 의 `optimizer_lr` /
    `optimizer_lr_backbone` 기반으로 ACTPolicy 가 내부적으로 backbone vs 나머지 두 그룹을
    생성하므로, 학습 코드에서 수동 그룹핑(`model.backbone.parameters()` 등) 금지.
  - `loss, loss_dict = model.forward(batch)` (LeRobot 0.x ACTPolicy 시그니처).
    `loss_dict` 키: `l1_loss`, `kld_loss` (CVAE KL). 누적 후 에폭 평균 메트릭으로 기록.
- grad clip: `torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)`.
- batch device 이동: `v.to(device, non_blocking=True)` (hasattr 가드).
- 단계별 로그: `config.log_every_n_steps` (기본 10) 마다 JSON 한 줄 stdout (flush).
- 에폭 종료 시 `epoch_done` JSON 한 줄 + history append.
- 체크포인트: `(epoch+1) % save_every_n_epochs == 0` 또는 마지막 에폭에서 저장.

### 2. `_save_checkpoint()` 신규
- `checkpoints/act/epoch_NNNN/` 디렉터리 생성.
- `model.save_pretrained(ckpt_root)` (ACTPolicy = HF PreTrainedPolicy 상속) 으로 정책 dir 저장
  → 추후 `ACTPolicy.from_pretrained(ckpt_root)` 로 resume 가능 (이미 build_model `resume_from`
  지원).
- `trainer_state.pt` 별도 저장: `optimizer.state_dict()` + epoch + history.

### 3. `main()` CLI 정비
- `argparse` 도입: `--smoke`, `--epochs N`, `--resume-from PATH`, `--dry-run`.
- 기본 호출(인자 없음) = 설정 검증만 (기존 동작 보존, 크론에서 안전).
- `--smoke` = 1 epoch / 2 step. W3 D1(6/15) 의 sanity check 용.
  - PHASE_ROADMAP W3 노트의 "`--smoke` 1 epoch 검증 → 통과 시 nohup epoch 100" 절차 그대로 적용.
- `--epochs N` = 본 학습. nohup 백그라운드 실행 시 사용:
  ```
  nohup .venv/bin/python3 scripts/train_act.py --epochs 100 > logs/act_train.log 2>&1 &
  ```
- result JSON `pipeline_status.train` → `"implemented"`.
- venv 경로 표기 수정: 구 `~/Documents/dev/...` → 신 `/Volumes/MARK_DATA/dev/...` (실제 위치).

## 검증
- 정적 검토만 수행. 본 세션 sandbox 가 `.venv/bin/python3` 및 `python3 -m py_compile` 호출을
  여전히 차단 (6/7~6/9 동일). 런타임 검증은 6/15 W3 D1 `--smoke` 단계에서 일괄 수행 예정.
- 정적 점검 사항:
  - ACTConfig 매핑은 6/9 build_model 구현과 일치 (변경 없음).
  - LeRobot 0.x `ACTPolicy.forward` → `(loss, loss_dict)` 시그니처 사용. `loss_dict` 키는
    `modeling_act.py` 의 `loss_dict["l1_loss"]`, `loss_dict["kld_loss"]` 와 일치.
  - `get_optim_params()` 는 `PreTrainedPolicy` 가 강제하는 추상 메서드로 ACTPolicy 구현 완비.
  - `save_pretrained` 는 HF 기반 `PreTrainedPolicy` 표준 메서드.

## 다음 단계 (2026-06-11~14)
- 11~12일: smoke 경로(`--smoke`) 의 환경 변수 — log dir 자동 생성, MPS device 폴백 분기
  세부 검증. 가능하면 sandbox 해제 후 `--smoke` 실런 1회.
- 13~14일: nohup 백그라운드 실행 wrapper (`scripts/start_act_train.sh`) 신규 — pid 파일,
  로그 로테이션, 재시작 시 최신 checkpoint 자동 resume.
- 15일 (Phase 1 W3 D1): `--smoke` 통과 시 `--epochs 100` nohup 백그라운드 실행 착수,
  `logs/act_train.pid` 기록 → PHASE_ROADMAP W3 첫 항목 `[v]` 체크.

## 연결 — PHASE_ROADMAP
- Phase 1 W3 의 첫 두 항목 — "LeRobot ACT 학습 파이프라인 구성 (`scripts/train_act.py`)" 과
  "nohup 백그라운드로 epoch 100 학습 실행" — 의 사전 준비. 본 작업으로 첫 항목의 코드
  골격이 완성 (load_dataset / build_model / train 모두 `implemented`). 정식 W3 진입(6/15)
  까지 `[ ]` 유지.
