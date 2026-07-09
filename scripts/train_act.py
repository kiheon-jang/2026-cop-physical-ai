#!/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python
"""
ACT (Action Chunking with Transformers) 학습 파이프라인

실행:
    /Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv/bin/python scripts/train_act.py
    또는 (venv 활성화 후):
    python scripts/train_act.py

구조:
    1. 설정   — ACTTrainingConfig
    2. 데이터  — load_dataset() [플레이스홀더]
    3. 모델   — build_model()   [플레이스홀더]
    4. 학습   — train()         [플레이스홀더]
    5. 진입점 — main() → JSON 출력
"""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

# ─────────────────────────────────────────
# 의존성 처리
# ─────────────────────────────────────────
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.policies.act.configuration_act import ACTConfig
    from lerobot.policies.act.modeling_act import ACTPolicy
    from lerobot.configs.types import FeatureType, PolicyFeature
    LEROBOT_AVAILABLE = True
except ImportError:
    LEROBOT_AVAILABLE = False


# ─────────────────────────────────────────
# 1. 학습 설정
# ─────────────────────────────────────────
@dataclass
class ACTTrainingConfig:
    """ACT 학습 하이퍼파라미터. SO-ARM101 (6 DOF) 기준 기본값."""

    # 데이터셋
    dataset_repo_id: str = "local/cop-pickplace"
    # COP_DATASET_ROOT 로 데이터 경로 오버라이드 (파이프라인 드라이버가 closed-loop data/episodes_cl 지정).
    dataset_root: str = os.environ.get(
        "COP_DATASET_ROOT",
        "/Volumes/MARK_DATA/dev/2026-cop-physical-ai/data/episodes",
    )
    camera_keys: List[str] = field(default_factory=lambda: ["top"])
    fps: int = 30
    # 영상 디코딩 백엔드. 기본 torchcodec 은 시스템 ffmpeg(libtorchcodec) 에 의존 —
    # Homebrew ffmpeg/libvpx 링크가 깨지면 dlopen 실패로 첫 배치에서 학습이 중단된다.
    # pyav 는 자체 ffmpeg 를 번들로 가져 시스템 의존이 없으므로 안정적.
    video_backend: str = "pyav"

    # 모델 구조 (ACT)
    n_obs_steps: int = 1           # 관측 시퀀스 길이
    chunk_size: int = 100          # 예측 액션 청크 크기 (ACT 핵심 파라미터)
    action_dim: int = 6            # SO-ARM101 관절 수 (DOF)
    state_dim: int = 6             # 관절 상태 차원
    hidden_dim: int = 512          # Transformer 히든 차원
    num_heads: int = 8             # 멀티헤드 어텐션 헤드 수
    num_encoder_layers: int = 4    # 인코더 레이어 수
    num_decoder_layers: int = 7    # 디코더 레이어 수
    dim_feedforward: int = 3200    # FFN 내부 차원
    kl_weight: float = 10.0        # CVAE KL 발산 가중치

    # 비전 인코더
    vision_backbone: str = "resnet18"  # resnet18 | resnet34 | resnet50
    image_size: List[int] = field(default_factory=lambda: [480, 640])

    # 학습
    batch_size: int = 8
    num_workers: int = 4           # DataLoader worker. smoke 시 0 강제 (macOS spawn 회피)
    lr: float = 1e-5
    lr_backbone: float = 1e-5
    weight_decay: float = 1e-4
    num_epochs: int = 200
    grad_clip_norm: float = 10.0
    seed: int = 42

    # 출력
    # COP_CKPT_DIR 로 체크포인트 디렉터리 오버라이드 (드라이버가 데이터셋별 격리 경로 지정 —
    # 재학습이 기존 baseline 체크포인트를 in-place 로 덮어쓰지 않게).
    checkpoint_dir: str = os.environ.get(
        "COP_CKPT_DIR",
        "/Volumes/MARK_DATA/dev/2026-cop-physical-ai/checkpoints/act",
    )
    log_dir: str = "/Volumes/MARK_DATA/dev/2026-cop-physical-ai/logs"
    log_every_n_steps: int = 10
    save_every_n_epochs: int = 10

    def validate(self) -> List[str]:
        errors = []
        if self.chunk_size < 1:
            errors.append("chunk_size는 1 이상이어야 합니다.")
        if self.kl_weight < 0:
            errors.append("kl_weight는 0 이상이어야 합니다.")
        if self.batch_size < 1:
            errors.append("batch_size는 1 이상이어야 합니다.")
        if self.num_heads > 0 and self.hidden_dim % self.num_heads != 0:
            errors.append(
                f"hidden_dim({self.hidden_dim})은 num_heads({self.num_heads})의 배수여야 합니다."
            )
        return errors


# ─────────────────────────────────────────
# 2. 데이터셋 로딩 [플레이스홀더]
# ─────────────────────────────────────────
def resolve_device(prefer: Optional[str] = None) -> str:
    """학습 device 선택. prefer 우선, 없으면 cuda → mps → cpu.

    MPS 선택 시 PYTORCH_ENABLE_MPS_FALLBACK=1 설정 — ACT 의 일부 op (예: 일부 conv 백워드)
    가 MPS 미구현일 때 CPU 폴백으로 학습이 중단되지 않도록 함. 이미 설정되어 있으면 유지.
    """
    if not TORCH_AVAILABLE:
        return "cpu"
    if prefer in ("cpu", "cuda", "mps"):
        device = prefer
    elif torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    if device == "mps":
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    return device


def load_dataset(
    config: ACTTrainingConfig,
    num_workers: Optional[int] = None,
) -> Optional[object]:
    """LeRobot 데이터셋을 로드하여 DataLoader 반환.

    delta_timestamps 규약 (LeRobot):
        - observation.* : 과거 n_obs_steps 프레임 (0 포함, 음수 = 과거)
        - action        : 미래 chunk_size 프레임 (0 포함, 양수 = 미래)

    Args:
        num_workers: DataLoader worker 수. None=config 기본(4). smoke 테스트에서는 0 권장 —
            macOS spawn fork 시 멀티프로세싱 데드락/segfault 회피.
    """
    if not LEROBOT_AVAILABLE or not TORCH_AVAILABLE:
        return None

    image_keys = [f"observation.images.{k}" for k in config.camera_keys]

    # ACT 는 현재 단일 관측만 사용한다. delta_timestamps 에 길이 1 리스트(예: [0.0])를 주면
    # 관측 텐서에 크기 1 시간축이 생겨 (B, 1, *) 가 되고, ACT VAE 인코더의
    # robot_state_embed.unsqueeze(1) 과 충돌(4D vs 3D)한다. 따라서 action 청크만 delta 로 주고,
    # 관측은 n_obs_steps>1 일 때만 과거 프레임을 적층한다(현 config: n_obs_steps=1 → 단일 프레임).
    delta_timestamps = {
        "action": [t / config.fps for t in range(config.chunk_size)],
    }
    if config.n_obs_steps > 1:
        obs_delta = [-t / config.fps for t in reversed(range(config.n_obs_steps))]
        delta_timestamps["observation.state"] = obs_delta
        for k in image_keys:
            delta_timestamps[k] = obs_delta

    dataset = LeRobotDataset(
        repo_id=config.dataset_repo_id,
        root=Path(config.dataset_root),
        delta_timestamps=delta_timestamps,
        video_backend=config.video_backend,
    )

    # pin_memory 는 CUDA 에서만 의미가 있음. MPS/CPU 에서는 워크로드 무익 + 워닝 발생.
    use_pin = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    workers = config.num_workers if num_workers is None else num_workers
    # persistent_workers: 워커를 매 epoch 재생성하지 않고 1회 spawn 후 재사용.
    # macOS(spawn)에서 epoch 마다 워커 pipe FD 가 누적돼 ~50 epoch 후
    # OSError [Errno 24] Too many open files 로 학습이 이상종료하던 문제 해결(2026-07-09).
    # num_workers=0(smoke) 에서는 persistent_workers 를 반드시 False 로 둬야 함.
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=workers,
        pin_memory=use_pin,
        drop_last=True,
        persistent_workers=workers > 0,
    )


# ─────────────────────────────────────────
# 3. 모델 정의 [플레이스홀더]
# ─────────────────────────────────────────
def build_model(
    config: ACTTrainingConfig,
    resume_from: Optional[str] = None,
    device: Optional[str] = None,
) -> Optional[object]:
    """ACT 정책 모델 생성.

    설치된 lerobot 버전의 ACTConfig 필드명에 맞춰 매핑:
        hidden_dim → dim_model, num_heads → n_heads,
        num_encoder_layers → n_encoder_layers, num_decoder_layers → n_decoder_layers.
    input/output 은 PolicyFeature dict (input_features/output_features) 로 전달.

    Args:
        resume_from: 체크포인트 디렉터리(또는 HF repo id) 경로. 지정 시 from_pretrained 로 로드.
    """
    if not LEROBOT_AVAILABLE or not TORCH_AVAILABLE:
        return None

    image_features = {
        f"observation.images.{k}": PolicyFeature(
            type=FeatureType.VISUAL, shape=(3, *config.image_size)
        )
        for k in config.camera_keys
    }
    input_features = {
        **image_features,
        "observation.state": PolicyFeature(
            type=FeatureType.STATE, shape=(config.state_dim,)
        ),
    }
    output_features = {
        "action": PolicyFeature(type=FeatureType.ACTION, shape=(config.action_dim,)),
    }

    device = resolve_device(device)

    act_config = ACTConfig(
        n_obs_steps=config.n_obs_steps,
        chunk_size=config.chunk_size,
        n_action_steps=config.chunk_size,
        input_features=input_features,
        output_features=output_features,
        vision_backbone=config.vision_backbone,
        dim_model=config.hidden_dim,
        n_heads=config.num_heads,
        n_encoder_layers=config.num_encoder_layers,
        n_decoder_layers=config.num_decoder_layers,
        dim_feedforward=config.dim_feedforward,
        kl_weight=config.kl_weight,
        optimizer_lr=config.lr,
        optimizer_lr_backbone=config.lr_backbone,
        optimizer_weight_decay=config.weight_decay,
        device=device,
        push_to_hub=False,
    )

    if resume_from:
        model = ACTPolicy.from_pretrained(resume_from, config=act_config)
    else:
        model = ACTPolicy(act_config)

    model = model.to(torch.device(device))
    return model


# ─────────────────────────────────────────
# 4. 학습 루프 [플레이스홀더]
# ─────────────────────────────────────────
def _device_of(model: object) -> "torch.device":
    return next(model.parameters()).device


def _save_checkpoint(
    model: object,
    optimizer: object,
    epoch: int,
    config: ACTTrainingConfig,
    history: List[dict],
) -> Path:
    """체크포인트 저장. ACTPolicy.save_pretrained 로 정책 디렉터리 + optimizer/history 별도 저장."""
    ckpt_root = Path(config.checkpoint_dir) / f"epoch_{epoch:04d}"
    ckpt_root.mkdir(parents=True, exist_ok=True)
    # ACTPolicy는 HF PreTrainedPolicy → save_pretrained 보유
    model.save_pretrained(str(ckpt_root))
    torch.save(
        {"optimizer": optimizer.state_dict(), "epoch": epoch, "history": history},
        ckpt_root / "trainer_state.pt",
    )
    return ckpt_root


def train(
    config: ACTTrainingConfig,
    model: object,
    dataloader: object,
    max_epochs: Optional[int] = None,
    max_steps_per_epoch: Optional[int] = None,
) -> List[dict]:
    """ACT 학습 루프.

    LeRobot ACTPolicy.forward(batch) → (loss, loss_dict) 시그니처.
    backbone vs 나머지 lr 분리는 ACTConfig 의 optimizer_lr/optimizer_lr_backbone 기반으로
    `policy.get_optim_params()` 가 두 그룹을 생성한다. 직접 그룹을 만들지 않는다.

    Args:
        max_epochs: None 이면 config.num_epochs 사용. smoke 테스트 시 1 등으로 축소.
        max_steps_per_epoch: None 이면 전체 배치. smoke 테스트 시 소수로 축소.

    Returns:
        에포크별 메트릭 리스트 (JSON 직렬화 가능).
    """
    if not TORCH_AVAILABLE:
        raise NotImplementedError("train: torch가 필요합니다.")
    if model is None or dataloader is None:
        raise ValueError("train: model/dataloader 가 None 입니다 (load_dataset/build_model 확인).")

    device = _device_of(model)
    epochs = max_epochs if max_epochs is not None else config.num_epochs

    optimizer = torch.optim.AdamW(
        model.get_optim_params(),
        lr=config.lr,
        weight_decay=config.weight_decay,
    )

    history: List[dict] = []
    Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    Path(config.log_dir).mkdir(parents=True, exist_ok=True)
    metrics_log = Path(config.log_dir) / "act_train_metrics.jsonl"

    for epoch in range(epochs):
        model.train()
        sum_loss = 0.0
        sum_l1 = 0.0
        sum_kl = 0.0
        step_count = 0
        epoch_start = time.time()

        for step, batch in enumerate(dataloader):
            if max_steps_per_epoch is not None and step >= max_steps_per_epoch:
                break

            batch = {
                k: (v.to(device, non_blocking=True) if hasattr(v, "to") else v)
                for k, v in batch.items()
            }

            loss, loss_dict = model.forward(batch)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), config.grad_clip_norm
            )
            optimizer.step()

            sum_loss += float(loss.detach().item())
            sum_l1 += float(loss_dict.get("l1_loss", 0.0))
            sum_kl += float(loss_dict.get("kld_loss", 0.0))
            step_count += 1

            if step_count % config.log_every_n_steps == 0:
                print(
                    json.dumps(
                        {
                            "epoch": epoch,
                            "step": step_count,
                            "loss": sum_loss / step_count,
                            "l1": sum_l1 / step_count,
                            "kl": sum_kl / step_count,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

        if step_count == 0:
            raise RuntimeError("train: dataloader 가 비어있습니다.")

        epoch_metric = {
            "epoch": epoch,
            "steps": step_count,
            "loss": sum_loss / step_count,
            "l1_loss": sum_l1 / step_count,
            "kld_loss": sum_kl / step_count,
            "elapsed_sec": time.time() - epoch_start,
            "timestamp": time.time(),
            # 런 식별자 — 여러 데이터셋 학습이 한 jsonl 에 누적되므로 구분 필수
            "dataset": Path(config.dataset_root).name,
            "ckpt_dir": Path(config.checkpoint_dir).name,
        }
        history.append(epoch_metric)
        print(json.dumps({"epoch_done": epoch_metric}, ensure_ascii=False), flush=True)
        with metrics_log.open("a") as f:
            f.write(json.dumps(epoch_metric, ensure_ascii=False) + "\n")

        if (epoch + 1) % config.save_every_n_epochs == 0 or (epoch + 1) == epochs:
            ckpt_path = _save_checkpoint(model, optimizer, epoch, config, history)
            print(
                json.dumps({"checkpoint_saved": str(ckpt_path)}, ensure_ascii=False),
                flush=True,
            )

    return history


# ─────────────────────────────────────────
# 5. 진입점
# ─────────────────────────────────────────
def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ACT 학습 파이프라인")
    p.add_argument("--smoke", action="store_true",
                   help="1 epoch / 2 step smoke 테스트 (W3 D1 sanity check 용)")
    p.add_argument("--epochs", type=int, default=None,
                   help="config.num_epochs 오버라이드 (기본: config 값)")
    p.add_argument("--resume-from", type=str, default=None,
                   help="체크포인트 디렉터리 경로")
    p.add_argument("--device", choices=["cpu", "cuda", "mps"], default=None,
                   help="학습 device 강제 지정. 기본: cuda → mps → cpu 자동 선택.")
    p.add_argument("--dry-run", action="store_true",
                   help="설정 검증만 수행, 학습 미실행 (기본 동작)")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    config = ACTTrainingConfig()
    errors = config.validate()

    result = {
        "status": "ok" if not errors else "config_error",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "venv": "/Volumes/MARK_DATA/dev/2026-cop-physical-ai/.venv",
        "python": sys.executable,
        "env": {
            "torch_available": TORCH_AVAILABLE,
            "lerobot_available": LEROBOT_AVAILABLE,
            "cuda_available": torch.cuda.is_available() if TORCH_AVAILABLE else False,
        },
        "config": asdict(config),
        "config_errors": errors,
        "pipeline_status": {
            "load_dataset": "implemented",
            "build_model": "implemented",
            "train": "implemented",
        },
        "args": vars(args),
    }

    if errors:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # smoke / 본 학습 분기. --dry-run 또는 옵션 없음 = 설정 검증만.
    if args.smoke or args.epochs is not None:
        if not (LEROBOT_AVAILABLE and TORCH_AVAILABLE):
            result["status"] = "blocked"
            result["message"] = "lerobot/torch 미설치 — venv 확인 필요."
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

        max_epochs = 1 if args.smoke else args.epochs
        max_steps = 2 if args.smoke else None

        # smoke 시 device 강제 cpu (사용자 --device 지정 시 그대로 존중) + num_workers=0.
        # 사유: M5 MPS 환경에서 ACT의 일부 op 폴백 + 멀티프로세싱 fork 가 smoke 통과 자체를
        # 가리는 경우가 있어, 최소 가시성 확보가 우선.
        if args.smoke:
            effective_device = args.device or "cpu"
            effective_workers = 0
        else:
            effective_device = args.device
            effective_workers = None

        # 데이터셋 존재 검증 — 오타/미동기 경로면 LeRobot 이 빈 디렉터리를 만들고
        # HF Hub 다운로드를 시도해 혼란스러운 실패가 되므로 여기서 명확히 차단.
        _info = Path(config.dataset_root) / "meta" / "info.json"
        if not _info.exists():
            result["status"] = "error"
            result["message"] = f"dataset_root 에 meta/info.json 없음: {config.dataset_root}"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)

        # 런 시작 배너 — 9시간 무인 학습 동안 로그만으로 어떤 데이터/체크포인트인지 검증 가능해야 함
        print(json.dumps({
            "train_start": {
                "dataset_root": config.dataset_root,
                "checkpoint_dir": config.checkpoint_dir,
                "epochs": args.epochs if args.epochs is not None else config.num_epochs,
                "resume_from": args.resume_from,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        }, ensure_ascii=False), flush=True)
        if args.resume_from:
            print(json.dumps({
                "warning": "resume 는 가중치만 복원 — 옵티마이저/epoch 카운터는 리셋됨 (실험 비교 시 주의)"
            }, ensure_ascii=False), flush=True)

        t0 = time.time()
        dataloader = load_dataset(config, num_workers=effective_workers)
        model = build_model(config, resume_from=args.resume_from, device=effective_device)
        result["device"] = str(_device_of(model))
        history = train(
            config, model, dataloader,
            max_epochs=max_epochs,
            max_steps_per_epoch=max_steps,
        )
        result["history"] = history
        result["wall_clock_sec"] = time.time() - t0
        result["message"] = "smoke 완료" if args.smoke else f"학습 {max_epochs} epoch 완료"
    else:
        result["message"] = (
            "설정 검증 완료. 실제 학습은 --smoke 또는 --epochs N 으로 실행. "
            "예: .venv/bin/python3 scripts/train_act.py --smoke"
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
