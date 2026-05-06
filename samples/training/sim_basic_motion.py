
import mujoco
import mujoco.viewer
import numpy as np
import os

# Absolute path to the MJCF model
MODEL_PATH = "/Users/markmini/Documents/dev/2026-cop-physical-ai/SO-ARM100/Simulation/SO101/so101_new_calib.xml"

if not os.path.exists(MODEL_PATH):
    print(f"Error: Model file not found at {MODEL_PATH}")
    exit(1)

# Load the model and data
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

# Find the joint IDs for the robot arm
# Assuming the robot has 6 joints based on the 6-DoF description
# This might need refinement based on the actual model's joint names
joint_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"] # Exclude gripper for now 
joint_ids = [model.joint(name).id for name in joint_names if model.joint(name).id != -1]

if not joint_ids:
    print("Warning: No controllable joints found. Please check joint names in the MJCF model.")
    # Attempt to use all free joints if no specific names found
    joint_ids = [i for i in range(model.nu)]
    if not joint_ids:
        print("Error: No joints available to control. Exiting.")
        exit(1)
    else:
        print(f"Controlling {len(joint_ids)} joints using default indices.")

# Simulation duration and control frequency
duration = 5  # seconds
framerate = 60  # Hz
n_frames = int(duration * framerate)

# Create a viewer
with mujoco.viewer.launch_passive(model, data) as viewer:
    # Set the camera to an overhead view if possible
    # You might need to adjust these values to get a good overhead view
    # Example for setting a specific camera if available in the model
    # If the model has named cameras, you can use: viewer.cam.fixedcamid = model.camera('overhead_camera_name').id
    # Otherwise, you can adjust the spectator camera
    viewer.cam.azimuth = 90
    viewer.cam.elevation = -45
    viewer.cam.distance = 2
    viewer.cam.lookat[0] = 0
    viewer.cam.lookat[1] = 0
    viewer.cam.lookat[2] = 0.5


    # Simulation loop
    for i in range(n_frames):
        # Calculate sine wave joint targets
        # Assuming a range of -1 to 1 radian for demonstration
        # You may need to adjust amplitude and frequency
        amplitude = np.pi / 4  # 45 degrees
        frequency = 1 # Hz
        target_angle = amplitude * np.sin(2 * np.pi * frequency * data.time)

        # Apply the same target to all controllable joints
        for jid in joint_ids:
            if jid < data.ctrl.shape[0]: # Ensure jid is a valid control index
                data.ctrl[jid] = target_angle
            
        # Step the simulation
        mujoco.mj_step(model, data)

        # Update viewer and synchronize
        viewer.sync()

        # Check if the viewer window was closed
        if viewer.is_closing():
            break

print("Simulation finished.")
