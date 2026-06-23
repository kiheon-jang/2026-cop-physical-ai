"""접촉모델 보정 grasp 검증 — 실물이 3~5cm를 잡으니 sim도 그래야 한다는 전제.
가설: 기본 condim=3(접선마찰만)이라 큐브가 그립축으로 비틀려 빠짐. condim=4/6(비틀림·구름
마찰) + 마찰↑ 로 실물처럼 잡히게. 패드 모델 기반.
사용: python _grasp_contact_tune.py [CONDIM] [FT] [FTOR] [HALF] [APPROACH_GRIP] [GRIP_CLOSE]
"""
import mujoco, numpy as np, sys
np.seterr(all="ignore")

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")
nid = lambda t, n: mujoco.mj_name2id(m, t, n)

CONDIM = int(sys.argv[1]) if len(sys.argv) > 1 else 4
FT = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0      # 접선 마찰
FTOR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.1    # 비틀림 마찰
HALF = float(sys.argv[4]) if len(sys.argv) > 4 else 0.015  # 큐브 반폭(기본 30mm)
APPROACH_GRIP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.4
GRIP_CLOSE = float(sys.argv[6]) if len(sys.argv) > 6 else -0.6
FROLL = 0.01
GRIP_OPEN = 1.5
TCP_LOCAL = np.array([0.0071, -0.0002, -0.090])  # 30mm 갭 측정 중점
TABLE_TOP = 0.16

CUBE_BID = nid(mujoco.mjtObj.mjOBJ_BODY, "cube")
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == CUBE_BID][0]
PADS = [nid(mujoco.mjtObj.mjOBJ_GEOM, "fixed_pad"), nid(mujoco.mjtObj.mjOBJ_GEOM, "moving_pad")]
# 큐브 크기/질량
m.geom_size[CUBE_GEOM] = [HALF, HALF, HALF]
m.body_mass[CUBE_BID] = 0.05 * (HALF / 0.015) ** 3
# 접촉모델 보정: 패드 + 큐브
for g in PADS + [CUBE_GEOM]:
    m.geom_condim[g] = CONDIM
    m.geom_friction[g] = [FT, FTOR, FROLL]

d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CADR = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
for ai in range(6):
    m.actuator_forcerange[ai] = [-6.0, 6.0]  # 메커니즘 격리(토크는 변수 아님 확인됨)


def ik_tcp(target, seed):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pe = np.ones(3)
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP_LOCAL
        pe = target - tcp; rot = np.cross(R[:, 2], UP)
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
               if (d.contact[c].geom1 in JAWG and d.contact[c].geom2 == CUBE_GEOM)
               or (d.contact[c].geom2 in JAWG and d.contact[c].geom1 == CUBE_GEOM))


def episode(xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [xy[0], xy[1], TABLE_TOP + HALF]; d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    c = d.body("cube").xpos.copy(); z0 = float(c[2]); xy0 = c[:2].copy()
    qp = ik_tcp(np.array([c[0], c[1], z0 + 0.07]), np.zeros(5))
    qg = ik_tcp(np.array([c[0], c[1], z0]), np.zeros(5))
    ql = ik_tcp(np.array([c[0], c[1], z0 + 0.10]), np.zeros(5))
    drive(qp, GRIP_OPEN, 150)
    drive(qg, APPROACH_GRIP, 150)
    ca = contacts(); drift_app = np.linalg.norm(d.body("cube").xpos[:2] - xy0)
    drive(qg, GRIP_CLOSE, 130)
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE; mujoco.mj_step(m, d)
    cc = contacts(); gq = float(d.qpos[GQA]); drift_cl = np.linalg.norm(d.body("cube").xpos[:2] - xy0)
    ml = 0.0; cur = d.ctrl[:5].copy()
    for s in range(400):
        d.ctrl[:5] = cur + (ql - cur) * (s + 1) / 400; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        ml = max(ml, float(d.body("cube").xpos[2]) - z0)
    fin = float(d.body("cube").xpos[2]) - z0
    if verbose:
        print(f"    접근:접촉{ca} 큐브밀림{drift_app*1000:.0f}mm | 닫음:접촉{cc} grip_q{gq:.2f} 밀림{drift_cl*1000:.0f}mm | max_lift{ml*1000:.0f} final{fin*1000:.0f}mm")
    return fin, cc


print(f"접촉튜닝: condim={CONDIM} 마찰=[{FT},{FTOR},{FROLL}] 큐브={HALF*2000:.0f}mm approach={APPROACH_GRIP} close={GRIP_CLOSE}")
POS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
       (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]
res = []
for k, xy in enumerate(POS):
    fin, cc = episode(xy, verbose=(k < 2))
    ok = fin >= 0.04
    res.append(ok)
print(f"  성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%")
