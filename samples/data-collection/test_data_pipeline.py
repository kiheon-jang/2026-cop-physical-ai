"""
샘플: 데이터 수집 파이프라인 테스트
에피소드 구조, 저장 형식, 메타데이터 검증

Requirements:
    pip install lerobot[feetech]
    pip install datasets
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import time


# ─────────────────────────────────────────
# 1. 에피소드 메타데이터 구조
# ─────────────────────────────────────────
@dataclass
class EpisodeMeta:
    """수집된 에피소드 메타데이터"""
    episode_id: int
    task: str
    success: bool
    num_frames: int
    duration_sec: float
    camera_keys: List[str]
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "task": self.task,
            "success": self.success,
            "num_frames": self.num_frames,
            "duration_sec": self.duration_sec,
            "camera_keys": self.camera_keys,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


# ─────────────────────────────────────────
# 2. 데이터셋 설정
# ─────────────────────────────────────────
@dataclass
class DataCollectionConfig:
    """데이터 수집 설정"""
    # 로봇 설정
    follower_port: str = "/dev/tty.usbmodem5AE60573201"
    leader_port: str = "/dev/tty.usbmodem5AE60537131"
    robot_id: str = "hdel_iot_01"

    # 데이터셋 설정
    dataset_repo_id: str = "kiheon-jang/hdel_iot_pick_place_v1"
    target_episodes: int = 50
    fps: int = 30

    # 카메라 설정
    cameras: Dict = field(default_factory=lambda: {
        "top": {"type": "opencv", "index": 0, "width": 640, "height": 480, "fps": 30},
        "gripper": {"type": "opencv", "index": 2, "width": 640, "height": 480, "fps": 30},
    })

    # 태스크 정의
    task_description: str = "Pick and place object from A to B"

    def to_lerobot_cmd(self) -> str:
        """LeRobot record 명령어 생성"""
        cameras_str = " ".join([
            f"--robot.cameras.{k}='{json.dumps(v)}'"
            for k, v in self.cameras.items()
        ])
        return f"""lerobot-record \\
  --robot.type=so101_follower \\
  --robot.port={self.follower_port} \\
  --robot.id={self.robot_id}_follower_arm \\
  --teleop.type=so101_leader \\
  --teleop.port={self.leader_port} \\
  --teleop.id={self.robot_id}_leader_arm \\
  {cameras_str} \\
  --dataset.repo_id={self.dataset_repo_id} \\
  --dataset.num_episodes={self.target_episodes} \\
  --dataset.fps={self.fps}"""


# ─────────────────────────────────────────
# 3. 로컬 에피소드 로그 관리
# ─────────────────────────────────────────
class EpisodeLogger:
    """에피소드 수집 현황 추적"""

    def __init__(self, log_path: Path = Path("episode_log.jsonl")):
        self.log_path = log_path
        self.episodes: List[EpisodeMeta] = []

    def add_episode(self, meta: EpisodeMeta):
        self.episodes.append(meta)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(meta.to_dict()) + "\n")

    def summary(self) -> dict:
        total = len(self.episodes)
        success = sum(1 for e in self.episodes if e.success)
        return {
            "total_episodes": total,
            "success_episodes": success,
            "success_rate": f"{success/total*100:.1f}%" if total > 0 else "N/A",
            "avg_duration": f"{sum(e.duration_sec for e in self.episodes)/total:.2f}s" if total > 0 else "N/A",
        }


# ─────────────────────────────────────────
# 4. 단위 테스트
# ─────────────────────────────────────────
def test_episode_meta_serialization():
    """에피소드 메타데이터 직렬화 테스트"""
    meta = EpisodeMeta(
        episode_id=0,
        task="pick_place",
        success=True,
        num_frames=150,
        duration_sec=5.0,
        camera_keys=["top", "gripper"],
        timestamp="2026-04-21T09:00:00",
    )
    d = meta.to_dict()
    assert d["episode_id"] == 0
    assert d["success"] is True
    assert "top" in d["camera_keys"]
    print("✅ test_episode_meta_serialization PASSED")


def test_config_cmd_generation():
    """LeRobot 명령어 생성 테스트"""
    config = DataCollectionConfig()
    cmd = config.to_lerobot_cmd()
    assert "lerobot-record" in cmd
    assert "so101_follower" in cmd
    assert "so101_leader" in cmd
    assert "top" in cmd
    assert "gripper" in cmd
    print("✅ test_config_cmd_generation PASSED")
    print("\n생성된 명령어:")
    print(cmd)


def test_episode_logger():
    """에피소드 로거 테스트"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jsonl", mode='w', delete=False) as f:
        log_path = Path(f.name)

    logger = EpisodeLogger(log_path)
    for i in range(5):
        logger.add_episode(EpisodeMeta(
            episode_id=i,
            task="pick_place",
            success=(i % 2 == 0),  # 홀수는 실패
            num_frames=100 + i * 10,
            duration_sec=5.0 + i * 0.5,
            camera_keys=["top", "gripper"],
        ))

    summary = logger.summary()
    assert summary["total_episodes"] == 5
    assert summary["success_episodes"] == 3
    print("✅ test_episode_logger PASSED")
    print(f"   수집 현황: {summary}")

    log_path.unlink()


if __name__ == "__main__":
    print("=" * 55)
    print("  데이터 수집 파이프라인 단위 테스트")
    print("=" * 55)

    test_episode_meta_serialization()
    test_config_cmd_generation()
    test_episode_logger()

    print("\n✅ 모든 테스트 통과!")
