"""가설 검증: 좁은 받침(peg)이면 손가락 끝이 받침 옆을 지나 큐브에 닿아 핀치되는가.
scene_grasp_peg.xml(24mm peg) + 검증된 v2 IK(TCP+body z→up). 하강 깊이(TCP_Z, GRASP_DZ) 스윕.
"""
import mujoco, numpy as np, itertools

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_peg.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CADR = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
GQAD = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
GRIP_OPEN, GRIP_CLOSE = 1.5, -1.5
for ai in range(5):
    m.actuator_forcerange[ai] = [-6.0, 6.0]   # 메커니즘 격리


def ik_tcp(target, seed, tcp_z):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pe = np.ones(3)
    TCP = np.array([0.0, 0.0, tcp_z])
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP
        pe = target - tcp
        rot = np.cross(R[:, 2], UP)
        err = np.concatenate([pe, 0.7 * rot])
        if np.linalg.norm(pe) < 5e-4 and np.linalg.norm(rot) < 0.02:
            break
        jp = np.zeros((3, m.nv)); jr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jp, jr, tcp, GBID)
        J = np.vstack([jp[:, DOF], jr[:, DOF]])
        q = q + np.clip(J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err), -0.2, 0.2)
    return q


def drive(q, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        d.ctrl[:5] = cur + (q - cur) * (s + 1) / n; d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def contacts():
    return sum(1 for c in range(d.ncon)
               if (d.contact[c].geom1 in JAWG and d.contact[c].geom2 in CUBE_GEOM)
               or (d.contact[c].geom2 in JAWG and d.contact[c].geom1 in CUBE_GEOM))


def episode(tcp_z, grasp_dz):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [0.13, 0.0, 0.175]; d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    qp = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5), tcp_z)
    qg = ik_tcp(np.array([cube[0], cube[1], z0 + grasp_dz]), np.zeros(5), tcp_z)
    ql = ik_tcp(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5), tcp_z)
    drive(qp, GRIP_OPEN, 150); drive(qg, GRIP_OPEN, 150)
    c_app = contacts()
    drive(qg, GRIP_CLOSE, 150)
    c_close = contacts(); gq = float(d.qpos[GQAD])
    ml = 0.0; cur = d.ctrl[:5].copy()
    for s in range(300):
        d.ctrl[:5] = cur + (ql - cur) * (s + 1) / 300; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        ml = max(ml, float(d.body("cube").xpos[2]) - z0)
    final = float(d.body("cube").xpos[2]) - z0
    return ml, final, c_app, c_close, gq


print("peg(24mm) 씬, 큐브(0.13,0), ±6Nm. TCP_Z×GRASP_DZ 스윕")
print(f"{'TCP_Z':>7}{'GRASP_DZ':>9}{'접근접촉':>8}{'닫음접촉':>8}{'grip_q':>8}{'max_lift':>9}{'final':>8}  판정")
best = None
for tcp_z, gdz in itertools.product([-0.085, -0.075, -0.065], [0.02, 0.0, -0.02, -0.04, -0.06]):
    ml, fin, ca, cc, gq = episode(tcp_z, gdz)
    ok = fin >= 0.04
    if best is None or fin > best[0]:
        best = (fin, tcp_z, gdz)
    print(f"{tcp_z:>7.3f}{gdz:>9.3f}{ca:>8}{cc:>8}{gq:>8.2f}{ml*1000:>8.1f}m{fin*1000:>7.1f}m  {'✅성공' if ok else ''}")
print(f"\nbest final_lift={best[0]*1000:.1f}mm @ TCP_Z={best[1]} GRASP_DZ={best[2]}")
