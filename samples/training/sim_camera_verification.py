import mujoco as mj
import mujoco.viewer
import numpy as np
import time
import os

# Absolute path to the MJCF model file
MODEL_PATH = '/Users/markmini/Documents/dev/2026-cop-physical-ai/models/SO-ARM100/Simulation/SO101/so101_new_calib.xml'
OUTPUT_DIR = '/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/'

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    model = mj.MjModel.from_xml_path(MODEL_PATH)
    data = mj.MjData(model)
except Exception as e:
    print(f"Error loading MJCF model: {e}")
    exit()

# Setup renderer for offscreen rendering
renderer_overhead = mj.Renderer(model, height=480, width=640)
renderer_gripper = mj.Renderer(model, height=240, width=320)

# Find camera IDs
overhead_camera_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_CAMERA, 'overhead_camera')
gripper_camera_id = mj.mj_name2id(model, mj.mjtObj.mjOBJ_CAMERA, 'gripper_camera')

if overhead_camera_id == -1:
    print("Overhead camera not found in the model.")
    exit()
if gripper_camera_id == -1:
    print("Gripper camera not found in the model.")
    exit()

# Simulate and render frames
duration = 1  # seconds
framerate = 30  # Hz
n_frames = int(duration * framerate)

print(f"Starting simulation for {duration} seconds, capturing {n_frames} frames...")

for i in range(n_frames):
    mj.mj_step(model, data)

    # Render and save overhead camera image
    renderer_overhead.update_scene(data, camera=overhead_camera_id)
    overhead_img = renderer_overhead.render()
    overhead_filename = os.path.join(OUTPUT_DIR, f"overhead_frame_{i:04d}.png")
    from PIL import Image
    Image.fromarray(overhead_img).save(overhead_filename)

    # Render and save gripper camera image
    renderer_gripper.update_scene(data, camera=gripper_camera_id)
    gripper_img = renderer_gripper.render()
    gripper_filename = os.path.join(OUTPUT_DIR, f"gripper_frame_{i:04d}.png")
    Image.fromarray(gripper_img).save(gripper_filename)

    # We don't need time.sleep in offscreen rendering
    # time.sleep(1/framerate)

print(f"Captured {n_frames} frames from both cameras.")
print(f"Images saved to: {OUTPUT_DIR}")
