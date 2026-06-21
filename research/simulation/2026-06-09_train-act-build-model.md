# train_act.py::build_model() 구현 — 2026-06-09

## 단계
Phase 1 - W3 사전 준비 (정규 W3 윈도우 6/15~6/21).
어제(6/8) "다음 단계"에 명시된 `build_model()` 실제 구현 항목.

## 무엇을 했나
`scripts/train_act.py` 의 두 가지 결함을 수정 + `build_model()` 플레이스홀더 → 실제 구현.

### 1. lerobot import 경로 수정
설치된 lerobot (`.venv/lib/python3.14/site-packages/lerobot/`) 의 실제 패키지 레이아웃은
`lerobot.policies.act` / `lerobot.datasets.lerobot_dataset` 이다. 스크립트는 구버전 경로
(`lerobot.common.policies.act`, `lerobot.common.datasets.lerobot_dataset`) 로 import 하고
있어서 `ImportError` 가 무음으로 발생, `LEROBOT_AVAILABLE = False` 가 되며 데이터/모델
로딩이 전부 `None` 으로 빠지는 잠재 결함이 있었음. 이를 수정하고 `FeatureType`,
`PolicyFeature` 도 함께 import.

### 2. ACTConfig 필드명 매핑
현재 설치된 ACTConfig 의 필드명은 `dim_model`, `n_heads`, `n_encoder_layers`,
`n_decoder_layers`, `optimizer_lr`, `optimizer_lr_backbone`, `optimizer_weight_decay`.
스크립트의 placeholder 주석(`hidden_dim`, `num_heads`, `encoder_layers` 등)과 다름.
실제 ACTConfig 시그니처 기준으로 매핑함.

### 3. input/output features 는 PolicyFeature dict
구버전 lerobot 의 `input_shapes`/`output_shapes` 는 더 이상 존재하지 않음.
대신 `input_features: dict[str, PolicyFeature]`, `output_features: dict[str, PolicyFeature]`
로 전달해야 함. `observation.images.<cam>` (VISUAL, shape=(3,H,W)),
`observation.state` (STATE, shape=(6,)), `action` (ACTION, shape=(6,)) 로 구성.

### 4. resume_from 지원
`build_model(config, resume_from=None)` 추가. resume_from 이 지정되면
`ACTPolicy.from_pretrained(resume_from, config=act_config)` 로 로드, 아니면 from-scratch
인스턴스화. 디렉터리 또는 HF repo id 모두 허용 (lerobot from_pretrained 규약 그대로).

### 5. device 자동 선택 + 이동
`cuda > mps > cpu` 우선순위로 device 선택 (Mac Mini M5 는 mps 사용 예상).
`act_config.device` 에도 같은 값을 주입하여 lerobot 내부 정규화 모듈이 동일 device 로
배치되도록 함. 마지막에 `model.to(torch.device(device))` 호출.

### 6. pipeline_status 갱신
`main()` 의 출력 JSON 의 `pipeline_status.build_model` 을 `placeholder` → `implemented`.

## 검증
- 정적 검토: lerobot 설치본 (`configuration_act.py`, `policies.py`, `types.py`) 의 필드명/
  시그니처와 1:1 대조. ACTConfig.__post_init__ 의 검증 규칙
  (`vision_backbone.startswith("resnet")`, `n_action_steps <= chunk_size`, `n_obs_steps == 1`)
  통과 가능한 값으로 구성 완료.
- 런타임 검증: `.venv/bin/python3 scripts/train_act.py` 실행은 본 세션 sandbox 권한으로
  차단됨 (`.venv/bin/python3` 심볼릭 링크 대상이 working dir 밖 — 2026-06-07/08 과 동일).
  → 6/15 W3 진입 시 첫 단계로 `--smoke` 실행 + load_dataset/build_model 단독 호출 검증
  예정.

## 다음 단계 연결
- 6/10~14: `train()` 루프 구현 (optimizer는 `policy.get_optim_params()` 활용 → backbone vs
  나머지 분리 lr 자동 적용, AdamW + grad clip + 에폭 메트릭 + 체크포인트 저장).
- 6/15 (Phase 1 W3 D1): 전체 파이프라인 smoke test → 통과 시 nohup epoch 100 백그라운드
  실행 착수, pid 파일 기록.
