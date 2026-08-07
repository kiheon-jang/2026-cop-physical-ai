"""Phase 3 W2 — S1 리셋버튼 closed-loop expert + LeRobot 수집기 (실기 정렬).

sim_pcb_reset.PcbResetTwin 위에서 검증된 expert 로 성공 시연만 수집한다.
실기 정렬 계약 (soarm_lerobot 와 동일):
  - observation.images.top / observation.images.closeup (640×480@30, video)
  - observation.state / action = 6dof pos
  - task = "press the reset button"
  - 성공 판정 = LED latch (실기 P1 녹색 LED 판정과 동일 계약 — 시뮬은 정답이 공짜)

Expert (2026-08-05 프로토타입 검증, 20-seed 95%):
  - PRESS_LOCAL: jaw 끝 접촉점 (gripper 로컬) — 보드 상면 접촉 실측 캘리브 값.
    TCP(패드 갭 중점)로 누르면 jaw 가 보드에 먼저 닿아 실패한다.
  - pan 정렬 → 버튼 위 60mm 경유 → 단계 하강(+30/+10/+3/-2.5mm, 매 단계 IK 재계산)
    → LED 확인, 실패 시 리트랙 + 버튼 재관측 재시도(최대 3).
  - 남는 실패는 존 구석의 기하학적 도달 불가 배치(팔 링크가 보드를 관통해야 하는
    자세 — 실기 SO-101 도 동일 기하라 못 누른다). 성공만 저장하므로 무해.

환경 수정 금지 원칙: 버튼 치수·스프링·존 크기는 실기 트윈 그대로. 성공률을 위해
환경을 바꾸지 않는다 (사용자 지시 2026-08-05).
"""
import os
import numpy as np
import mujoco

import sim_pcb_reset as twin_mod
from sim_pcb_reset import PcbResetTwin, CAM_W, CAM_H, FPS, TASK_LABEL

try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
except ImportError:
    print("LeRobot is not installed.")
    raise SystemExit(1)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_ROOT = os.path.join(BASE, "data", "episodes_s1")
DATASET_REPO_ID = "local/pcb_reset_sim"

JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
ARM = JOINT_NAMES[:5]

# 물리 timestep 0.002s, 30fps → 매 17 스텝 1프레임 (기존 수집기와 동일)
DATA_SAMPLE_EVERY = 17

# jaw 끝 접촉점 (gripper 로컬) — 보드 상면 접촉 실측 (2026-08-05)
PRESS_LOCAL = np.array([0.0114, -0.0001, -0.1044])
WAYPOINT_Z = 0.060           # 버튼 위 경유 높이
DESCENT_STEPS = (0.030, 0.010, 0.003, -0.0025)  # 단계 하강 (마지막 = 2.5mm 눌러넣기)
MAX_ATTEMPTS_PER_EP = 3


class PressExpert:
    """closed-loop 버튼 누르기 — twin 의 model/data 를 공유, 매 물리 step record 훅."""

    def __init__(self, twin: PcbResetTwin):
        self.t = twin
        m = twin.model
        nid = lambda ty, n: mujoco.mj_name2id(m, ty, n)
        self.DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
        self.QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
        self.GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
        self.BTN_BID = nid(mujoco.mjtObj.mjOBJ_BODY, "reset_button")
        self.d_ik = mujoco.MjData(m)
        self._step_count = 0
        self.record_hook = None

    # --- 물리 step + record ---
    def _phys_step(self):
        self.t.step()
        if self.record_hook is not None:
            if self._step_count % DATA_SAMPLE_EVERY == 0:
                self.record_hook()
            self._step_count += 1

    # --- 운동학 ---
    def ik_point(self, local_pt, target, seed):
        m, d_ik = self.t.model, self.d_ik
        q = np.array(seed, float)
        UP = np.array([0., 0., 1.])
        for _ in range(700):
            for i, a in enumerate(self.QAD):
                d_ik.qpos[a] = q[i]
            mujoco.mj_forward(m, d_ik)
            R = d_ik.xmat[self.GBID].reshape(3, 3)
            pt = d_ik.xpos[self.GBID] + R @ local_pt
            pe = target - pt
            re = np.cross(R[:, 2], UP)
            if np.linalg.norm(pe) < 5e-4 and np.linalg.norm(re) < 0.02:
                break
            jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
            mujoco.mj_jac(m, d_ik, jacp, jacr, pt, self.GBID)
            J = np.vstack([jacp[:, self.DOF], jacr[:, self.DOF]])
            dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), np.concatenate([pe, 0.7 * re]))
            q = q + np.clip(dq, -0.2, 0.2)
        return q

    def step_to(self, q_arm, n):
        d = self.t.data
        cur = d.ctrl[:5].copy()
        for s in range(n):
            tt = (s + 1) / n
            d.ctrl[:5] = cur + (q_arm - cur) * tt
            d.ctrl[5] = 0.0  # jaw 닫힘 유지 — 그리퍼 끝으로 누른다 (실기 S1 방식)
            self._phys_step()

    def _btn_top(self):
        return self.t.data.xpos[self.BTN_BID] + np.array([0, 0, 0.003])

    # --- 에피소드 ---
    def run_episode(self):
        """홈에서 버튼 누르기 1회. 성공(LED latch) 여부와 시도 횟수 반환."""
        d = self.t.data
        bt = self._btn_top()
        # pan 정렬 (홈 자세 유지 — 접힌 팔이 버튼 방위로 회전)
        qpan = np.array(d.ctrl[:5]); qpan[0] = np.arctan2(bt[1], bt[0])
        self.step_to(qpan, 200)
        # 경유 → 단계 하강, 실패 시 리트랙+재관측 재시도
        q = self.ik_point(PRESS_LOCAL, bt + [0, 0, WAYPOINT_Z], [d.qpos[a] for a in self.QAD])
        self.step_to(q, 300)
        for attempt in range(MAX_ATTEMPTS_PER_EP):
            for dz in DESCENT_STEPS:
                q = self.ik_point(PRESS_LOCAL, bt + [0, 0, dz], [d.qpos[a] for a in self.QAD])
                self.step_to(q, 120)
                if self.t.led_on():
                    # 리트랙 (누른 뒤 팔을 들어 top 뷰에서 LED 가 보이는 종단 상태)
                    q = self.ik_point(PRESS_LOCAL, bt + [0, 0, WAYPOINT_Z], [d.qpos[a] for a in self.QAD])
                    self.step_to(q, 150)
                    return True, attempt + 1
            bt = self._btn_top()  # 버튼 재관측 (closed-loop)
            q = self.ik_point(PRESS_LOCAL, bt + [0, 0, 0.050], [d.qpos[a] for a in self.QAD])
            self.step_to(q, 180)
        return self.t.led_on(), MAX_ATTEMPTS_PER_EP


def main(root=None, episodes=100, seed=None):
    root = root or DATASET_ROOT
    twin = PcbResetTwin()
    expert = PressExpert(twin)
    rng = np.random.default_rng(seed)

    # --- DR 수집 (env-gated, 하위호환): COP_COLLECT_DR=1 이면 조명/마찰/카메라 무작위화하며 수집 ---
    # 환경치수 불변 원칙 유지 — 버튼/스프링/존은 안 건드리고 조명/마찰/카메라 노이즈만 흔들고 매 reset 복원.
    # DR rng 는 배치 rng 와 분리 스트림 → 버튼 배치 시퀀스는 nominal 수집과 동일(비교 가능).
    # expert 는 버튼 실좌표 기반이라 시각 DR 이 시연 자체를 오염시키지 않는다(저장 영상 외형만 다양화).
    dr_on = os.environ.get("COP_COLLECT_DR", "") == "1"
    dr_mod = dr_baseline = dr_rng = None
    dr_axes = ()
    dr_noise_std = 0.0
    if dr_on:
        import sim_domain_randomization as dr_mod
        dr_axes = tuple(a.strip() for a in os.environ.get(
            "COP_COLLECT_DR_AXES", "light,friction,camera").split(",") if a.strip())
        dr_baseline = dr_mod.snapshot_baseline(twin.model)
        dr_rng = np.random.default_rng((seed or 0) + 99991)
        print(f"[DR 수집] axes={dr_axes} (환경치수 불변 — 조명/마찰/카메라만 섭동·복원)", flush=True)

    cam_shape = (CAM_H, CAM_W, 3)
    features = {
        "observation.images.top": {"dtype": "video", "shape": cam_shape,
                                   "names": ["height", "width", "channels"]},
        "observation.images.closeup": {"dtype": "video", "shape": cam_shape,
                                       "names": ["height", "width", "channels"]},
        "observation.state": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
        "action": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
    }
    if os.path.exists(root):
        import shutil
        shutil.rmtree(root)
    dataset = LeRobotDataset.create(
        repo_id=DATASET_REPO_ID, fps=FPS, features=features, root=root,
        robot_type="so101", use_videos=True, vcodec="h264",
    )

    frame_buffer = []

    def record():
        d = twin.data
        top = twin.render("top")
        closeup = twin.render("closeup")
        if dr_on:  # 카메라 센서 노이즈 (top+closeup 둘 다, 측정기와 동일 계약)
            top = dr_mod.apply_camera_noise(top, dr_noise_std, dr_rng)
            closeup = dr_mod.apply_camera_noise(closeup, dr_noise_std, dr_rng)
        frame_buffer.append({
            "task": TASK_LABEL,
            "observation.images.top": top,
            "observation.images.closeup": closeup,
            "observation.state": d.qpos[:6].astype(np.float32).copy(),
            "action": d.ctrl[:6].astype(np.float32).copy(),
        })

    expert.record_hook = record

    saved = attempts = 0
    max_attempts = 2 * episodes  # expert 95% 검증 — 캡은 넉넉히
    pcb_placements = []  # 에피소드별 PCB 배치 사이드카 (3D 리플레이가 PCB 를 그 자리에 그린다)
    while saved < episodes and attempts < max_attempts:
        attempts += 1
        frame_buffer.clear()
        placement = twin.reset(rng)
        if dr_on:  # reset 마다 원본복원 후 무작위화 (누적방지, render 측정기와 동일 순서)
            dr_mod.restore_baseline(twin.model, dr_baseline)
            applied = dr_mod.randomize_scene(twin.model, dr_rng, axes=dr_axes)
            mujoco.mj_setConst(twin.model, twin.data)
            dr_noise_std = applied["camera_noise_std"]
        ok, tries = expert.run_episode()
        if ok and frame_buffer:
            for fr in frame_buffer:
                dataset.add_frame(fr)
            dataset.save_episode()
            pcb_placements.append(placement)
            saved += 1
            print(f"[성공 {saved}/{episodes}] 시도#{attempts} frames={len(frame_buffer)} "
                  f"press시도={tries} pcb=({placement['x']:.3f},{placement['y']:.3f},{placement['yaw_deg']:.1f}°)",
                  flush=True)
        else:
            print(f"[실패 폐기] 시도#{attempts} pcb=({placement['x']:.3f},{placement['y']:.3f}) "
                  f"(기하 도달불가 배치 가능성)", flush=True)

    dataset.finalize()
    if pcb_placements:
        import json
        sidecar = os.path.join(root, "meta", "pcb_traj.json")
        with open(sidecar, "w") as f:
            json.dump({"format": "per-episode PCB placement {x, y, yaw_deg} (worldbody pcb body)",
                       "episodes": pcb_placements}, f)
        print(f"[사이드카] PCB 배치 {len(pcb_placements)}ep → {sidecar}")
    yld = saved / attempts * 100 if attempts else 0
    print(f"\n수집 완료: {saved}/{episodes} (시도 {attempts}, yield {yld:.0f}%) → {root}")
    return 0 if saved >= episodes else 1


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="S1 리셋버튼 closed-loop 시연 수집 (LeRobot v3, 실기 정렬)")
    p.add_argument("--root", default=None)
    p.add_argument("--episodes", type=int, default=100)
    p.add_argument("--seed", type=int, default=None)
    a = p.parse_args()
    raise SystemExit(main(root=a.root, episodes=a.episodes, seed=a.seed))
