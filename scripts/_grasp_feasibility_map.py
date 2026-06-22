"""Grasp 가용영역 맵 (임시 진단) — 1.5Nm 서보가 탑다운 자세를 '유지'하는 (x,z) 영역 측정.

핵심 질문: IK로는 도달하는 자세를, position 액추에이터(forcerange ±1.5Nm)가
중력 하에서 실제로 버티는가? 큐브 없이 팔만 구동해 settle 오차로 판정한다.
오차가 작으면 = 그 (x, 높이)에 작업대+큐브를 놓으면 grasp 가능.
"""
import mujoco, numpy as np

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene.xml")
d = mujoco.MjData(m)
d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID)]
GRIP_OPEN = 1.5


def jaw_mid(dd):
    return np.mean([dd.geom_xpos[i] for i in JAWG], axis=0)


def ik_jaw(target, seed):
    """jaw 중점→target + 그리퍼 x_local 을 월드 +z 로 정렬(탑다운). 5제약/5DOF."""
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


def hold_test(target):
    """탑다운 자세로 IK → 그 자세로 구동 → settle → jaw중점 실제 위치 측정."""
    q, ik_err = ik_jaw(target, np.zeros(5))
    if ik_err > 5e-3:
        return None  # 키네매틱하게도 도달 못함
    mujoco.mj_resetData(m, d)
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    # 부드럽게 목표 자세로
    for s in range(300):
        t = (s + 1) / 300
        d.ctrl[:5] = q * t
        d.ctrl[5] = GRIP_OPEN
        mujoco.mj_step(m, d)
    # 추가로 버티게 두고 settle
    for _ in range(300):
        mujoco.mj_step(m, d)
    mid = jaw_mid(d)
    hold_err = np.linalg.norm(mid - target)
    q_final = np.array([d.qpos[a] for a in QAD])
    return ik_err, hold_err, mid, q, q_final


XS = [0.10, 0.13, 0.16, 0.19, 0.22]
ZS = [0.12, 0.16, 0.20, 0.24, 0.28]
print("탑다운 grasp 자세 유지 가용영역 (jaw중점 settle 오차, mm)")
print("  '.' = IK 미도달   숫자 = settle오차mm   [*] = 유지 양호(<8mm)\n")
print("        " + "  ".join(f"z={z:.2f}" for z in ZS))
feasible = []
for x in XS:
    row = [f"x={x:.2f}"]
    for z in ZS:
        r = hold_test(np.array([x, 0.0, z]))
        if r is None:
            row.append("   .  ")
        else:
            ik_err, hold_err, mid, q, qf = r
            mm = hold_err * 1000
            mark = "*" if mm < 8 else " "
            row.append(f"{mm:5.0f}{mark}")
            if mm < 8:
                feasible.append((x, z, mm))
    print("  ".join(row))

print()
if feasible:
    print("유지 양호(<8mm) 후보:")
    for x, z, mm in sorted(feasible, key=lambda t: t[2]):
        print(f"  x={x:.2f}  z={z:.2f}  settle오차={mm:.1f}mm")
    bx, bz, _ = min(feasible, key=lambda t: t[2])
    print(f"\n→ 작업대 표면 높이 ≈ {bz:.2f}m, 큐브 x≈{bx:.2f} 권장 출발점")
else:
    print("유지 양호 영역 없음 — 더 높은 z / 더 가까운 x 로 격자 확장 필요")
