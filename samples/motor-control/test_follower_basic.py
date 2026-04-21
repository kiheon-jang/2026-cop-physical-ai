"""
샘플: SO-ARM101 모터 기본 제어 테스트
단위 테스트용 - 실제 하드웨어 연결 없이 구조 확인 가능

Requirements:
    pip install lerobot[feetech]
"""

import time
from typing import Optional


# ─────────────────────────────────────────
# 1. 포트 자동 감지
# ─────────────────────────────────────────
def find_robot_port() -> Optional[str]:
    """연결된 모터 컨트롤러 포트를 자동으로 찾습니다."""
    try:
        from lerobot.common.robot_devices.motors.feetech import FeetechMotorsBus
        # lerobot-find-port 와 동일한 동작
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            print(f"  발견된 포트: {port.device} - {port.description}")
        return ports[0].device if ports else None
    except ImportError:
        print("lerobot 미설치 - pip install 'lerobot[feetech]'")
        return None


# ─────────────────────────────────────────
# 2. Follower 연결 & 상태 확인
# ─────────────────────────────────────────
def check_follower_status(port: str, robot_id: str = "test_follower"):
    """Follower 모터 6개의 현재 위치/온도/부하를 출력합니다."""
    from lerobot.common.robot_devices.robots.factory import make_robot
    from lerobot.common.robot_devices.utils import RobotDeviceAlreadyConnectedError

    robot_config = {
        "type": "so101_follower",
        "port": port,
        "id": robot_id,
        "use_degrees": True,
    }

    try:
        robot = make_robot(robot_config)
        robot.connect()

        obs = robot.get_observation()
        print("\n📊 현재 Follower 상태:")
        print(f"  {'관절':<20} {'위치(°)':>10} {'온도(°C)':>10} {'부하(%)':>10}")
        print("  " + "-" * 55)

        joint_names = [
            "shoulder_pan", "shoulder_lift", "elbow_flex",
            "wrist_flex", "wrist_roll", "gripper"
        ]
        for i, name in enumerate(joint_names):
            pos = obs.get(f"observation.state.{name}", "N/A")
            print(f"  {name:<20} {str(pos):>10}")

        robot.disconnect()

    except RobotDeviceAlreadyConnectedError:
        print("⚠️  이미 연결된 장치입니다. 기존 연결을 종료 후 재시도하세요.")
    except Exception as e:
        print(f"❌ 오류: {e}")


# ─────────────────────────────────────────
# 3. 간단한 모션 테스트 (홈 포지션)
# ─────────────────────────────────────────
def move_to_home(port: str, robot_id: str = "test_follower"):
    """모든 모터를 홈 포지션(0°)으로 천천히 이동합니다."""
    from lerobot.common.robot_devices.robots.factory import make_robot

    robot_config = {
        "type": "so101_follower",
        "port": port,
        "id": robot_id,
        "use_degrees": True,
    }

    home_position = {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.0,
        "elbow_flex": 90.0,
        "wrist_flex": 0.0,
        "wrist_roll": 0.0,
        "gripper": 0.0,
    }

    robot = make_robot(robot_config)
    robot.connect()

    print("🏠 홈 포지션으로 이동 중...")
    robot.send_action(home_position)
    time.sleep(2.0)
    print("✅ 완료")

    robot.disconnect()


# ─────────────────────────────────────────
# 4. 단위 테스트
# ─────────────────────────────────────────
def test_motor_ids_sequence():
    """모터 ID 순서 검증 (하드웨어 없이 실행 가능)"""
    FOLLOWER_MOTOR_IDS = {
        "shoulder_pan": 1,
        "shoulder_lift": 2,
        "elbow_flex": 3,
        "wrist_flex": 4,
        "wrist_roll": 5,
        "gripper": 6,
    }

    assert len(FOLLOWER_MOTOR_IDS) == 6, "모터 6개여야 함"
    assert list(FOLLOWER_MOTOR_IDS.values()) == list(range(1, 7)), "ID 1~6 순서여야 함"
    print("✅ test_motor_ids_sequence PASSED")


def test_home_position_range():
    """홈 포지션 각도 범위 검증"""
    home = {
        "shoulder_pan": 0.0,
        "shoulder_lift": 0.0,
        "elbow_flex": 90.0,
        "wrist_flex": 0.0,
        "wrist_roll": 0.0,
        "gripper": 0.0,
    }
    for joint, angle in home.items():
        assert -180.0 <= angle <= 180.0, f"{joint}: 각도 범위 초과 ({angle}°)"
    print("✅ test_home_position_range PASSED")


if __name__ == "__main__":
    print("=" * 50)
    print("  SO-ARM101 모터 제어 단위 테스트")
    print("=" * 50)

    # 하드웨어 없이 실행 가능한 테스트
    test_motor_ids_sequence()
    test_home_position_range()

    # 하드웨어 연결 시 실행
    # port = find_robot_port()
    # if port:
    #     check_follower_status(port)
    #     move_to_home(port)
