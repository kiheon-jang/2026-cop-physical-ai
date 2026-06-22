"""콜리전 패드 보정 모델 grasp 검증. 측정 TCP + 반개 straddle 접근 + 부분닫힘 압착.
사용: python _grasp_pads_test.py [FORCE] [APPROACH_GRIP] [GRIP_CLOSE] [GRASP_DZ]
"""
import mujoco, numpy as np, sys
np.seterr(all="ignore")

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CADR = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TABLE_TOP = 0.16

FORCE = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
APPROACH_GRIP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
GRIP_CLOSE = float(sys.argv[3]) if len(sys.argv) > 3 else -0.5
GRASP_DZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
GRIP_OPEN = 1.5
TCP_LOCAL = np.array([0.0071, -0.0002, -0.090])   # 측정값(고정/가동 안쪽면 중점, 30mm 갭자세)
if FORCE > 0:
    for ai in range(6):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]


def ik_tcp(target, seed):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pe = np.ones(3)
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP_LOCAL
        pe = target - tcp
        rot = np.cross(R[:, 2], UP)
        err = np.concatenate([pe, 0.7 * rot])
        if np.linalg.norm(pe) < 5e-4 and np.linalg.norm(rot) < 0.02:
            break
        jp = np.zeros((3, m.nv)); jr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jp, jr, tcp, GBID)
        J = np.vstack([jp[:, DOF], jr[:, DOF]])
        q = q + np.clip(J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err), -0.2, 0.2)
    return q, np.linalg.norm(pe)


def drive(q, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        d.ctrl[:5] = cur + (q - cur) * (s + 1) / n; d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def contacts():
    return sum(1 for c in range(d.ncon)
               if (d.contact[c].geom1 in JAWG and d.contact[c].geom2 in CUBE_GEOM)
               or (d.contact[c].geom2 in JAWG and d.contact[c].geom1 in CUBE_GEOM))


def episode(xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [xy[0], xy[1], TABLE_TOP + 0.015]; d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    qp, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5))
    qg, eg = ik_tcp(np.array([cube[0], cube[1], z0 + GRASP_DZ]), np.zeros(5))
    ql, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5))
    drive(qp, GRIP_OPEN, 150)
    drive(qg, APPROACH_GRIP, 150)
    ca = contacts()
    drive(qg, GRIP_CLOSE, 130)
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE; mujoco.mj_step(m, d)
    cc = contacts(); gq = float(d.qpos[GQA])
    if verbose:
        print(f"    접근접촉={ca} 닫음접촉={cc} grip_q={gq:.3f} cube={d.body('cube').xpos.round(3).tolist()} ik={eg*1000:.1f}mm")
    ml = 0.0; cur = d.ctrl[:5].copy()
    for s in range(400):
        d.ctrl[:5] = cur + (ql - cur) * (s + 1) / 400; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        ml = max(ml, float(d.body("cube").xpos[2]) - z0)
    fin = float(d.body("cube").xpos[2]) - z0
    return ml, fin, cc, gq


print(f"패드모델 grasp: FORCE={FORCE} APPROACH_GRIP={APPROACH_GRIP} GRIP_CLOSE={GRIP_CLOSE} GRASP_DZ={GRASP_DZ}")
POS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
       (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]
res = []; lifts = []
for k, xy in enumerate(POS):
    ml, fin, cc, gq = episode(xy, verbose=(k == 0))
    ok = fin >= 0.04
    res.append(ok); lifts.append(fin * 1000)
    print(f"  cube{xy}: max_lift={ml*1000:5.1f} final={fin*1000:6.1f}mm 접촉={cc} grip_q={gq:+.2f} {'✅' if ok else ''}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%  중앙final={np.median(lifts):.1f}mm")
