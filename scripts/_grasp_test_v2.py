"""grasp expert v2 — 진짜 TCP(손가락 패드 중점) + 올바른 탑다운 정렬(손가락이 아래로).

수정점(진단 결과):
- TCP = 그리퍼 몸체로컬 [0,0,TCP_Z] (손가락 패드 사이). jaw_mid(geom평균) 아님.
- 정렬: 그리퍼 body +z → 월드 +z (손가락=body -z 가 아래로). 기존 body x→up 은 손가락이 옆을 봄.
사용: python _grasp_test_v2.py [GRIP_OPEN] [GRIP_CLOSE] [TCP_Z] [FORCE]
"""
import mujoco, numpy as np, sys

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")

GRIP_OPEN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
GRIP_CLOSE = float(sys.argv[2]) if len(sys.argv) > 2 else -1.5
TCP_Z = float(sys.argv[3]) if len(sys.argv) > 3 else -0.085
FORCE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
GRASP_DZ = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0  # 큐브중심 대비 grasp 타겟 z 보정(-면 더깊이)
TABLE_TOP = 0.16
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TCP_LOCAL = np.array([0.0, 0.0, TCP_Z])
if FORCE > 0:
    for ai in range(5):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def ik_tcp(target, seed):
    """TCP→target(위치3) + 그리퍼 body z축→월드 +z(손가락 아래, 정렬2) = 5제약/5DOF."""
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pos_err = np.ones(3)
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP_LOCAL
        z_local = R[:, 2]
        pos_err = target - tcp
        rot_err = np.cross(z_local, UP)
        err6 = np.concatenate([pos_err, 0.7 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, tcp, GBID)
        J = np.vstack([jacp[:, DOF], jacr[:, DOF]])
        dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err6)
        q = q + np.clip(dq, -0.2, 0.2)
    return q, np.linalg.norm(pos_err)


def drive(q_arm, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        t = (s + 1) / n
        d.ctrl[:5] = cur + (q_arm - cur) * t; d.ctrl[5] = grip
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
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    q_pre, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5))
    q_grasp, e_g = ik_tcp(np.array([cube[0], cube[1], z0 + GRASP_DZ]), np.zeros(5))
    q_lift, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5))
    drive(q_pre, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_OPEN, 150)
    if verbose:
        R = d.xmat[GBID].reshape(3, 3)
        fixed_c = d.geom_xpos[29] + R @ m.geom_aabb[29, :3]
        moving_c = d.geom_xpos[31] + R @ m.geom_aabb[31, :3]
        cb = d.body('cube').xpos
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={cb.round(3).tolist()} 접촉={jaw_cube_contacts()}")
        print(f"      고정패드29={fixed_c.round(3).tolist()} 가동패드31={moving_c.round(3).tolist()} body+z(월드)={R[:,2].round(2).tolist()}")
        print(f"      개폐축 body-x(월드)={R[:,0].round(2).tolist()}  cube-고정패드={(cb-fixed_c).round(3).tolist()}  cube-가동패드={(cb-moving_c).round(3).tolist()}")
    drive(q_grasp, GRIP_CLOSE, 120)
    if verbose:
        print(f"    닫음후  접촉={jaw_cube_contacts()} grip_q={float(d.qpos[m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT,'gripper')]]):.3f} cube={d.body('cube').xpos.round(3).tolist()}")
    maxlift = 0.0; cur = d.ctrl[:5].copy()
    for s in range(250):
        t = (s + 1) / 250
        d.ctrl[:5] = cur + (q_lift - cur) * t; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    return maxlift, e_g


print(f"GRIP_OPEN={GRIP_OPEN} GRIP_CLOSE={GRIP_CLOSE} TCP_Z={TCP_Z} FORCE={FORCE or 'XML기본(1.5)'}")
res = []
for k, xy in enumerate([(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01), (0.12, 0.015),
                        (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]):
    ml, eg = episode(xy, verbose=(k == 0))
    ok = ml >= 0.04
    res.append(ok)
    print(f"  cube{xy}: max_lift={ml*1000:5.1f}mm  ik오차={eg*1000:.1f}mm  {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%")
