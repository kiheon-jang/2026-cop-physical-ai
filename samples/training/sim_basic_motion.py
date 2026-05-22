"""sim_basic_motion.py — SO-ARM101 기본 sin파 동작 시연 (headless 기본, 크론 안전)

기본 실행 (headless, 크론/CI 환경):
    .venv/bin/python3 samples/training/sim_basic_motion.py

인터랙티브 뷰어 (로컬 테스트 전용):
    .venv/bin/python3 samples/training/sim_basic_motion.py --interactive
"""

import argparse
import mujoco
import numpy as np
import os

REPO_ROOT = "/Users/markmini/Documents/dev/2026-cop-physical-ai"
MODEL_PATH = os.path.join(REPO_ROOT, "SO-ARM100/Simulation/SO101/so101_new_calib.xml")


def run_headless(model, data, duration=5.0, fps=30):
    """Renderer 방식 — headless 환경(크론) 안전. 프레임 수 반환."""
    renderer = mujoco.Renderer(model, height=480, width=640)
    frames = []

    frequency = 1.0   # Hz
    amplitude = 0.4   # radians (~23°)

    mujoco.mj_resetData(model, data)
    n_joints = min(model.nu, 6)

    while data.time < duration:
        for j in range(n_joints):
            data.ctrl[j] = amplitude * np.sin(2 * np.pi * frequency * data.time)
        mujoco.mj_step(model, data)
        renderer.update_scene(data)
        frames.append(renderer.render().copy())

    renderer.close()
    print(f"[headless] {len(frames)} frames generated, sim_time={data.time:.2f}s")
    return frames


def run_interactive(model, data, duration=5.0):
    """viewer 방식 — 로컬 GUI 전용. 크론에서 절대 호출 금지."""
    import mujoco.viewer

    frequency = 1.0
    amplitude = 0.4
    n_joints = min(model.nu, 6)

    with mujoco.viewer.launch_passive(model, data) as viewer:
        viewer.cam.azimuth = 90
        viewer.cam.elevation = -45
        viewer.cam.distance = 2.0
        viewer.cam.lookat[:] = [0, 0, 0.5]

        while data.time < duration and viewer.is_running():
            for j in range(n_joints):
                data.ctrl[j] = amplitude * np.sin(2 * np.pi * frequency * data.time)
            mujoco.mj_step(model, data)
            viewer.sync()

    print(f"[interactive] sim_time={data.time:.2f}s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive", action="store_true",
                        help="GUI viewer 사용 (로컬 전용, 크론 실행 금지)")
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print(f"Error: MJCF not found at {MODEL_PATH}")
        raise SystemExit(1)

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)
    print(f"Model loaded: {model.njnt} joints, {model.nu} actuators")

    if args.interactive:
        run_interactive(model, data, args.duration)
    else:
        run_headless(model, data, args.duration)


if __name__ == "__main__":
    main()
