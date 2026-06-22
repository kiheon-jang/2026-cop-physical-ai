"""작은/가는 물체 자유 grasp 검증 (wire 태스크 근접 proxy).
큐브 크기를 코드로 줄이고(geom_size/mass override), 물체를 고정 패드 쪽에 두어
가동조 호 스윕을 최소화한다. "자유 물체 grasp가 정말 불가한가"를 실측으로 답한다.
사용: python _grasp_small_test.py [HALF_M] [FORCE] [APPROACH_GRIP] [GRIP_CLOSE]
"""
import mujoco, numpy as np, sys
np.seterr(all="ignore")

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
CUBE_BID = nid(mujoco.mjtObj.mjOBJ_BODY, "cube")
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == CUBE_BID]

# 3차원: HX=집는방향(개폐축 x) 반폭, HY=손가락폭방향 반폭, HZ=높이 반폭
HX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.006   # 집는 방향(핀치) 반폭
FORCE = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
APPROACH_GRIP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
GRIP_CLOSE = float(sys.argv[4]) if len(sys.argv) > 4 else -1.1
HY = float(sys.argv[5]) if len(sys.argv) > 5 else HX       # 폭(손가락 길이방향)
HZ = float(sys.argv[6]) if len(sys.argv) > 6 else HX       # 높이
GRIP_OPEN = 1.5
# 커넥터 모델 + 질량(밀도 보존). 코드부분 예: HX=집는깊이, HY=0.015(폭30mm), HZ=0.005(높이10mm)
m.geom_size[CUBE_GEOM[0]] = [HX, HY, HZ]
m.body_mass[CUBE_BID] = 0.05 * (HX * HY * HZ) / (0.015 ** 3)
# TCP: 물체를 고정 패드(안쪽면 x=-0.0079)에 붙임 → 물체중심 x=-0.0079+HX. 스윕 최소화.
TCP_LOCAL = np.array([-0.0079 + HX, -0.0002, -0.090])
TABLE_TOP = 0.16

d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CADR = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
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
        pe = target - tcp; rot = np.cross(R[:, 2], UP)
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
               if (d.contact[c].geom1 in JAWG and d.contact[c].geom2 == CUBE_GEOM[0])
               or (d.contact[c].geom2 in JAWG and d.contact[c].geom1 == CUBE_GEOM[0]))


def episode(xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [xy[0], xy[1], TABLE_TOP + HZ]; d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    c = d.body("cube").xpos.copy(); z0 = float(c[2])
    qp, _ = ik_tcp(np.array([c[0], c[1], z0 + 0.07]), np.zeros(5))
    qg, eg = ik_tcp(np.array([c[0], c[1], z0]), np.zeros(5))
    ql, _ = ik_tcp(np.array([c[0], c[1], z0 + 0.10]), np.zeros(5))
    drive(qp, GRIP_OPEN, 150)
    drive(qg, APPROACH_GRIP, 150)
    ca = contacts()
    drive(qg, GRIP_CLOSE, 140)
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE; mujoco.mj_step(m, d)
    cc = contacts(); gq = float(d.qpos[GQA])
    if verbose:
        print(f"    접근접촉={ca} 닫음접촉={cc} grip_q={gq:.2f} cube={d.body('cube').xpos.round(3).tolist()} ik={eg*1000:.1f}mm")
    ml = 0.0; cur = d.ctrl[:5].copy()
    for s in range(400):
        d.ctrl[:5] = cur + (ql - cur) * (s + 1) / 400; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        ml = max(ml, float(d.body("cube").xpos[2]) - z0)
    fin = float(d.body("cube").xpos[2]) - z0
    return ml, fin, cc, gq


print(f"커넥터 집는폭(x)={HX*2000:.0f}mm 폭(y)={HY*2000:.0f}mm 높이(z)={HZ*2000:.0f}mm ({m.body_mass[CUBE_BID]*1000:.1f}g) | FORCE={FORCE} APPROACH={APPROACH_GRIP} CLOSE={GRIP_CLOSE} TCP_x={TCP_LOCAL[0]:+.4f}")
POS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
       (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]
res = []; lifts = []
for k, xy in enumerate(POS):
    ml, fin, cc, gq = episode(xy, verbose=(k == 0))
    ok = fin >= 0.03
    res.append(ok); lifts.append(fin * 1000)
    print(f"  {xy}: max_lift={ml*1000:5.1f} final={fin*1000:6.1f}mm 접촉={cc} grip_q={gq:+.2f} {'✅' if ok else ''}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%  중앙final={np.median(lifts):.1f}mm")
