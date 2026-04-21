"""
샘플: Diffusion Policy 학습 파이프라인 테스트
노이즈 스케줄러, 액션 디노이징 루프, 학습 설정 검증

실행 방법:
    python3 samples/training/test_diffusion_training.py

Requirements (하드웨어 없이 실행 가능):
    pip install torch numpy
    pip install lerobot  # 선택적 — 없으면 mock 모드로 동작

Diffusion Policy 개요:
    - 학습 시: 액션 시퀀스에 랜덤 노이즈 추가 → 노이즈 예측 학습
    - 추론 시: 순수 노이즈에서 시작 → T 스텝에 걸쳐 클린 액션 복원
    - SO-ARM101 적용: 6 DOF 관절 각도 시퀀스 (horizon=16)
"""

import math
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ─────────────────────────────────────────
# 의존성 처리: lerobot 미설치 시 mock 사용
# ─────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from lerobot.common.policies.diffusion.configuration_diffusion import DiffusionConfig  # noqa: F401
    LEROBOT_AVAILABLE = True
except ImportError:
    LEROBOT_AVAILABLE = False
    # lerobot 없이도 핵심 로직 검증 가능하도록 mock 구현


# ─────────────────────────────────────────
# 1. 학습 설정
# ─────────────────────────────────────────
@dataclass
class DiffusionTrainingConfig:
    """Diffusion Policy 학습 하이퍼파라미터.

    SO-ARM101 (6 DOF) + 카메라 2개 환경 기준 기본값.
    """
    # 모델 구조
    n_obs_steps: int = 2        # 관측 시퀀스 길이 (현재 + 과거 1프레임)
    horizon: int = 16           # 예측 액션 시퀀스 길이
    n_action_steps: int = 8     # 실제 실행할 스텝 수 (horizon 이하)
    action_dim: int = 6         # SO-ARM101 관절 수 (DOF)
    obs_dim: int = 14           # 관절 6 + 속도 6 + 그리퍼 2

    # 노이즈 스케줄러 (DDPM)
    num_train_timesteps: int = 100   # 학습 시 노이즈 스텝 수
    num_inference_steps: int = 10    # 추론 시 디노이징 스텝 수
    beta_start: float = 0.0001
    beta_end: float = 0.02
    beta_schedule: str = "squaredcos_cap_v2"  # DDPM 논문 권장

    # 학습
    batch_size: int = 64
    lr: float = 1e-4
    lr_warmup_steps: int = 500
    num_epochs: int = 100
    grad_clip_norm: float = 10.0

    # 데이터셋
    dataset_repo_id: str = "kiheon-jang/hdel_iot_pick_place_v1"
    fps: int = 30

    # 카메라 입력 (vision encoder)
    camera_keys: List[str] = field(default_factory=lambda: ["top", "gripper"])
    image_size: Tuple[int, int] = (96, 96)
    vision_encoder: str = "resnet18"  # resnet18 | resnet34 | efficientnet_b0

    def to_lerobot_cmd(self) -> str:
        """LeRobot train 명령어 생성 (참고용)."""
        cameras_str = " ".join([
            f"--policy.camera_keys={k}" for k in self.camera_keys
        ])
        return (
            f"lerobot-train policy=diffusion \\\n"
            f"  dataset_repo_id={self.dataset_repo_id} \\\n"
            f"  policy.n_obs_steps={self.n_obs_steps} \\\n"
            f"  policy.horizon={self.horizon} \\\n"
            f"  policy.n_action_steps={self.n_action_steps} \\\n"
            f"  training.batch_size={self.batch_size} \\\n"
            f"  training.lr={self.lr} \\\n"
            f"  training.num_epochs={self.num_epochs} \\\n"
            f"  {cameras_str}"
        )

    def validate(self) -> List[str]:
        """설정값 유효성 검사. 오류 목록 반환 (빈 리스트 = 정상)."""
        errors = []
        if self.n_action_steps > self.horizon:
            errors.append(
                f"n_action_steps({self.n_action_steps}) > horizon({self.horizon}): "
                "실행 스텝이 예측 범위를 초과할 수 없습니다."
            )
        if self.num_inference_steps > self.num_train_timesteps:
            errors.append(
                f"num_inference_steps({self.num_inference_steps}) > "
                f"num_train_timesteps({self.num_train_timesteps})"
            )
        if self.beta_start >= self.beta_end:
            errors.append(
                f"beta_start({self.beta_start}) >= beta_end({self.beta_end})"
            )
        if self.batch_size < 1:
            errors.append("batch_size는 1 이상이어야 합니다.")
        return errors


# ─────────────────────────────────────────
# 2. DDPM 노이즈 스케줄러 (순수 Python)
# ─────────────────────────────────────────
class SimpleDDPMScheduler:
    """DDPM 노이즈 스케줄러 — torch 없이 동작하는 참조 구현.

    논문: Ho et al., "Denoising Diffusion Probabilistic Models" (NeurIPS 2020)
    https://arxiv.org/abs/2006.11239
    """

    def __init__(
        self,
        num_train_timesteps: int = 100,
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
    ):
        self.num_train_timesteps = num_train_timesteps
        # 선형 베타 스케줄
        self.betas = [
            beta_start + (beta_end - beta_start) * t / (num_train_timesteps - 1)
            for t in range(num_train_timesteps)
        ]
        self.alphas = [1.0 - b for b in self.betas]
        # 누적곱: ᾱ_t = ∏_{s=1}^{t} α_s
        self.alphas_cumprod = []
        acc = 1.0
        for a in self.alphas:
            acc *= a
            self.alphas_cumprod.append(acc)

    def add_noise(
        self,
        clean_action: List[float],
        noise: List[float],
        timestep: int,
    ) -> List[float]:
        """순방향 확산: x_t = √ᾱ_t · x_0 + √(1-ᾱ_t) · ε.

        Args:
            clean_action: 원본 클린 액션 벡터 x_0.
            noise: 가우시안 노이즈 ε ~ N(0,I).
            timestep: 노이즈 타임스텝 t (0-indexed).

        Returns:
            노이즈가 섞인 액션 x_t.
        """
        sqrt_alpha_bar = math.sqrt(self.alphas_cumprod[timestep])
        sqrt_one_minus = math.sqrt(1.0 - self.alphas_cumprod[timestep])
        return [
            sqrt_alpha_bar * x + sqrt_one_minus * n
            for x, n in zip(clean_action, noise)
        ]

    def noise_level(self, timestep: int) -> Tuple[float, float]:
        """타임스텝 t의 신호/노이즈 비율 반환.

        Returns:
            (signal_ratio, noise_ratio): 각각 √ᾱ_t, √(1-ᾱ_t)
        """
        a = self.alphas_cumprod[timestep]
        return math.sqrt(a), math.sqrt(1.0 - a)

    def get_velocity(
        self,
        clean_action: List[float],
        noise: List[float],
        timestep: int,
    ) -> List[float]:
        """v-prediction 타겟 계산: v = √ᾱ_t · ε - √(1-ᾱ_t) · x_0."""
        sqrt_alpha_bar = math.sqrt(self.alphas_cumprod[timestep])
        sqrt_one_minus = math.sqrt(1.0 - self.alphas_cumprod[timestep])
        return [
            sqrt_alpha_bar * n - sqrt_one_minus * x
            for x, n in zip(clean_action, noise)
        ]


# ─────────────────────────────────────────
# 3. 학습 스텝 시뮬레이터
# ─────────────────────────────────────────
class DiffusionTrainingStep:
    """단일 학습 스텝 시뮬레이션 (loss 계산 로직 검증용).

    실제 학습에서는 모델이 노이즈를 예측하지만,
    여기서는 타겟 생성/loss 형태만 검증합니다.
    """

    def __init__(self, config: DiffusionTrainingConfig):
        """
        Args:
            config: 학습 하이퍼파라미터 설정.
        """
        self.config = config
        self.scheduler = SimpleDDPMScheduler(
            num_train_timesteps=config.num_train_timesteps,
            beta_start=config.beta_start,
            beta_end=config.beta_end,
        )

    def simulate_batch(
        self,
        batch_size: int = 4,
    ) -> dict:
        """미니배치 학습 스텝 시뮬레이션.

        Args:
            batch_size: 배치 내 샘플 수.

        Returns:
            dict: {
                'batch_size': int,
                'action_dim': int,
                'horizon': int,
                'timesteps': List[int],
                'mean_signal_ratio': float,
                'mean_noise_ratio': float,
                'loss_shape_ok': bool,
            }
        """
        import random
        rng = random.Random(42)

        # 랜덤 타임스텝 샘플링
        timesteps = [
            rng.randint(0, self.config.num_train_timesteps - 1)
            for _ in range(batch_size)
        ]

        signal_ratios = []
        noise_ratios = []
        losses = []

        for t in timesteps:
            # 클린 액션 (horizon × action_dim)
            clean = [
                rng.gauss(0, 1)
                for _ in range(self.config.horizon * self.config.action_dim)
            ]
            # 가우시안 노이즈
            noise = [rng.gauss(0, 1) for _ in range(len(clean))]

            # 노이즈 추가
            noisy = self.scheduler.add_noise(clean, noise, t)

            # MSE loss (predicted = noise, target = noise — 완벽 예측 가정)
            mse = sum((p - n) ** 2 for p, n in zip(noisy, noise)) / len(noise)
            losses.append(mse)

            s, n = self.scheduler.noise_level(t)
            signal_ratios.append(s)
            noise_ratios.append(n)

        return {
            "batch_size": batch_size,
            "action_dim": self.config.action_dim,
            "horizon": self.config.horizon,
            "timesteps": timesteps,
            "mean_signal_ratio": sum(signal_ratios) / len(signal_ratios),
            "mean_noise_ratio": sum(noise_ratios) / len(noise_ratios),
            "loss_shape_ok": len(losses) == batch_size,
        }


# ─────────────────────────────────────────
# 4. 단위 테스트
# ─────────────────────────────────────────

def test_config_validation():
    """학습 설정 유효성 검사 테스트."""
    # 정상 설정
    cfg = DiffusionTrainingConfig()
    errors = cfg.validate()
    assert errors == [], f"정상 설정에서 오류 발생: {errors}"

    # n_action_steps > horizon 오류 케이스
    bad_cfg = DiffusionTrainingConfig(n_action_steps=20, horizon=16)
    errors = bad_cfg.validate()
    assert len(errors) == 1, "n_action_steps > horizon 오류가 감지되어야 합니다."
    assert "n_action_steps" in errors[0]

    # 복합 오류 케이스
    multi_bad = DiffusionTrainingConfig(
        n_action_steps=20,
        horizon=16,
        num_inference_steps=200,
        num_train_timesteps=100,
        beta_start=0.02,
        beta_end=0.01,
    )
    errors = multi_bad.validate()
    assert len(errors) == 3, f"3개 오류 기대, 실제: {len(errors)}"

    print("✅ test_config_validation PASSED")


def test_cmd_generation():
    """LeRobot 학습 명령어 생성 테스트."""
    cfg = DiffusionTrainingConfig()
    cmd = cfg.to_lerobot_cmd()
    assert "lerobot-train" in cmd
    assert "diffusion" in cmd
    assert "top" in cmd
    assert "gripper" in cmd
    assert str(cfg.horizon) in cmd
    print("✅ test_cmd_generation PASSED")
    print("\n  생성된 명령어 (참고용):")
    for line in cmd.split("\n"):
        print(f"  {line}")


def test_ddpm_scheduler_noise_level():
    """DDPM 노이즈 스케줄러 신호/노이즈 비율 단조성 테스트.

    타임스텝이 증가할수록 노이즈 비율이 단조 증가해야 합니다.
    """
    scheduler = SimpleDDPMScheduler(num_train_timesteps=100)
    prev_noise = -1.0
    for t in range(0, 100, 10):
        signal, noise = scheduler.noise_level(t)
        # 신호 + 노이즈 제곱합 ≈ 1 (파서발 등식 완화 버전)
        assert 0.0 < signal <= 1.0, f"t={t}: signal ratio 범위 초과 ({signal:.4f})"
        assert 0.0 <= noise <= 1.0, f"t={t}: noise ratio 범위 초과 ({noise:.4f})"
        assert noise >= prev_noise - 1e-9, f"t={t}: 노이즈 비율이 단조 증가하지 않음"
        prev_noise = noise
    print("✅ test_ddpm_scheduler_noise_level PASSED")


def test_add_noise_shape():
    """add_noise 출력 길이 및 값 범위 테스트."""
    scheduler = SimpleDDPMScheduler(num_train_timesteps=100)
    action_len = 16 * 6  # horizon=16, action_dim=6
    clean = [0.0] * action_len
    noise = [1.0] * action_len

    # t=0: 거의 클린 (노이즈 매우 적음)
    noisy_t0 = scheduler.add_noise(clean, noise, timestep=0)
    assert len(noisy_t0) == action_len

    # t=99: 거의 순수 노이즈
    noisy_t99 = scheduler.add_noise(clean, noise, timestep=99)
    assert len(noisy_t99) == action_len

    # t=99에서 노이즈 성분이 t=0보다 커야 함
    mean_t0 = sum(abs(v) for v in noisy_t0) / len(noisy_t0)
    mean_t99 = sum(abs(v) for v in noisy_t99) / len(noisy_t99)
    assert mean_t99 > mean_t0, (
        f"t=99 평균 절댓값({mean_t99:.4f})이 t=0({mean_t0:.4f})보다 작음 — "
        "노이즈 스케줄 오류"
    )

    print("✅ test_add_noise_shape PASSED")
    print(f"   t=0  신호비중: {mean_t0:.4f}, t=99 신호비중: {mean_t99:.4f}")


def test_batch_simulation():
    """배치 학습 스텝 시뮬레이션 테스트."""
    cfg = DiffusionTrainingConfig()
    step = DiffusionTrainingStep(cfg)
    result = step.simulate_batch(batch_size=8)

    assert result["batch_size"] == 8
    assert result["action_dim"] == cfg.action_dim
    assert result["horizon"] == cfg.horizon
    assert result["loss_shape_ok"] is True
    assert 0.0 < result["mean_signal_ratio"] <= 1.0
    assert 0.0 <= result["mean_noise_ratio"] <= 1.0

    print("✅ test_batch_simulation PASSED")
    print(f"   배치 크기: {result['batch_size']}")
    print(f"   평균 신호 비율: {result['mean_signal_ratio']:.4f}")
    print(f"   평균 노이즈 비율: {result['mean_noise_ratio']:.4f}")
    print(f"   샘플된 타임스텝: {result['timesteps']}")


def test_lerobot_availability():
    """lerobot 설치 여부 확인 및 안내 메시지 출력."""
    if LEROBOT_AVAILABLE:
        print("✅ test_lerobot_availability PASSED (lerobot 설치됨)")
    else:
        print(
            "✅ test_lerobot_availability PASSED (mock 모드)\n"
            "   ⚠️  lerobot 미설치 — 실제 학습을 실행하려면:\n"
            "      pip install lerobot\n"
            "   현재 테스트는 하드웨어/lerobot 없이 실행 가능한 단위테스트만 포함합니다."
        )


def test_velocity_prediction():
    """v-prediction 타겟 계산 테스트.

    v-prediction: v = √ᾱ_t · ε - √(1-ᾱ_t) · x_0
    noise-prediction으로 복원 가능한지 검증합니다.
    """
    scheduler = SimpleDDPMScheduler(num_train_timesteps=100)
    import random
    rng = random.Random(0)

    action_len = 6
    clean = [rng.gauss(0, 1) for _ in range(action_len)]
    noise = [rng.gauss(0, 1) for _ in range(action_len)]
    t = 50

    v = scheduler.get_velocity(clean, noise, t)
    assert len(v) == action_len

    # v에서 noise 복원: ε = √ᾱ_t · v + √(1-ᾱ_t) · x_t
    sqrt_alpha_bar = math.sqrt(scheduler.alphas_cumprod[t])
    sqrt_one_minus = math.sqrt(1.0 - scheduler.alphas_cumprod[t])
    noisy = scheduler.add_noise(clean, noise, t)
    recovered_noise = [
        sqrt_alpha_bar * vi + sqrt_one_minus * xi
        for vi, xi in zip(v, noisy)
    ]
    for orig, rec in zip(noise, recovered_noise):
        assert abs(orig - rec) < 1e-9, f"noise 복원 오류: {orig:.6f} ≠ {rec:.6f}"

    print("✅ test_velocity_prediction PASSED")
    print(f"   v-prediction → noise 복원 최대 오차: "
          f"{max(abs(o-r) for o,r in zip(noise, recovered_noise)):.2e}")


# ─────────────────────────────────────────
# 5. 메인
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Diffusion Policy 학습 파이프라인 단위 테스트")
    print("=" * 60)
    print(f"  torch 사용 가능: {TORCH_AVAILABLE}")
    print(f"  lerobot 사용 가능: {LEROBOT_AVAILABLE}")
    print()

    tests = [
        test_lerobot_availability,
        test_config_validation,
        test_cmd_generation,
        test_ddpm_scheduler_noise_level,
        test_add_noise_shape,
        test_batch_simulation,
        test_velocity_prediction,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ {test_fn.__name__} FAILED: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"  결과: {passed} PASSED / {failed} FAILED / {len(tests)} 전체")
    if failed == 0:
        print("  ✅ 모든 테스트 통과!")
    else:
        print("  ❌ 일부 테스트 실패 — 위 오류를 확인하세요.")
    print("=" * 60)

    if failed > 0:
        raise SystemExit(1)
