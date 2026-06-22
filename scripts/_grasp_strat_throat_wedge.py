"""전략4 — throat wedge: 큐브를 손가락 뿌리(throat) 깊숙이 넣고 닫아 wedge 핀치.

검증된 IK/기하(_grasp_test_v2.py)를 그대로 재사용한다:
- TCP = gripper body-local [0,0,TCP_Z]
- IK: TCP→target(위치3) + gripper body +z축→월드+z(손가락 아래, 정렬2) = 5제약/5DOF

핵심 아이디어:
- moving_jaw 는 닫힐 때 x=+0.056 → -0.016, z=-0.029 근방에서 큰 호를 그린다(뿌리쪽).
- 고정패드(geom29)는 z=-0.098(끝)~+0.008(뿌리) 로 길다.
- 큐브를 TCP_Z 를 얕게(예: -0.05 ~ -0.04, 뿌리쪽) 잡아 두 손가락이 모이는 깊은 V 안쪽에
  앉히면, 닫을 때 가동조 호가 큐브를 쳐내기보다 뿌리로 밀어넣어 wedge 핀치한다.

사용:
  python _grasp_strat_throat_wedge.py [TCP_Z] [GRASP_DZ] [APPROACH_DZ] [LIFT_DZ] [FORCE] [GRIP_OPEN] [GRIP_CLOSE] [verbose]
"""
import mujoco
import numpy as np
import sys

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m)
d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)

ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")
CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TABLE_TOP = 0.16

# ── 파라미터 ────────────────────────────────────────────────
TCP_Z = float(sys.argv[1]) if len(sys.argv) > 1 else -0.085
GRASP_DZ = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0   # 큐브중심 대비 grasp 타겟 z 보정(+=위로 덜내림)
APPROACH_DZ = float(sys.argv[3]) if len(sys.argv) > 3 else 0.07
LIFT_DZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.10
FORCE = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
GRIP_OPEN = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5
GRIP_CLOSE = float(sys.argv[7]) if len(sys.argv) > 7 else -1.5
# XOFF: grasp 타겟을 개폐축(월드+x) 으로 보정. 닫힐 때 가동조가 큐브를 +x(로컬)로 쳐내므로
# 큐브를 미리 로컬 -x(=월드+x 로 TCP 이동) 쪽에 놓아 닫으면 중심(로컬x≈0)에 안착시킨다.
XOFF = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0
VERBOSE = "v" in sys.argv[9:]

if FORCE > 0:
    for ai in range(5):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]

TCP_LOCAL = np.array([0.0, 0.0, TCP_Z])


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def ik_tcp(target, seed, grip):
    q = np.array(seed, float)
    UP = np.array([0.0, 0.0, 1.0])
    pos_err = np.ones(3)
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = grip
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP_LOCAL
        z_local = R[:, 2]
        pos_err = target - tcp
        rot_err = np.cross(z_local, UP)
        err6 = np.concatenate([pos_err, 0.7 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv))
        jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, tcp, GBID)
        J = np.vstack([jacp[:, DOF], jacr[:, DOF]])
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


def jaw_cube_contacts():
    n = 0
    for c in range(d.ncon):
        g1, g2 = d.contact[c].geom1, d.contact[c].geom2
        if (g1 in JAWG and g2 in CUBE_GEOM) or (g2 in JAWG and g1 in CUBE_GEOM):
            n += 1
    return n


def episode(cube_xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + 0.015]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0
    d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy()
    z0 = float(cube[2])

    q_pre, _ = ik_tcp(np.array([cube[0] + XOFF, cube[1], z0 + APPROACH_DZ]), np.zeros(5), GRIP_OPEN)
    q_grasp, e_g = ik_tcp(np.array([cube[0] + XOFF, cube[1], z0 + GRASP_DZ]), np.zeros(5), GRIP_OPEN)
    q_lift, _ = ik_tcp(np.array([cube[0] + XOFF, cube[1], z0 + LIFT_DZ]), np.zeros(5), GRIP_CLOSE)

    drive(q_pre, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_OPEN, 250)
    # 큐브가 안착하도록 잔류 속도 제거(가동조 닫힘 호가 큐브를 쳐내는 비대칭 충격 완화)
    d.qvel[m.jnt_dofadr[CJ]:m.jnt_dofadr[CJ] + 6] = 0.0
    mujoco.mj_forward(m, d)

    if verbose:
        R = d.xmat[GBID].reshape(3, 3)
        cb = d.body('cube').xpos
        cb_local = R.T @ (cb - d.xpos[GBID])
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={cb.round(3).tolist()} 접촉={jaw_cube_contacts()}")
        print(f"      cube(gripper로컬)={cb_local.round(4).tolist()}  (TCP_Z={TCP_Z})")

    # 느린 점진 닫힘: 가동조가 큐브를 쳐내지 않고 부드럽게 핀치하도록 ctrl 을 천천히 램프
    for s in range(400):
        d.ctrl[:5] = q_grasp
        d.ctrl[5] = GRIP_OPEN + (GRIP_CLOSE - GRIP_OPEN) * ((s + 1) / 400)
        mujoco.mj_step(m, d)

    if verbose:
        print(f"    닫음후 접촉={jaw_cube_contacts()} grip_q={float(d.qpos[GQA]):.3f} "
              f"cube={d.body('cube').xpos.round(3).tolist()}")

    maxlift = 0.0
    cur = d.ctrl[:5].copy()
    for s in range(250):
        t = (s + 1) / 250
        d.ctrl[:5] = cur + (q_lift - cur) * t
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    # final settle at top
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    final_lift = float(d.body("cube").xpos[2]) - z0
    return maxlift, final_lift, e_g, float(d.qpos[GQA]), jaw_cube_contacts()


XY = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
      (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]

print(f"[throat_wedge] TCP_Z={TCP_Z} GRASP_DZ={GRASP_DZ} APPROACH_DZ={APPROACH_DZ} "
      f"LIFT_DZ={LIFT_DZ} FORCE={FORCE} OPEN={GRIP_OPEN} CLOSE={GRIP_CLOSE} XOFF={XOFF}")
res = []
lifts = []
for k, xy in enumerate(XY):
    ml, fl, eg, gq, ct = episode(xy, verbose=(VERBOSE and k == 0))
    ok = ml >= 0.04
    res.append(ok)
    lifts.append(ml * 1000)
    print(f"  cube{xy}: max_lift={ml*1000:5.1f}mm final={fl*1000:5.1f}mm "
          f"ik={eg*1000:.1f}mm grip_q={gq:.2f} 접촉={ct}  {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%  "
      f"median_lift={np.median(lifts):.1f}mm")
