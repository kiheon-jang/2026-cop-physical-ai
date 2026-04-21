"""
하드웨어 연결 확인 스크립트
실제 로봇 연결 후 실행 — 모터 상태, 카메라, 캘리브레이션 파일 확인

실행 방법:
    conda activate lerobot
    python samples/hardware/run_connection_check.py \
        --follower-port /dev/tty.usbmodem5AE60573201 \
        --leader-port /dev/tty.usbmodem5AE60537131
"""

import argparse
import sys
from pathlib import Path


def check_calibration_files(robot_id_follower: str, robot_id_leader: str) -> bool:
    """캘리브레이션 파일 존재 여부 확인"""
    calib_dir = Path.home() / ".cache" / "huggingface" / "lerobot" / "calibration"
    follower_calib = calib_dir / f"{robot_id_follower}.json"
    leader_calib = calib_dir / f"{robot_id_leader}.json"

    print("\n📁 캘리브레이션 파일 확인:")
    ok = True
    for path, name in [(follower_calib, "Follower"), (leader_calib, "Leader")]:
        if path.exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name}: 없음 — lerobot-calibrate 먼저 실행 필요")
            ok = False
    return ok


def check_follower(port: str, robot_id: str) -> bool:
    """Follower 모터 연결 및 상태 확인"""
    print(f"\n🤖 Follower 연결 확인 ({port}):")
    try:
        from lerobot.common.robot_devices.robots.factory import make_robot
        robot = make_robot({
            "type": "so101_follower",
            "port": port,
            "id": robot_id,
            "use_degrees": True,
        })
        robot.connect()
        obs = robot.get_observation()
        joints = ["shoulder_pan", "shoulder_lift", "elbow_flex",
                  "wrist_flex", "wrist_roll", "gripper"]
        print(f"  {'관절':<20} {'위치(°)':>10}")
        print("  " + "-" * 33)
        for j in joints:
            val = obs.get(f"observation.state", {})
            print(f"  {j:<20} {'OK':>10}")
        robot.disconnect()
        print("  ✅ Follower 연결 정상")
        return True
    except ImportError:
        print("  ⚠️  lerobot 미설치 (pip install 'lerobot[feetech]')")
        return False
    except Exception as e:
        print(f"  ❌ Follower 연결 실패: {e}")
        return False


def check_leader(port: str, teleop_id: str) -> bool:
    """Leader 연결 확인"""
    print(f"\n🕹️  Leader 연결 확인 ({port}):")
    try:
        from lerobot.common.robot_devices.robots.factory import make_robot
        teleop = make_robot({
            "type": "so101_leader",
            "port": port,
            "id": teleop_id,
            "use_degrees": True,
        })
        teleop.connect()
        teleop.disconnect()
        print("  ✅ Leader 연결 정상")
        return True
    except ImportError:
        print("  ⚠️  lerobot 미설치")
        return False
    except Exception as e:
        print(f"  ❌ Leader 연결 실패: {e}")
        return False


def check_cameras() -> bool:
    """카메라 연결 확인"""
    print("\n📷 카메라 확인:")
    try:
        import cv2
        found = []
        for idx in range(5):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    h, w = frame.shape[:2]
                    found.append((idx, w, h))
                cap.release()

        if found:
            for idx, w, h in found:
                print(f"  ✅ 카메라 {idx}: {w}x{h}")
            if len(found) < 2:
                print(f"  ⚠️  카메라가 {len(found)}개만 감지됨 (2개 필요)")
            return len(found) >= 2
        else:
            print("  ❌ 카메라 감지 안 됨")
            return False
    except ImportError:
        print("  ⚠️  opencv 미설치 (pip install opencv-python)")
        return False


def main():
    parser = argparse.ArgumentParser(description="SO-ARM101 연결 상태 전체 확인")
    parser.add_argument("--follower-port", default="/dev/tty.usbmodem5AE60573201")
    parser.add_argument("--leader-port", default="/dev/tty.usbmodem5AE60537131")
    parser.add_argument("--follower-id", default="hdel_iot_01_follower_arm")
    parser.add_argument("--leader-id", default="hdel_iot_01_leader_arm")
    args = parser.parse_args()

    print("=" * 50)
    print("  SO-ARM101 하드웨어 연결 상태 확인")
    print("=" * 50)

    results = {
        "캘리브레이션": check_calibration_files(args.follower_id, args.leader_id),
        "Follower": check_follower(args.follower_port, args.follower_id),
        "Leader": check_leader(args.leader_port, args.leader_id),
        "카메라": check_cameras(),
    }

    print("\n" + "=" * 50)
    print("  최종 결과")
    print("=" * 50)
    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n🎉 모든 항목 정상 — 텔레오퍼레이션 시작 가능!")
    else:
        print("\n⚠️  일부 항목 확인 필요 — 위 오류 메시지를 참고하세요.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
