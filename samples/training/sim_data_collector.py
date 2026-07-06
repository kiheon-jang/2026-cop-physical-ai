"""
CoP Physical AI 프로젝트 - 자동 데이터 수집 스크립트 (closed-loop grasp expert)

이 스크립트는 MuJoCo 시뮬레이터에서 SO-ARM101(SO101) 로봇팔의 *검증된 closed-loop grasp 정책*을
실행해, 성공한 grasp+lift 시연만 LeRobot 포맷으로 자동 수집한다. 무인 크론 실행용(headless).

핵심 설계(이전 open-loop 수집기와의 차이):
- expert 교체: 망가진 open-loop 고정각 PICK_PLACE_POSES 시퀀스를 제거하고,
  scripts/_grasp_closedloop.py 의 검증된 closed-loop 정책(ik_tcp / graded_close /
  closed_loop_lift / attempt)을 이 파일로 이식해 재사용한다. 매 물리 step 큐브 ground-truth
  xpos 를 추종(visual servoing)한다.
- 씬 교체: scene.xml → scene_grasp_pads.xml (평평 패드 모델 so101_grasp_calib.xml).
  풀메시 그리퍼는 닫는 순간 큐브를 쳐냈고, 평패드 씬만 면 접촉 patch 가 생겨 잡힌다.
  overhead_camera 는 so101_grasp_calib.xml(world 레벨)에 정의돼 있다.
- 성공 필터(핵심): 각 에피소드 프레임을 로컬 버퍼에 쌓고, grasp+lift 후
  성공(cube_z 상승 ≥ 40mm)일 때만 dataset.add_frame + save_episode 로 flush 한다.
  실패면 버퍼 폐기. → "성공 시연만" 학습데이터가 된다(이전 수집기는 실패도 저장하는 버그).

forcerange = 3.0 (팔 5관절):
  BOM(docs/02_hardware/BOM.md)상 Follower 서보 = 12V STS3215-C018 (≈2.94Nm 스톨).
  시뮬 XML 기본 1.5Nm 는 12V 실하드웨어보다 낮다 → 3.0 이 faithful.
  closed-loop 정책은 FORCE=3 에서 75% 성공(FORCE=6 은 과스펙이라 안 씀).
  코드에서 m.actuator_forcerange[0:5] = [-3, 3].

큐브 크기 = 30mm:
  scene_grasp_pads.xml 기본 size 0.015(=30mm 한 변) 그대로 사용한다.
  50mm 큐브는 그리퍼 개구폭/CLOSE_Q/패드 갭 별도 보정이 필요하므로 본 수집기에서는 미적용.

큐브 위치 = base (0.13, 0) 에서 x,y ±20mm 랜덤(검증된 가용영역).
  z = TABLE_TOP(0.16) + HALF(0.015) = 0.175.

수정 금지: scene_grasp_pads.xml, so101_grasp_calib.xml, scripts/_grasp_*.py.
오직 이 파일만 재작성.
"""

import mujoco
import numpy as np
import os
import random
import time

import sim_domain_randomization as dr  # 같은 폴더 (samples/training)

np.seterr(all="ignore")

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
except ImportError:
    print("LeRobot is not installed. Please install it using 'uv pip install lerobot'")
    exit(1)


# ---------------------------------------------------------------------------
# 경로 / 상수
# ---------------------------------------------------------------------------
MODEL_XML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..",
    "SO-ARM100", "Simulation", "SO101", "scene_grasp_pads.xml",
)
DATASET_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "episodes")
DATASET_REPO_ID = "local/cop-pickplace"

SIM_FPS = 30
JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

# 물리 스텝 당 데이터 샘플링 비율 (timestep=0.002s, FPS=30 → 매 17번째 스텝 1프레임)
DATA_SAMPLE_EVERY = 17

# closed-loop 정책 파라미터 (검증된 값, _grasp_closedloop.py 기본값과 동일)
FORCE = 3.0           # 팔 5관절 forcerange(±Nm). BOM 12V STS3215-C018 faithful 값.
CLOSE_Q = 0.13        # firm grip 목표 gripper qpos (30mm 큐브 점진 닫힘 종료점)
LIFT_X = 0.09         # 들 때 큐브를 당겨갈 x(베이스쪽)
RETRY = 3             # firm grasp 재시도 최대 횟수
SUCCESS_LIFT = 0.04   # 성공 판정: cube_z 상승 ≥ 40mm

# 큐브 위치 랜덤화
CUBE_BASE_XY = np.array([0.13, 0.0])
RANDOM_POS_RANGE = 0.02  # ±20mm

TCP_LOCAL = np.array([0.0071, -0.0002, -0.090])  # 검증된 패드 갭 중점
TABLE_TOP = 0.16
GRIP_OPEN = 1.5
APPROACH_GRIP = 0.45

ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


# ---------------------------------------------------------------------------
# Expert(closed-loop) — 모델/데이터/주소는 build_policy()에서 묶어 GraspExpert 로 보유.
# _grasp_closedloop.py 의 모듈전역을 클래스 멤버로 옮긴 것 외 로직은 동일하게 이식.
# 매 물리 step record_hook() 으로 프레임 버퍼링 훅을 호출한다.
# ---------------------------------------------------------------------------
class GraspExpert:
    def __init__(self, model_path):
        self.m = mujoco.MjModel.from_xml_path(model_path)
        self.d = mujoco.MjData(self.m)
        self.d_ik = mujoco.MjData(self.m)
        m = self.m

        nid = lambda t, n: mujoco.mj_name2id(m, t, n)
        self.DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
        self.QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
        CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")
        self.CADR = m.jnt_qposadr[CJ]
        self.CUBE_BID = nid(mujoco.mjtObj.mjOBJ_BODY, "cube")
        self.GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
        self.GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
        self.FIXED_PAD = nid(mujoco.mjtObj.mjOBJ_GEOM, "fixed_pad")
        self.MOVING_PAD = nid(mujoco.mjtObj.mjOBJ_GEOM, "moving_pad")
        self.CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == self.CUBE_BID][0]

        # 큐브 30mm: scene 기본 size 0.015 그대로. (코드에서 명시적으로 재설정)
        self.HALF = 0.015
        m.geom_size[self.CUBE_GEOM] = [self.HALF, self.HALF, self.HALF]
        m.body_mass[self.CUBE_BID] = 0.05
        mujoco.mj_setConst(m, self.d)

        # forcerange = 3.0 (팔 5관절). 사유는 헤더 주석 참조.
        for ai in range(5):
            m.actuator_forcerange[ai] = [-FORCE, FORCE]

        # record 훅: 물리 step 카운터 + 콜백(없으면 no-op)
        self._step_count = 0
        self.record_hook = None

    # --- 물리 step + record 훅 ---
    def _phys_step(self):
        mujoco.mj_step(self.m, self.d)
        if self.record_hook is not None:
            if self._step_count % DATA_SAMPLE_EVERY == 0:
                self.record_hook()
            self._step_count += 1

    # --- 운동학 ---
    def tcp_pos(self, dd):
        return dd.xpos[self.GBID] + dd.xmat[self.GBID].reshape(3, 3) @ TCP_LOCAL

    def ik_tcp(self, target, seed):
        m, d_ik = self.m, self.d_ik
        q = np.array(seed, float)
        UP = np.array([0., 0., 1.])
        pos_err = np.ones(3)
        for _ in range(700):
            for i, a in enumerate(self.QAD):
                d_ik.qpos[a] = q[i]
            d_ik.ctrl[5] = GRIP_OPEN
            mujoco.mj_forward(m, d_ik)
            R = d_ik.xmat[self.GBID].reshape(3, 3)
            tcp = d_ik.xpos[self.GBID] + R @ TCP_LOCAL
            pos_err = target - tcp
            rot_err = np.cross(R[:, 2], UP)
            err6 = np.concatenate([pos_err, 0.7 * rot_err])
            if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
                break
            jacp = np.zeros((3, m.nv))
            jacr = np.zeros((3, m.nv))
            mujoco.mj_jac(m, d_ik, jacp, jacr, tcp, self.GBID)
            J = np.vstack([jacp[:, self.DOF], jacr[:, self.DOF]])
            dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err6)
            q = q + np.clip(dq, -0.2, 0.2)
        return q, np.linalg.norm(pos_err)

    def step_to(self, q_arm, grip, n):
        d = self.d
        cur = d.ctrl[:5].copy()
        for s in range(n):
            t = (s + 1) / n
            d.ctrl[:5] = cur + (q_arm - cur) * t
            d.ctrl[5] = grip
            self._phys_step()

    def pad_contacts(self):
        d = self.d
        nf = nm = 0
        for c in range(d.ncon):
            g1, g2 = d.contact[c].geom1, d.contact[c].geom2
            if self.CUBE_GEOM not in (g1, g2):
                continue
            other = g1 if g2 == self.CUBE_GEOM else g2
            if other == self.FIXED_PAD:
                nf += 1
            elif other == self.MOVING_PAD:
                nm += 1
        return nf, nm

    def graded_close(self, z_grasp):
        """점진 닫힘: APPROACH_GRIP→CLOSE_Q 를 여러 step 에 나눠 닫으며 매 step 큐브 추종."""
        d = self.d
        seed = d.ctrl[:5].copy()
        n_micro = 50
        g0 = float(d.qpos[self.GQA])
        for k in range(n_micro):
            t = (k + 1) / n_micro
            grip = g0 + (CLOSE_Q - g0) * t
            cube = d.body("cube").xpos.copy()
            target = np.array([cube[0], cube[1], z_grasp])
            q_arm, _ = self.ik_tcp(target, seed)
            seed = q_arm
            cur = d.ctrl[:5].copy()
            for s in range(5):
                d.ctrl[:5] = cur + (q_arm - cur) * (s + 1) / 5
                d.ctrl[5] = grip
                self._phys_step()
        for _ in range(80):
            d.ctrl[5] = CLOSE_Q
            self._phys_step()
        nf, nm = self.pad_contacts()
        return nf > 0 and nm > 0

    def closed_loop_lift(self, z0):
        """closed-loop 들기: 큐브를 위+베이스쪽(LIFT_X)으로 당기는 곡선 경로. 매 step 큐브추종."""
        d = self.d
        n = 550
        seed = d.ctrl[:5].copy()
        maxlift = 0.0
        cube0_xy = d.body("cube").xpos[:2].copy()
        for s in range(n):
            t = min(1.0, (s + 1) / 420)
            cube = d.body("cube").xpos.copy()
            tx = cube0_xy[0] + (LIFT_X - cube0_xy[0]) * t
            tz = z0 + 0.065 * t
            target = np.array([tx, cube[1], tz])
            q_arm, _ = self.ik_tcp(target, seed)
            seed = q_arm
            cur = d.ctrl[:5].copy()
            d.ctrl[:5] = cur + (q_arm - cur) * 0.5
            d.ctrl[5] = CLOSE_Q
            self._phys_step()
            maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
        return maxlift

    def reopen(self, z0):
        d = self.d
        cube = d.body("cube").xpos.copy()
        q_up, _ = self.ik_tcp(np.array([cube[0], cube[1], z0 + 0.06]), d.ctrl[:5].copy())
        self.step_to(q_up, GRIP_OPEN, 100)

    def attempt(self, z0):
        d = self.d
        cube = d.body("cube").xpos.copy()
        q_pre, _ = self.ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), d.ctrl[:5].copy())
        self.step_to(q_pre, GRIP_OPEN, 120)
        cube = d.body("cube").xpos.copy()
        q_grasp, _ = self.ik_tcp(np.array([cube[0], cube[1], z0]), q_pre)
        self.step_to(q_grasp, APPROACH_GRIP, 130)
        return self.graded_close(z0)

    def reset_with_cube(self, cube_xy):
        """리셋 + 큐브 배치 + 안정화. 안정화된 z0 반환. (안정화 step 은 기록 안 함)"""
        m, d = self.m, self.d
        mujoco.mj_resetData(m, d)
        d.qpos[self.CADR:self.CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + self.HALF]
        d.qpos[self.CADR + 3:self.CADR + 7] = [1, 0, 0, 0]
        d.ctrl[:5] = 0
        d.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d)
        for _ in range(100):
            mujoco.mj_step(m, d)  # 훅 없이: 큐브 낙하 안정화는 시연이 아님
        self._step_count = 0
        return float(d.body("cube").xpos[2])

    def run_episode(self, cube_xy):
        """reset → 안정화 → attempt(재시도) → closed_loop_lift. (maxlift, tries) 반환.
        record_hook 이 설정돼 있으면 attempt/lift 의 매 DATA_SAMPLE_EVERY step 기록."""
        z0 = self.reset_with_cube(cube_xy)
        tries = 0
        firm = False
        for r in range(RETRY + 1):
            tries = r + 1
            firm = self.attempt(z0)
            if firm:
                break
            self.reopen(z0)
        maxlift = self.closed_loop_lift(z0)
        return maxlift, tries

    def cube_z(self):
        return float(self.d.body("cube").xpos[2])


# ---------------------------------------------------------------------------
# 수집 루프
# ---------------------------------------------------------------------------
def main(dataset_root_arg=None, num_episodes_arg=None, use_dr=False, dr_seed=0, seed=None):
    if seed is not None:
        random.seed(seed)  # 큐브 배치 재현성 (미지정 시 기존 비결정 동작 유지)
    if not os.path.exists(MODEL_XML_PATH):
        print(f"Error: MJCF model file not found at {MODEL_XML_PATH}")
        return

    expert = GraspExpert(MODEL_XML_PATH)
    model, data = expert.m, expert.d
    num_joints = model.nu  # 6

    # Domain Randomization (opt-in). 매 에피소드 reset 마다 조명/마찰 무작위화 + 카메라 노이즈.
    # baseline 을 캐시해 friction 곱셈/light_pos 덧셈 누적을 방지한다.
    dr_baseline = dr.snapshot_baseline(model) if use_dr else None
    dr_rng = np.random.default_rng(dr_seed) if use_dr else None
    dr_state = {"noise_std": 0.0}  # record() 가 참조할 현재 카메라 노이즈 std

    # overhead_camera (so101_grasp_calib.xml world 레벨)
    renderer = mujoco.Renderer(model, height=480, width=640)
    camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "overhead_camera")
    if camera_id == -1:
        print("Warning: 'overhead_camera' not found. Using default camera (id=-1).")
        camera_id = -1

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

    dataset_root = os.path.realpath(dataset_root_arg or DATASET_ROOT)
    if os.path.exists(dataset_root):
        # 삭제 대신 타임스탬프 백업으로 대피 — 드라이버 오판/크래시 재시작이 운영 데이터를 파괴하지 않게
        bak = f"{dataset_root}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        os.rename(dataset_root, bak)
        print(f"[백업] 기존 데이터셋 대피: {bak}")

    dataset = LeRobotDataset.create(
        repo_id=DATASET_REPO_ID,
        fps=SIM_FPS,
        features=features,
        root=dataset_root,
        robot_type="so101",
        use_videos=True,
        vcodec="h264",
    )

    target_episodes = num_episodes_arg if num_episodes_arg is not None else 50
    max_attempts = 4 * target_episodes  # 무한루프 방지 캡

    # 에피소드 프레임 버퍼 (성공 시에만 flush)
    frame_buffer = []

    def record():
        """현재 시뮬 상태 1프레임을 버퍼에 적재 (overhead RGB + qpos[:6] + ctrl[:6])."""
        renderer.update_scene(data, camera=camera_id)
        rgb = renderer.render()[::-1, :, :]  # 상하 반전 보정
        if use_dr:
            rgb = dr.apply_camera_noise(rgb, dr_state["noise_std"], dr_rng)
        frame_buffer.append({
            "task": "pick up red cube",
            "observation.images.top": rgb,
            "observation.state": data.qpos[:num_joints].astype(np.float32).copy(),
            "action": data.ctrl[:num_joints].astype(np.float32).copy(),
        })

    expert.record_hook = record

    saved = 0
    attempts = 0
    while saved < target_episodes and attempts < max_attempts:
        attempts += 1
        frame_buffer.clear()

        if use_dr:
            # 매 에피소드 원본 복원 후 무작위화 (누적 방지). 카메라 노이즈 std 는 record() 에 전달.
            dr.restore_baseline(model, dr_baseline)
            applied = dr.randomize_scene(model, dr_rng)
            mujoco.mj_setConst(model, data)  # 마찰 변경을 상수 캐시에 반영
            dr_state["noise_std"] = applied["camera_noise_std"]
            print(f"[DR] {applied}")

        off = np.array([random.uniform(-RANDOM_POS_RANGE, RANDOM_POS_RANGE),
                        random.uniform(-RANDOM_POS_RANGE, RANDOM_POS_RANGE)])
        cube_xy = CUBE_BASE_XY + off

        maxlift, tries = expert.run_episode(cube_xy)
        success = maxlift >= SUCCESS_LIFT

        if success and len(frame_buffer) > 0:
            for fr in frame_buffer:
                dataset.add_frame(fr)
            dataset.save_episode()
            saved += 1
            print(f"[성공 {saved}/{target_episodes}] 시도 #{attempts} "
                  f"lift={maxlift * 1000:5.1f}mm frames={len(frame_buffer)} grasp재시도={tries} "
                  f"cube=({cube_xy[0]:.3f},{cube_xy[1]:.3f})")
        else:
            print(f"[실패 폐기] 시도 #{attempts} lift={maxlift * 1000:5.1f}mm "
                  f"frames={len(frame_buffer)}(폐기) grasp재시도={tries} "
                  f"cube=({cube_xy[0]:.3f},{cube_xy[1]:.3f})")

    dataset.finalize()
    yld = (saved / attempts * 100) if attempts else 0.0
    print(f"\n수집 완료: 성공 {saved}/{target_episodes}  (시도 {attempts}회, yield {yld:.0f}%)  "
          f"→ {dataset_root}")
    if saved < target_episodes:
        print(f"경고: 목표({target_episodes}) 미달 — max_attempts({max_attempts}) 캡 도달.")


if __name__ == "__main__":
    import argparse
    _p = argparse.ArgumentParser(
        description="시뮬 closed-loop grasp 성공 시연 자동 수집 (LeRobot 포맷)")
    _p.add_argument("--root", type=str, default=None,
                    help="데이터셋 저장 루트 (기본: data/episodes). 대상 루트만 삭제 후 재생성.")
    _p.add_argument("--episodes", type=int, default=None,
                    help="목표 '성공' 에피소드 수 (기본: 50). 성공할 때까지 시도(max=4×목표 캡).")
    _p.add_argument("--dr", action="store_true",
                    help="Domain Randomization 적용(조명/마찰/카메라노이즈). 기본 off — 드라이버 파이프라인 불변.")
    _p.add_argument("--dr-seed", type=int, default=0, help="DR 무작위 시드")
    _p.add_argument("--seed", type=int, default=None,
                    help="큐브 배치 랜덤 시드 (재현성. 기본: 비결정)")
    _a = _p.parse_args()
    main(dataset_root_arg=_a.root, num_episodes_arg=_a.episodes,
         use_dr=_a.dr, dr_seed=_a.dr_seed, seed=_a.seed)
