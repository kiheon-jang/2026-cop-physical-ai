"""IK 그립 expert 검증 (임시) — jaw 중점(TCP)을 큐브에 맞추는 올바른 IK."""
import mujoco, numpy as np, sys

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene.xml")
d = mujoco.MjData(m)
d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID)]

GRIP_OPEN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
GRIP_CLOSE = float(sys.argv[2]) if len(sys.argv) > 2 else -1.5
APPROACH_Z = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0   # jaw중점을 큐브중심 +이만큼 위에


def jaw_mid(dd):
    return np.mean([dd.geom_xpos[i] for i in JAWG], axis=0)


def ik_jaw(target, seed):
    """jaw 중점→target(위치) + 그리퍼 x_local축을 월드 +z 로 정렬(탑다운).
    위치 3 + 축정렬(x_local→up) 2자유도 = 5제약 / 5DOF. 손가락이 아래를 향하게."""
    q = np.array(seed, float)
    UP = np.array([0.0, 0.0, 1.0])
    err6 = np.zeros(6)
    for _ in range(500):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        mid = jaw_mid(d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        x_local = R[:, 0]
        pos_err = target - mid
        rot_err = np.cross(x_local, UP)          # x_local 을 +z 로 회전시키는 벡터
        err6 = np.concatenate([pos_err, 0.5 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, mid, GBID)
        J = np.vstack([jacp[:, DOF], jacr[:, DOF]])     # 6x5
        dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err6)
        q = q + np.clip(dq, -0.2, 0.2)
    return q, np.linalg.norm(pos_err)


def drive(q_arm, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        t = (s + 1) / n
        d.ctrl[:5] = cur + (q_arm - cur) * t
        d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def episode(cube_xy):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], 0.015]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(50):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    seed = np.zeros(5)
    q_pre, _ = ik_jaw(np.array([cube[0], cube[1], z0 + 0.08]), seed)
    q_grasp, e_grasp = ik_jaw(np.array([cube[0], cube[1], z0 + APPROACH_Z]), q_pre)
    q_lift, _ = ik_jaw(np.array([cube[0], cube[1], z0 + 0.18]), q_grasp)
    drive(q_pre, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_CLOSE, 100)
    maxlift = 0.0; cur = d.ctrl[:5].copy()
    for s in range(250):
        t = (s + 1) / 250
        d.ctrl[:5] = cur + (q_lift - cur) * t
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    # 그립 직전 jaw중점-큐브 거리도 리포트 (도달 검증)
    return maxlift, e_grasp


print(f"GRIP_OPEN={GRIP_OPEN} GRIP_CLOSE={GRIP_CLOSE} APPROACH_Z={APPROACH_Z}")
res = []
for xy in [(0.15, 0.0), (0.15, 0.02), (0.13, -0.02), (0.17, 0.01), (0.14, 0.015)]:
    ml, eg = episode(xy)
    ok = ml >= 0.05
    res.append(ok)
    print(f"  cube{xy}: max_lift={ml*1000:5.1f}mm  ik오차={eg*1000:.1f}mm  {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)}")
