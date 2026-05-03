
import mujoco
import mujoco.viewer
import numpy as np
import os

# Construct the absolute path to the MJCF file
mjcf_path = os.path.join(
    "/Users/markmini/Documents/dev/2026-cop-physical-ai",
    "SO-ARM100",
    "Simulation",
    "SO101",
    "so101_new_calib.xml"
)

# Check if the file exists
if not os.path.exists(mjcf_path):
    print(f"Error: MJCF file not found at {mjcf_path}")
    exit()

try:
    model = mujoco.MjModel.from_xml_path(mjcf_path)
    data = mujoco.MjData(model)
except Exception as e:
    print(f"Error loading MuJoCo model: {e}")
    exit()

print("MuJoCo model loaded successfully. Launching viewer...")

with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.sync()
    
    # Animation parameters
    duration = 5  # seconds
    frequency = 1  # Hz
    amplitude = 0.5  # radians

    # Get joint IDs for the 6-DoF arm (assuming 6 joints to animate)
    # This part might need adjustment based on the actual joint names in so101_new_calib.xml
    # For now, let's try to animate the first 6 joints if they exist.
    joint_ids = []
    for i in range(min(model.njnt, 6)):  # Animate up to the first 6 joints
        joint_ids.append(i)
        print(f"Animating joint: {model.joint(i).name if model.joint(i).name else f'joint_{i}'}")

    start_time = data.time
    while viewer.is_running() and data.time - start_time < duration:
        current_time = data.time - start_time
        
        for joint_id in joint_ids:
            # Simple sinusoidal movement
            data.ctrl[joint_id] = amplitude * np.sin(2 * np.pi * frequency * current_time)
            
        mujoco.mj_step(model, data)
        viewer.sync()

print("Animation finished.")
