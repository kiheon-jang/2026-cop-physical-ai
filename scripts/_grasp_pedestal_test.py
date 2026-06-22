"""작업대 위 큐브 grasp+lift 성공률 (재설계 검증).

scene_grasp.xml(작업대 윗면 z=0.16)에 큐브를 올리고, jaw중점 탑다운 IK 로
집어서 들어올린다. 여러 XY 위치(데이터 다양성)에서 성공률 측정.
목표: >90% (expert 검증 통과 기준).
"""
import mujoco, numpy as np, sys

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
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
APPROACH_Z = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
FORCE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0  # >0 이면 팔 5관절 forcerange 덮어쓰기
TABLE_TOP = 0.16
if FORCE > 0:
    for ai in range(5):  # pan,lift,elbow,wrist_flex,wrist_roll
        m.actuator_forcerange[ai] = [-FORCE, FORCE]


def jaw_mid(dd):
    return np.mean([dd.geom_xpos[i] for i in JAWG], axis=0)


def ik_jaw(target, seed):
    q = np.array(seed, float)
    UP = np.array([0.0, 0.0, 1.0])
    pos_err = np.ones(3)
    for _ in range(500):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        mid = jaw_mid(d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        x_local = R[:, 0]
        pos_err = target - mid
        rot_err = np.cross(x_local, UP)
        err6 = np.concatenate([pos_err, 0.5 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, mid, GBID)
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


def episode(cube_xy):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + 0.015]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):  # 작업대 위 큐브 안정화
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    # 매 타겟 zeros 시드 → 토크-유지 가능한 IK 브랜치 일관 선택 (체이닝 시드는 미유지 브랜치 선택)
    q_pre, _ = ik_jaw(np.array([cube[0], cube[1], z0 + 0.08]), np.zeros(5))
    q_grasp, e_grasp = ik_jaw(np.array([cube[0], cube[1], z0 + APPROACH_Z]), np.zeros(5))
    q_lift, _ = ik_jaw(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5))
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
    return maxlift, e_grasp


print(f"GRIP_OPEN={GRIP_OPEN} GRIP_CLOSE={GRIP_CLOSE} APPROACH_Z={APPROACH_Z} TABLE_TOP={TABLE_TOP}")
res = []
for xy in [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01), (0.12, 0.015),
           (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]:
    ml, eg = episode(xy)
    ok = ml >= 0.04
    res.append(ok)
    print(f"  cube{xy}: max_lift={ml*1000:5.1f}mm  ik오차={eg*1000:.1f}mm  {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%")
