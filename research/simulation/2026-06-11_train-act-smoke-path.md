# 2026-06-11 — scripts/train_act.py smoke 경로 점검 (W3 D1 사전 준비)

## 오늘 한 일
어제(6/10) 로그의 "다음 단계 (6/11~12)" 항목인 **smoke 경로 세부 점검 — log dir 자동
생성 + MPS device 폴백 분기** 를 적용. 6/15 (Phase 1 W3 D1) `--smoke` 1 epoch 실행 시
즉시 통과하도록 하는 사전 준비.

## 변경 사항 (`scripts/train_act.py`)

### 1. 경로 정정 (스테일 → 정식)
- shebang `#!/Users/markmini/Documents/dev/...` → `#!/Volumes/MARK_DATA/dev/...`
- docstring 실행 예시 동일하게 정정
- `ACTTrainingConfig.dataset_root`, `checkpoint_dir` 기본값 `/Volumes/MARK_DATA/...` 로 통일

이전까지 셰뱅과 기본 경로가 구 .venv 위치(`~/Documents/dev/...`)를 가리켜 있었음. 실제
.venv 는 `/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv` 한 곳뿐. 직접 실행
(`./scripts/train_act.py`) 또는 기본 경로 의존 시 ModuleNotFound 발생할 수 있었음.

### 2. `resolve_device(prefer)` 신규 헬퍼 + MPS 폴백 활성화
- cuda → mps → cpu 자동 선택 로직 일원화 (기존 build_model 인라인 식 → 추출).
- `prefer` 인자로 강제 지정 가능 (cpu/cuda/mps).
- MPS 선택 시 `os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")` —
  ACT 의 일부 백워드 op 가 MPS 미구현일 때 학습이 NotImplementedError 로 죽지 않고
  해당 op 만 CPU 폴백되도록. 이미 외부에서 설정된 경우는 덮어쓰지 않음 (setdefault).

### 3. `build_model(config, resume_from=None, device=None)` 시그니처 확장
- `device` kwarg 추가 → 내부에서 `resolve_device(device)` 위임.
- 호출부(`main()`): `model = build_model(config, resume_from=args.resume_from, device=args.device)`.
- 결과 JSON 에 `"device": str(_device_of(model))` 노출 — smoke 실행 시 어떤 device 로
  돌아갔는지 사후 확인 가능.

### 4. `--device {cpu,cuda,mps}` CLI 플래그 추가
- 기본 None (자동 선택). Mac Mini M5 에서 MPS 회피가 필요한 경우 `--device cpu`.
- W3 D1 시나리오: 우선 `--smoke` 로 자동 선택(=MPS) → 실패 시 `--smoke --device cpu`
  로 1차 폴백 → 그래도 실패 시 PYTORCH_ENABLE_MPS_FALLBACK 단독 확인.

### 5. 로그 디렉터리 자동 생성 + epoch 메트릭 JSONL 영속화
- `train()` 진입 시 `Path(config.log_dir).mkdir(parents=True, exist_ok=True)`
  (`log_dir` 신규 필드, 기본 `/Volumes/MARK_DATA/dev/.../logs`).
- 매 epoch 종료마다 `logs/act_train_metrics.jsonl` 에 한 줄 append
  (`{epoch, steps, loss, l1_loss, kld_loss, elapsed_sec, timestamp}`).
- 효과: nohup 로그 (`logs/act_train.log`, PHASE_ROADMAP W3 지정 경로) 와 별개로,
  매일 크론이 `tail -1 logs/act_train_metrics.jsonl` 로 진행률만 깔끔하게 파싱 가능.

### 6. DataLoader `pin_memory` 조건부
- pin_memory=True 는 CUDA 전용 의미. MPS/CPU 에서는 워닝 + 무익.
- `use_pin = torch.cuda.is_available()` 로 분기.

## 검증 방법
- 본 세션 sandbox 가 `.venv/bin/python3` 실행 여전히 차단 (6/7~6/10 동일, 8일 연속).
  `agent/external-dependencies.md` Claude Code v3.2 harness allowlist 블로커가 근본 원인.
- 따라서 정적 검토만 적용:
  - argparse `--device` choices = LeRobot/PyTorch device 문자열 명세 일치.
  - `resolve_device` 의 `setdefault` 는 멱등 — 본 세션 외부에서 `PYTORCH_ENABLE_MPS_FALLBACK=0`
    명시 시 그대로 유지.
  - JSONL append 는 epoch loop 외부에서 `metrics_log = Path(...)/"act_train_metrics.jsonl"`
    로 1회 결정 → race 없음 (single-process 학습).
- 런타임 검증은 6/15 W3 D1 `--smoke` 통과 시점에 일괄 수행.

## 다음 단계 연결
- 2026-06-12: `--smoke --device cpu` 강제 분기 추가 검증 항목 도출 (필요 시 dataloader
  num_workers 0 fallback — 일부 환경에서 multiprocessing fork 실패 회피).
- 2026-06-13~14: `scripts/start_act_train.sh` wrapper 작성 — nohup + pid 기록 +
  `PYTORCH_ENABLE_MPS_FALLBACK=1` 명시 설정 + 자동 resume (`checkpoints/act/epoch_*`
  최신 디렉터리 탐색).
- 2026-06-15 (W3 D1): `--smoke` 1 epoch 통과 → `--epochs 100` nohup 백그라운드 실행 →
  PHASE_ROADMAP W3 첫 두 항목 `[v]` 체크.
