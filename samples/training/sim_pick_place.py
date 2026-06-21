import mujoco
import numpy as np
import time
import os
import json
import imageio

# MJCF 파일 경로
MODEL_PATH = '/Users/markmini/Documents/dev/2026-cop-physical-ai/models/SO-ARM100/Simulation/SO101/so101_new_calib.xml'
VIDEO_PATH = '/Users/markmini/Documents/dev/2026-cop-physical-ai/research/simulation/video/pick_place_demo.mp4'
os.makedirs(os.path.dirname(VIDEO_PATH), exist_ok=True)

# 모델 로드
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

# 렌더러 설정 (headless)
renderer = mujoco.Renderer(model, height=480, width=640)

# 시뮬레이션 초기화
mujoco.mj_resetData(model, data)

# 그리퍼 조인트 ID (MJCF의 'gripper' 조인트 이름)
gripper_joint_id = model.jnt('gripper').id
if gripper_joint_id == -1:
    raise ValueError("Gripper joint 'gripper' not found in model.")

# 그리퍼 액추에이터 ID
gripper_actuator_id = model.actuator('gripper').id
if gripper_actuator_id == -1:
    raise ValueError("Gripper actuator 'gripper' not found in model.")

# 큐브 body ID
cube_body_id = model.body('cube').id
if cube_body_id == -1:
    raise ValueError("Cube body 'cube' not found in model.")

# 팔의 관절 액추에이터 ID (예시: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll)
joint_actuator_ids = [
    model.actuator('shoulder_pan').id,
    model.actuator('shoulder_lift').id,
    model.actuator('elbow_flex').id,
    model.actuator('wrist_flex').id,
    model.actuator('wrist_roll').id
]
joint_actuator_ids = [idx for idx in joint_actuator_ids if idx != -1]

# 그리퍼 제어 함수 (0: 열림, 1: 닫힘)
def set_gripper_state(state):
    # gripper_ctrl_range = model.actuator_ctrlrange[gripper_actuator_id]
    # data.ctrl[gripper_actuator_id] = gripper_ctrl_range[0] if state == 0 else gripper_ctrl_range[1]
    # NOTE: gripper의 ctrlrange가 특정 범위로 설정되어 있어, 0과 1로 직접 제어하는 대신 해당 범위를 이용
    if state == 0: # 열림
        data.ctrl[gripper_actuator_id] = model.actuator_ctrlrange[gripper_actuator_id, 0]
    else: # 닫힘
        data.ctrl[gripper_actuator_id] = model.actuator_ctrlrange[gripper_actuator_id, 1]

# 성공 기준 (PHASE_ROADMAP W4 5/22~24):
#   - 그리퍼가 큐브 ±5mm 접근 (approach_ok)
#   - 큐브를 Z+50mm 이상 들어올림 (lift_ok)
APPROACH_THRESHOLD_M = 0.005
LIFT_THRESHOLD_M = 0.050

# 픽-앤-플레이스 시나리오
def pick_and_place_scenario():
    frames = []
    duration = 5  # 시뮬레이션 시간 (초)
    framerate = 60 # 프레임레이트
    approach_ok = False
    lift_ok = False
    min_approach_dist = float('inf')
    max_lift_height = 0.0

    # 초기 관절 위치 (로봇을 준비 상태로)
    initial_qpos = np.array([0, 0, 0, 0, 0]) # 예시: 어깨 팬, 리프트, 팔꿈치 플렉스, 손목 플렉스, 손목 롤

    # 로봇 초기 위치 설정 (관절 제어)
    for i, actuator_id in enumerate(joint_actuator_ids):
        data.ctrl[actuator_id] = initial_qpos[i]
    
    # 큐브 초기 위치 (MJCF에 정의됨)
    cube_initial_pos = model.body_pos[cube_body_id].copy()

    # 시뮬레이션 루프
    for i in range(int(duration / model.opt.timestep)):
        mujoco.mj_step(model, data)
        renderer.update_scene(data)
        frames.append(renderer.render())

        # 간단한 Pick-Place 로직 (예시)
        # 1. 큐브 위로 이동 (대략적인 위치)
        if i < 0.2 * duration * framerate: # 초기 20% 시간 동안
            data.ctrl[model.actuator('shoulder_lift').id] = -0.5
            data.ctrl[model.actuator('elbow_flex').id] = -0.5
            set_gripper_state(0) # 그리퍼 열기

        # 2. 큐브에 접근
        elif i < 0.4 * duration * framerate:
            # 그리퍼의 Z 위치를 큐브 위로 조정
            gripper_pos = data.site_xpos[model.site('gripperframe').id] # 그리퍼 끝단의 site
            target_pos = cube_initial_pos + np.array([0, 0, 0.08]) # 큐브 위로 8cm

            dist = float(np.linalg.norm(gripper_pos - target_pos))
            if dist < min_approach_dist:
                min_approach_dist = dist
            if dist <= APPROACH_THRESHOLD_M:
                approach_ok = True

            # 그리퍼의 현재 위치가 목표 위치에 근접했는지 확인
            if dist > APPROACH_THRESHOLD_M: # 5mm 이내
                # 관절 제어를 통해 그리퍼를 목표 위치로 이동 (간단한 예시)
                # 실제 로봇 제어에서는 역기구학(IK) 필요
                data.ctrl[model.actuator('shoulder_lift').id] -= 0.001
                data.ctrl[model.actuator('elbow_flex').id] += 0.001
            else:
                set_gripper_state(0) # 그리퍼 열림 유지

        # 3. 큐브 잡기
        elif i < 0.6 * duration * framerate:
            set_gripper_state(1) # 그리퍼 닫기

        # 4. 큐브 들어 올리기
        elif i < 0.8 * duration * framerate:
            data.ctrl[model.actuator('shoulder_lift').id] += 0.001
            data.ctrl[model.actuator('elbow_flex').id] -= 0.001
            
            # 큐브가 Z+50mm 이상 올라갔는지 확인
            lift_height = float(data.body('cube').xpos[2] - cube_initial_pos[2])
            if lift_height > max_lift_height:
                max_lift_height = lift_height
            if lift_height >= LIFT_THRESHOLD_M:
                lift_ok = True

        # 5. 큐브 놓기 (대략적인 위치)
        else:
            data.ctrl[model.actuator('shoulder_lift').id] = 0
            data.ctrl[model.actuator('elbow_flex').id] = 0
            set_gripper_state(0) # 그리퍼 열기
    
    # MP4로 비디오 저장
    if frames:
        imageio.mimsave(VIDEO_PATH, frames, fps=framerate)
        print(f"Pick-Place demo video saved to: {VIDEO_PATH}")

    success = approach_ok and lift_ok
    result = {
        "status": "success" if success else "fail",
        "approach_ok": approach_ok,
        "lift_ok": lift_ok,
        "min_approach_dist_m": min_approach_dist if min_approach_dist != float('inf') else None,
        "max_lift_height_m": max_lift_height,
        "approach_threshold_m": APPROACH_THRESHOLD_M,
        "lift_threshold_m": LIFT_THRESHOLD_M,
        "video_path": VIDEO_PATH,
    }
    print(json.dumps(result, ensure_ascii=False))
    return success

ok = pick_and_place_scenario()
renderer.close()
raise SystemExit(0 if ok else 1)
