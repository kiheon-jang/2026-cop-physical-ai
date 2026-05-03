
import mujoco
import numpy as np
import os
import imageio.v3 as iio

# Construct the absolute path to the MJCF file
mjcf_path = os.path.join(
    "/Users/markmini/Documents/dev/2026-cop-physical-ai",
    "SO-ARM100",
    "Simulation",
    "SO101",
    "so101_new_calib.xml"
)

# Output video path
output_video_dir = os.path.join(
    "/Users/markmini/Documents/dev/2026-cop-physical-ai",
    "research",
    "simulation",
    "video"
)
output_video_path = os.path.join(output_video_dir, "sim_6dof_animation.mp4")

# Ensure output directory exists
os.makedirs(output_video_dir, exist_ok=True)

# Check if the MJCF file exists
if not os.path.exists(mjcf_path):
    print(f"Error: MJCF file not found at {mjcf_path}")
    exit()

try:
    model = mujoco.MjModel.from_xml_path(mjcf_path)
    data = mujoco.MjData(model)
except Exception as e:
    print(f"Error loading MuJoCo model: {e}")
    exit()

print("MuJoCo model loaded successfully. Generating video...")

# Renderer setup
renderer = mujoco.Renderer(model)
frames = []

# Animation parameters
duration = 5  # seconds
frame_rate = 30 # frames per second
frequency = 1  # Hz
amplitude = 0.5  # radians

# Get joint IDs for the 6-DoF arm (assuming first 6 joints)
joint_ids = []
for i in range(min(model.njnt, 6)): # Animate up to the first 6 joints
    joint_ids.append(i)
    print(f"Animating joint: {model.joint(i).name if model.joint(i).name else f'joint_{i}'}")

# Simulate and render frames
mujoco.mj_resetData(model, data)
while data.time < duration:
    for joint_id in joint_ids:
        # Simple sinusoidal movement
        data.ctrl[joint_id] = amplitude * np.sin(2 * np.pi * frequency * data.time)
    
    mujoco.mj_step(model, data)
    renderer.update_scene(data)
    frames.append(renderer.render())

print(f"Generated {len(frames)} frames. Saving video to {output_video_path}...")
iio.imwrite(output_video_path, frames, fps=frame_rate)
print("Video saved successfully.")

renderer.close()
