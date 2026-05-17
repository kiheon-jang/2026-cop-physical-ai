import mujoco
import numpy as np
import os
import sys

MJCF_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "SO-ARM100", "Simulation", "SO101", "so101_new_calib.xml"
)
MJCF_PATH = os.path.abspath(MJCF_PATH)

if not os.path.exists(MJCF_PATH):
    print(f"Error: MJCF not found at {MJCF_PATH}", file=sys.stderr)
    sys.exit(1)

model = mujoco.MjModel.from_xml_path(MJCF_PATH)
data = mujoco.MjData(model)

ACTUATOR_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

actuator_ids = []
for name in ACTUATOR_NAMES:
    aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    if aid < 0:
        print(f"Error: actuator '{name}' not found", file=sys.stderr)
        sys.exit(1)
    actuator_ids.append(aid)

# qpos address for each actuator's driven joint
joint_qpos_addrs = []
for aid in actuator_ids:
    jnt_id = model.actuator_trnid[aid, 0]
    joint_qpos_addrs.append(int(model.jnt_qposadr[jnt_id]))

DURATION = 5.0       # seconds
SAMPLE_DT = 0.01     # 100 Hz
AMPLITUDE = 0.5      # radians
FREQUENCY = 1.0      # Hz
PHASES = [i * np.pi / len(ACTUATOR_NAMES) for i in range(len(ACTUATOR_NAMES))]

next_sample_t = 0.0

while data.time < DURATION:
    if data.time >= next_sample_t - 1e-9:
        angles = [data.qpos[addr] for addr in joint_qpos_addrs]
        row = f"{data.time:.3f} " + " ".join(f"{a:.6f}" for a in angles)
        print(row)
        next_sample_t += SAMPLE_DT

    for i, aid in enumerate(actuator_ids):
        data.ctrl[aid] = AMPLITUDE * np.sin(2 * np.pi * FREQUENCY * data.time + PHASES[i])

    mujoco.mj_step(model, data)