#!/Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3
"""
SO-ARM101 관절각 비교 시뮬레이션
목표 각도를 설정하고 시뮬레이션이 수렴한 뒤 실제 관절각을 비교 출력한다.
"""

import mujoco
import numpy as np
import os
import sys

MJCF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "models", "SO-ARM100", "Simulation", "SO101", "so101_new_calib.xml")
)

if not os.path.exists(MJCF_PATH):
    print(f"Error: MJCF not found at {MJCF_PATH}", file=sys.stderr)
    sys.exit(1)

model = mujoco.MjModel.from_xml_path(MJCF_PATH)
data = mujoco.MjData(model)

JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex",
               "wrist_flex", "wrist_roll", "gripper"]

# 목표 관절각 (단위: radian) — 각 관절의 범위 내에서 임의 설정
TARGET_DEG = {
    "shoulder_pan":   30.0,
    "shoulder_lift": -20.0,
    "elbow_flex":     45.0,
    "wrist_flex":    -25.0,
    "wrist_roll":     35.0,
    "gripper":        50.0,   # gripper range: -10°~100°
}
TARGET_RAD = {k: np.deg2rad(v) for k, v in TARGET_DEG.items()}

# actuator id 및 qpos 주소 수집
actuator_ids = []
joint_qpos_addrs = []
for name in JOINT_NAMES:
    aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    if aid < 0:
        print(f"Error: actuator '{name}' not found", file=sys.stderr)
        sys.exit(1)
    actuator_ids.append(aid)
    jnt_id = model.actuator_trnid[aid, 0]
    joint_qpos_addrs.append(int(model.jnt_qposadr[jnt_id]))

# 목표값 고정 설정
for aid, name in zip(actuator_ids, JOINT_NAMES):
    data.ctrl[aid] = TARGET_RAD[name]

SETTLE_TIME = 3.0   # 수렴 대기 시간 (초)
PRINT_DT    = 0.5   # 출력 간격 (초)

print(f"{'시간(s)':<8}", end="")
for name in JOINT_NAMES:
    print(f"  {name:>14}", end="")
print()

next_print = 0.0
while data.time <= SETTLE_TIME + 1e-9:
    if data.time >= next_print - 1e-9:
        angles = [data.qpos[addr] for addr in joint_qpos_addrs]
        print(f"{data.time:<8.3f}", end="")
        for a in angles:
            print(f"  {np.rad2deg(a):>13.4f}°", end="")
        print()
        next_print += PRINT_DT
    mujoco.mj_step(model, data)

# 최종 비교 출력
final_angles = [data.qpos[addr] for addr in joint_qpos_addrs]
print()
print(f"{'관절':<18}  {'목표(deg)':>10}  {'실제(deg)':>10}  {'오차(deg)':>10}")
print("-" * 56)
for name, addr in zip(JOINT_NAMES, joint_qpos_addrs):
    target_d = TARGET_DEG[name]
    actual_d = np.rad2deg(data.qpos[addr])
    error_d  = actual_d - target_d
    print(f"{name:<18}  {target_d:>10.4f}  {actual_d:>10.4f}  {error_d:>10.4f}")
