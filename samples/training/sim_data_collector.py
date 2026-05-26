"""
CoP Physical AI 프로젝트 - 자동 데이터 수집 스크립트

이 스크립트는 MuJoCo 시뮬레이터를 사용하여 SO-ARM101 로봇팔의 Pick-Place 시나리오 데이터를 자동으로 수집하고,
LeRobot 데이터셋 형식으로 저장합니다.

목표:
*   총 50개의 에피소드를 수집합니다.
*   각 에피소드마다 큐브의 초기 위치를 랜덤하게 변동시킵니다 (x축 ±20mm, y축 ±20mm).
*   데이터셋 에피소드 구조는 다음을 포함해야 합니다:
    *   `observations.images.top`: 오버헤드 카메라에서 캡처한 640x480 RGB 이미지.
    *   `observations.state`: 로봇의 6DoF 관절 위치 (`qpos`).
    *   `actions`: 로봇의 6DoF 제어 신호 (`ctrl`).
    *   `timestamps`: 각 프레임의 타임스탬프.
*   MuJoCo `mujoco.Renderer`를 사용하여 headless 방식으로 렌더링하고 데이터를 수집합니다.
*   LeRobot 데이터셋 저장 패턴: `LeRobotDataset.create(repo_id="local/cop-pickplace", root="data/episodes")`

환경:
*   Python 가상환경 경로: /Users/markmini/Documents/dev/2026-cop-physical-ai/.venv/bin/python3
*   MuJoCo 3.x가 설치되어 있습니다.
*   LeRobot이 설치되어 있습니다.
*   로봇 모델: SO-ARM101 MJCF (경로: Simulation/SO101/so101_new_calib.xml 또는 유사한 MJCF 파일).
    이는 `2026-cop-physical-ai` 디렉토리 안에 있다고 가정합니다.
*   큐브 스펙: 50mm 정육면체, 질량 50g, MJCF body 이름 `cube`, 초기 위치 `pos="0.15 0 0.025"` 기준.

구현 상세:
1.  필요한 라이브러리 (mujoco, numpy, lerobot, etc.) 임포트.
2.  MJCF 모델 로드 및 MuJoCo 시뮬레이션 환경 초기화.
    *   로봇 모델 MJCF 경로를 확인하고 사용합니다.
3.  `mujoco.Renderer`를 사용하여 오버헤드 카메라 렌더러 설정 (640x480).
4.  50개의 에피소드를 반복하는 루프를 구현합니다.
    *   각 에피소드 시작 시 큐브의 초기 위치를 기준 `(0.15, 0, 0.025)`에서 x, y 방향으로 ±0.02 미터 (±20mm) 랜덤하게 변동시킵니다.
        (MuJoCo `m.body_pos` 또는 `d.body_xpos`를 활용).
    *   Pick-Place 동작 시뮬레이션 시퀀스를 정의합니다.
        *   예: 그리퍼 열기 -> 타겟 위로 이동 -> 그리퍼 닫기 -> 들어올리기 -> 특정 위치로 이동 -> 그리퍼 열기 (놓기) -> 그리퍼 닫기.
        *   로봇팔의 관절 제어 (`d.ctrl`)를 사용하여 동작을 만듭니다.
        *   간단한 PD 제어 또는 고정된 관절 각도 시퀀스를 사용할 수 있습니다.
    *   각 시뮬레이션 스텝에서 다음 데이터를 수집합니다:
        *   오버헤드 카메라 이미지 (`renderer.render()`).
        *   로봇의 관절 위치 (`d.qpos`).
        *   현재 로봇의 제어 신호 (`d.ctrl`).
        *   타임스탬프.
    *   수집된 데이터를 `LeRobotDataset`의 `episode_data` 형식에 맞춰 저장합니다.
        `lerobot.common.utils.create_sample_from_env_or_bridge` 함수를 사용할 수도 있습니다.
"""

import mujoco
import numpy as np
import os
import random
import shutil

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
except ImportError:
    print("LeRobot is not installed. Please install it using 'uv pip install lerobot'")
    exit(1)


# MJCF 모델 파일 경로 (cube body가 포함된 커스텀 씬)
MODEL_XML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "SO-ARM100", "Simulation", "SO101", "cop_pickplace_scene.xml"
)

# 데이터셋 저장 경로
DATASET_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "episodes")
DATASET_REPO_ID = "local/cop-pickplace"

# 큐브 설정
CUBE_NAME = "cube"
CUBE_INITIAL_POS = np.array([0.15, 0.0, 0.025])
RANDOM_POS_RANGE = 0.02  # ±20mm

# 시뮬레이션 FPS
SIM_FPS = 30

# 관절 인덱스 (so101_new_calib.xml actuator 순서)
# [shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper]
JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

# Pick-Place 관절 각도 시퀀스 (단위: 라디안)
# 각 포즈: [shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper]
# gripper > 0: 열림, gripper < 0: 닫힘
PICK_PLACE_POSES = {
    "home":         np.array([ 0.0,  0.0,  0.0,  0.0,  0.0,  1.5]),  # 홈 포지션, 그리퍼 열림
    "pre_grasp":    np.array([ 0.0, -1.1,  1.7,  0.4,  0.0,  1.5]),  # 큐브 위 10cm
    "grasp":        np.array([ 0.0, -0.8,  2.0,  0.8,  0.0,  1.5]),  # 큐브 파지 위치
    "close_grip":   np.array([ 0.0, -0.8,  2.0,  0.8,  0.0, -0.8]),  # 그리퍼 닫기
    "lift":         np.array([ 0.0, -1.3,  1.5,  0.3,  0.0, -0.8]),  # 들어올리기
    "transport":    np.array([ 0.8, -1.2,  1.6,  0.3,  0.0, -0.8]),  # 놓을 위치로 이동
    "pre_place":    np.array([ 0.8, -0.8,  1.9,  0.7,  0.0, -0.8]),  # 놓을 위치 위
    "place":        np.array([ 0.8, -0.7,  2.1,  0.9,  0.0, -0.8]),  # 놓기 위치
    "open_grip":    np.array([ 0.8, -0.7,  2.1,  0.9,  0.0,  1.5]),  # 그리퍼 열기
    "retreat":      np.array([ 0.8, -1.1,  1.7,  0.4,  0.0,  1.5]),  # 후퇴
    "return_home":  np.array([ 0.0,  0.0,  0.0,  0.0,  0.0,  1.5]),  # 홈 복귀
}

# 각 페이즈별 스텝 수 (timestep=0.002s, FPS=30이므로 30스텝=0.06s 물리 시간 → 1 데이터 프레임)
PHASE_STEPS = {
    "home":        60,
    "pre_grasp":  120,
    "grasp":       90,
    "close_grip":  60,
    "lift":        90,
    "transport":  120,
    "pre_place":   90,
    "place":       60,
    "open_grip":   60,
    "retreat":     90,
    "return_home": 90,
}
# 물리 스텝 당 데이터 샘플링 비율 (매 N번째 스텝마다 1 프레임 수집)
# timestep=0.002s, FPS=30 → N = round(1/(30*0.002)) = 17
DATA_SAMPLE_EVERY = 17


def interpolate_ctrl(current: np.ndarray, target: np.ndarray, t: float) -> np.ndarray:
    """t=0→current, t=1→target로 선형 보간."""
    return current + (target - current) * min(t, 1.0)


def main():
    # 1. MuJoCo 모델 로드
    if not os.path.exists(MODEL_XML_PATH):
        print(f"Error: MJCF model file not found at {MODEL_XML_PATH}")
        return

    model = mujoco.MjModel.from_xml_path(MODEL_XML_PATH)
    data = mujoco.MjData(model)

    # 2. 오버헤드 카메라 렌더러 설정 (640x480)
    renderer = mujoco.Renderer(model, height=480, width=640)
    camera_name = "overhead_camera"
    camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
    if camera_id == -1:
        print(f"Warning: '{camera_name}' not found. Using default camera (id=-1).")
        camera_id = -1  # MuJoCo default: free camera

    # 3. 큐브 body 및 freejoint qpos 주소 확인
    cube_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, CUBE_NAME)
    if cube_body_id == -1:
        print(f"Error: Cube body '{CUBE_NAME}' not found in MJCF.")
        return

    # freejoint qpos 주소: 큐브의 첫 번째 joint (freejoint)
    cube_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")
    if cube_joint_id == -1:
        print("Error: 'cube_joint' freejoint not found in MJCF.")
        return
    cube_qpos_addr = model.jnt_qposadr[cube_joint_id]  # freejoint: 7 dof (xyz + quat)

    num_joints = model.nu  # 6 (SO-ARM101 actuator 수)

    # 4. LeRobotDataset 초기화
    features = {
        "observation.images.top": {
            "dtype": "video",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "observation.state": {
            "dtype": "float32",
            "shape": (num_joints,),
            "names": JOINT_NAMES,
        },
        "action": {
            "dtype": "float32",
            "shape": (num_joints,),
            "names": JOINT_NAMES,
        },
    }

    dataset_root = os.path.realpath(DATASET_ROOT)
    if os.path.exists(dataset_root):
        shutil.rmtree(dataset_root)  # 기존 데이터셋 제거 후 재생성

    dataset = LeRobotDataset.create(
        repo_id=DATASET_REPO_ID,
        fps=SIM_FPS,
        features=features,
        root=dataset_root,
        robot_type="so101",
        use_videos=True,
        vcodec="h264",
    )

    num_episodes = 50
    phase_sequence = list(PICK_PLACE_POSES.keys())

    for episode_idx in range(num_episodes):
        print(f"Collecting episode {episode_idx + 1}/{num_episodes}...")

        # 5. 에피소드 시작: 시뮬레이션 리셋 + 큐브 초기 위치 랜덤 설정
        mujoco.mj_resetData(model, data)

        random_offset_x = random.uniform(-RANDOM_POS_RANGE, RANDOM_POS_RANGE)
        random_offset_y = random.uniform(-RANDOM_POS_RANGE, RANDOM_POS_RANGE)
        cube_pos = CUBE_INITIAL_POS + np.array([random_offset_x, random_offset_y, 0.0])

        # freejoint qpos 설정: [x, y, z, qw, qx, qy, qz]
        data.qpos[cube_qpos_addr:cube_qpos_addr + 3] = cube_pos
        data.qpos[cube_qpos_addr + 3:cube_qpos_addr + 7] = [1.0, 0.0, 0.0, 0.0]  # identity 쿼터니언

        # 홈 포지션으로 관절 초기화
        data.ctrl[:] = PICK_PLACE_POSES["home"]
        mujoco.mj_forward(model, data)

        # 6. Pick-Place 동작 시퀀스 실행 + 데이터 수집
        current_ctrl = PICK_PLACE_POSES["home"].copy()

        for phase_idx, phase_name in enumerate(phase_sequence):
            target_ctrl = PICK_PLACE_POSES[phase_name]
            num_steps = PHASE_STEPS[phase_name]

            for step in range(num_steps):
                # 선형 보간으로 부드러운 관절 이동
                t = (step + 1) / num_steps
                data.ctrl[:] = interpolate_ctrl(current_ctrl, target_ctrl, t)

                mujoco.mj_step(model, data)

                # DATA_SAMPLE_EVERY 스텝마다 1 프레임 수집
                if step % DATA_SAMPLE_EVERY == 0:
                    renderer.update_scene(data, camera=camera_id)
                    rgb = renderer.render()[::-1, :, :]  # 상하 반전 보정

                    dataset.add_frame({
                        "task": "pick and place red cube",
                        "observation.images.top": rgb,
                        "observation.state": data.qpos[:num_joints].astype(np.float32),
                        "action": data.ctrl[:num_joints].astype(np.float32),
                    })

            current_ctrl = target_ctrl.copy()

        # 7. 에피소드 저장
        dataset.save_episode()
        print(f"  Episode {episode_idx + 1} saved.")

    # 8. 데이터셋 파이널라이즈
    dataset.finalize()
    print(f"\nData collection complete: {num_episodes} episodes saved to {dataset_root}")


if __name__ == "__main__":
    main()
