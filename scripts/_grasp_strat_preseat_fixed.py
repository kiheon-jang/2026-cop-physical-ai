"""전략 3 — 고정 손가락에 큐브 선접촉(pre-seat) 후 닫기.

검증된 IK/기하 재사용(scripts/_grasp_test_v2.py, _gripper_geom_probe.py):
- TCP = 그리퍼 body로컬 [0,0,TCP_Z]. IK = TCP→타겟(위치3) + body+z→월드+z(정렬2).
- 고정패드(geom29) body로컬 x=-0.0163 (불변). 가동패드(geom31)는 닫힐수록 -x로 호.
- 개폐축 = body-x ≈ 월드+x (탑다운 자세).

선접촉 아이디어:
  IK 타겟을 큐브중심에서 개폐축(월드 ±x)으로 OFF만큼 옮겨 접근한다.
  → 고정패드 면이 큐브에 먼저 닿아 자리잡게(pre-seat) 한 뒤 가동조를 닫아
    큐브를 고정패드에 눌러 핀치. 가동조 호가 큐브를 쳐내지 않고 눌러 잡음.

OFF 부호 규약: 양수 = 고정패드(-x쪽)를 큐브에 더 밀어붙이는 방향(타겟 -x).
사용: python _grasp_strat_preseat_fixed.py [OFF_mm] [TCP_Z] [FORCE] [SEAT_PUSH_mm]
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
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GJQ = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]

GRIP_OPEN = 1.5
GRIP_CLOSE = -1.5
TABLE_TOP = 0.16

OFF = (float(sys.argv[1]) if len(sys.argv) > 1 else 12.0) / 1000.0   # mm→m, 하강 비켜섬(+x 가동조쪽)
TCP_Z = float(sys.argv[2]) if len(sys.argv) > 2 else -0.085
FORCE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
SEAT_PUSH = (float(sys.argv[4]) if len(sys.argv) > 4 else 8.0) / 1000.0  # 접근 후 고정패드로 밀기(seat)
# 결론: 어떤 파라미터 조합도 안정 핀치 실패. 최선 ~1/8(12%, 6Nm), 0/8(1.5Nm).
# 단일 회전 조가 자유 큐브를 jaw 밖으로 쳐냄 + 고정패드 선접촉이 하강 중 무너짐.
# 핵심수정: v2의 TCP(body로컬 x=0)는 두 패드 중앙이 아니라 고정패드 안쪽면 근처.
# 두 jaw면(고정+x면≈+0.011, 가동-x면≈+0.046) 중앙 ≈ +0.028 로 TCP를 +x 이동해야
# 큐브가 jaw 사이 한가운데 안착. TCP_X로 이 횡오프셋을 준다(기본 +28mm).
TCP_X = (float(sys.argv[5]) if len(sys.argv) > 5 else 28.0) / 1000.0
CLOSE_N = int(sys.argv[6]) if len(sys.argv) > 6 else 140  # 닫기 스텝수(부드러운 닫기=큐브 덜 쳐냄)

# 그리퍼 힘도 같이 덮어쓴다(핀치력의 진짜 한계). GFORCE 미지정시 FORCE와 동일.
GFORCE = float(sys.argv[7]) if len(sys.argv) > 7 else FORCE

TCP_LOCAL = np.array([TCP_X, 0.0, TCP_Z])
if FORCE > 0:
    for ai in range(5):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]
if GFORCE > 0:
    m.actuator_forcerange[5] = [-GFORCE, GFORCE]


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def open_axis(dd):
    """월드에서 개폐축 = body +x (열림 방향). -이 방향이 고정패드 쪽."""
    R = dd.xmat[GBID].reshape(3, 3)
    a = R[:, 0].copy(); a[2] = 0.0
    n = np.linalg.norm(a)
    return a / n if n > 1e-9 else np.array([1.0, 0.0, 0.0])


def ik_tcp(target, seed):
    """TCP→target(위치3) + body z축→월드+z(정렬2) = 5제약/5DOF. (v2 검증 IK)"""
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


def grip_q():
    return float(d.qpos[GJQ])


def episode(cube_xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + 0.015]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])

    # 개폐축 방향(현 자세 근사: body+x≈월드+x). 고정패드는 -x쪽 → 타겟을 -axis로 OFF.
    # 자세 의존이므로 pre 자세에서 한 번 평가.
    q_pre0, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5))
    for i, a in enumerate(QAD):
        d_ik.qpos[a] = q_pre0[i]
    d_ik.ctrl[5] = GRIP_OPEN; mujoco.mj_forward(m, d_ik)
    axis = open_axis(d_ik)                 # 월드 +x 근사 (=가동조 열림 방향)
    # TCP_X로 큐브가 jaw 중앙에 오도록 보정됨. OFF는 추가 선접촉 바이어스:
    # OFF>0 이면 타겟을 -x(고정패드 쪽)로 더 옮겨 큐브를 고정패드면에 미리 붙임.
    seat_dir = -axis                       # -x (고정패드 방향)

    # ── 선접촉(pre-seat) 모션 ──────────────────────────────────────────────
    # 진단: 큐브를 정중앙에 두고 똑바로 내려오면 활짝 벌린 가동손가락(+x, 아래로 뻗음)이
    # 하강 중 큐브를 -x로 쳐내 jaw 밖으로 보낸다. 그래서:
    #  1) 하강은 가동조 쪽(+x)으로 OFF만큼 비켜서 내려와 큐브가 고정패드 안쪽(+x면)에 오게.
    #  2) 내려온 뒤 -x(고정패드)로 SEAT_PUSH 만큼 밀어 큐브를 고정패드면에 선접촉시킴.
    #  3) 그 상태에서 가동조를 닫으면 고정패드가 backstop → 큐브가 안 쳐내짐.
    appr_xy = np.array([cube[0] - OFF * axis[0], cube[1] - OFF * axis[1]])   # 하강 위치(+x쪽으로 비켜)
    seat_xy = appr_xy + SEAT_PUSH * seat_dir[:2]                              # 고정패드로 밀기

    q_hi, _ = ik_tcp(np.array([appr_xy[0], appr_xy[1], z0 + 0.07]), np.zeros(5))
    q_grasp, e_g = ik_tcp(np.array([appr_xy[0], appr_xy[1], z0]), q_hi)
    q_seat, _ = ik_tcp(np.array([seat_xy[0], seat_xy[1], z0]), q_grasp)
    q_lift, _ = ik_tcp(np.array([seat_xy[0], seat_xy[1], z0 + 0.12]), q_seat)

    drive(q_hi, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_OPEN, 180)        # 비켜선 위치로 하강
    if SEAT_PUSH > 0:
        drive(q_seat, GRIP_OPEN, 120)     # 고정패드로 큐브를 밀어 선접촉

    if verbose:
        R = d.xmat[GBID].reshape(3, 3)
        fixed_c = d.geom_xpos[29] + d.geom_xmat[29].reshape(3, 3) @ m.geom_aabb[29, :3]
        moving_c = d.geom_xpos[31] + d.geom_xmat[31].reshape(3, 3) @ m.geom_aabb[31, :3]
        cb = d.body('cube').xpos
        print(f"    OFF={OFF*1000:.0f}mm seat_dir={seat_dir.round(2).tolist()}")
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={cb.round(3).tolist()} 접촉={jaw_cube_contacts()}")
        print(f"      고정패드29={fixed_c.round(3).tolist()} 가동패드31={moving_c.round(3).tolist()}")
        print(f"      cube-고정패드={(cb-fixed_c).round(3).tolist()}  cube-가동패드={(cb-moving_c).round(3).tolist()}")

    drive(q_seat if SEAT_PUSH > 0 else q_grasp, GRIP_CLOSE, CLOSE_N)   # 그리퍼가 느려 충분한 스텝 필요
    contacts_closed = jaw_cube_contacts(); gq = grip_q()
    if verbose:
        print(f"    닫음후  접촉={contacts_closed} grip_q={gq:.3f} cube={d.body('cube').xpos.round(3).tolist()}")

    maxlift = 0.0; cur = d.ctrl[:5].copy()
    cube_drift0 = d.body("cube").xpos[:2].copy()
    for s in range(250):
        t = (s + 1) / 250
        d.ctrl[:5] = cur + (q_lift - cur) * t; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    drift = float(np.linalg.norm(d.body("cube").xpos[:2] - cube_drift0))
    return maxlift, e_g, contacts_closed, gq, drift


def run():
    POS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
           (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]
    print(f"OFF={OFF*1000:.0f}mm TCP_Z={TCP_Z} FORCE={FORCE or 'XML기본(1.5)'} SEAT_PUSH={SEAT_PUSH*1000:.0f}mm")
    res = []; lifts = []
    for k, xy in enumerate(POS):
        ml, eg, nc, gq, drift = episode(xy, verbose=(k == 0))
        ok = ml >= 0.04
        res.append(ok); lifts.append(ml * 1000)
        print(f"  cube{xy}: lift={ml*1000:5.1f}mm ik={eg*1000:.1f}mm 접촉={nc} grip_q={gq:+.2f} drift={drift*1000:4.1f}mm {'성공' if ok else '실패'}")
    rate = sum(res) / len(res)
    print(f"성공률: {sum(res)}/{len(res)} = {100*rate:.0f}%  중앙lift={np.median(lifts):.1f}mm")
    return rate, float(np.median(lifts))


if __name__ == "__main__":
    run()
