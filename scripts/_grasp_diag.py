"""단일 grasp 에피소드 진단 — 물리상 실제 jaw 위치/개폐/접촉을 단계별로 본다."""
import mujoco, numpy as np, sys

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
FORCE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
if FORCE > 0:
    for ai in range(5):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]
    print(f"[forcerange override = ±{FORCE} Nm — 토크 변수 제거]")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GRIPJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper"); GQAD = m.jnt_qposadr[GRIPJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
CUBEG = nid(mujoco.mjtObj.mjOBJ_GEOM, None) if False else None
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID)]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
GRIP_OPEN, GRIP_CLOSE = 1.5, -1.5


def jaw_mid(dd):
    return np.mean([dd.geom_xpos[i] for i in JAWG], axis=0)


def jaw_geom_list(dd):
    # 손가락 지오메트리(콜리전)만 보고 싶을 때 위치 나열
    return {m.geom(i).name or f"g{i}": dd.geom_xpos[i].round(3).tolist() for i in JAWG}


def ik_jaw(target, seed):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pos_err = np.ones(3)
    for _ in range(500):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        mid = jaw_mid(d_ik); R = d_ik.xmat[GBID].reshape(3, 3); x_local = R[:, 0]
        pos_err = target - mid; rot_err = np.cross(x_local, UP)
        err6 = np.concatenate([pos_err, 0.5 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, mid, GBID)
        J = np.vstack([jacp[:, DOF], jacr[:, DOF]])
        dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err6)
        q = q + np.clip(dq, -0.2, 0.2)
    return q


def drive(q_arm, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        t = (s + 1) / n
        d.ctrl[:5] = cur + (q_arm - cur) * t; d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def contacts_jaw_cube():
    out = []
    for c in range(d.ncon):
        con = d.contact[c]
        g1, g2 = con.geom1, con.geom2
        if (g1 in JAWG and g2 in CUBE_GEOM) or (g2 in JAWG and g1 in CUBE_GEOM):
            f = np.zeros(6); mujoco.mj_contactForce(m, d, c, f)
            out.append((m.geom(g1).name or g1, m.geom(g2).name or g2, round(float(np.linalg.norm(f[:3])), 3)))
    return out


def report(tag, target=None):
    jm = jaw_mid(d); cube = d.body("cube").xpos.copy()
    line = f"[{tag}] jaw_mid={jm.round(3).tolist()} cube={cube.round(3).tolist()} grip_q={float(d.qpos[GQAD]):.3f}"
    if target is not None:
        line += f" | jaw-target오차={np.linalg.norm(jm-target)*1000:.1f}mm"
    line += f" | jaw-cube수평={np.linalg.norm(jm[:2]-cube[:2])*1000:.1f}mm z차={1000*(jm[2]-cube[2]):.1f}mm"
    print(line)


mujoco.mj_resetData(m, d)
d.qpos[CADR:CADR + 3] = [0.13, 0.0, 0.175]; d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
mujoco.mj_forward(m, d)
for _ in range(100):
    mujoco.mj_step(m, d)
cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
print(f"큐브 안정화: {cube.round(4).tolist()}  (작업대윗면 0.16, 큐브중심 기대 0.175)")
print("JAW 콜리전 지오메트리:")
for i in JAWG:
    g = m.geom(i)
    print(f"  geom {i} name={g.name!r} body={m.body(m.geom_bodyid[i]).name!r} group={g.group} type={g.type}")
print("CUBE 지오메트리:", [(i, m.geom(i).name) for i in CUBE_GEOM])

q_pre = ik_jaw(np.array([cube[0], cube[1], z0 + 0.08]), np.zeros(5))
q_grasp = ik_jaw(np.array([cube[0], cube[1], z0]), np.zeros(5))
q_lift = ik_jaw(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5))
tgt = np.array([cube[0], cube[1], z0])
print("q_grasp 명령(rad):", q_grasp.round(3).tolist())

drive(q_pre, GRIP_OPEN, 150); report("pre(open)", np.array([cube[0], cube[1], z0 + 0.08]))
drive(q_grasp, GRIP_OPEN, 150); report("grasp위치(open)", tgt)
q_ach = np.array([d.qpos[a] for a in QAD])
print("  q_grasp 달성(rad):", q_ach.round(3).tolist())
print("  관절오차(rad):    ", (q_grasp - q_ach).round(3).tolist(), "  ← 큰값=토크부족")
drive(q_grasp, GRIP_CLOSE, 100); report("닫음", tgt)
print("  닫음 후 jaw↔cube 접촉:", contacts_jaw_cube())
cur = d.ctrl[:5].copy()
for s in range(250):
    t = (s + 1) / 250
    d.ctrl[:5] = cur + (q_lift - cur) * t; d.ctrl[5] = GRIP_CLOSE
    mujoco.mj_step(m, d)
report("들기후")
print("  들기중 jaw↔cube 접촉:", contacts_jaw_cube())
print(f"최종 lift = {1000*(float(d.body('cube').xpos[2])-z0):.1f}mm")
