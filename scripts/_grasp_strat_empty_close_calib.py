"""전략 1 — 빈손 닫힘 캘리브레이션으로 진짜 TCP 찾기.

아이디어:
  큐브 없이 그리퍼를 아래향 자세로 두고 GRIP_OPEN→GRIP_CLOSE 로 닫으면서
  고정패드(geom29)와 가동패드(geom31)의 콜리전 표면이 '30mm 큐브를 핀치하는 순간'
  두 패드 안쪽면의 중점을 그리퍼 body 로컬좌표로 측정한다.
  그 중점을 TCP_LOCAL 로 삼으면 큐브가 갭 중앙에 와 대칭 핀치가 된다.

검증된 IK/기하 재사용: _grasp_test_v2.py 의 ik_tcp(위치3+그리퍼body z축→월드+z 정렬2).
단, TCP_LOCAL 을 [0,0,TCP_Z] 가 아니라 캘리브레이션으로 얻은 3D 오프셋으로 둔다.

scene_grasp.xml / so101 calib / 기존 _grasp_*.py 는 절대 수정하지 않는다.
"""
import mujoco
import numpy as np
import sys

XML = "SO-ARM100/Simulation/SO101/scene_grasp.xml"
m = mujoco.MjModel.from_xml_path(XML)
d = mujoco.MjData(m)
d_ik = mujoco.MjData(m)
d_cal = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)

ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint")
CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GRIPQADR = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
FIXED_G, MOVING_G = 29, 31


def _mesh_verts(gi):
    did = m.geom_dataid[gi]
    va = m.mesh_vertadr[did]
    vn = m.mesh_vertnum[did]
    return m.mesh_vert[va:va + vn].reshape(-1, 3).copy()


V_FIX = _mesh_verts(FIXED_G)
V_MOV = _mesh_verts(MOVING_G)
# 손가락끝 z-밴드(그리퍼 body 로컬). 이 구간의 실제 메시면이 큐브를 핀치한다.
BAND_LO, BAND_HI = -0.090, -0.045
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
JAWG = [i for i in range(m.ngeom)
        if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
TABLE_TOP = 0.16
CUBE_HALF = 0.015

# ---- 파라미터 (CLI 튜닝) ----
GRIP_OPEN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
GRIP_CLOSE = float(sys.argv[2]) if len(sys.argv) > 2 else -1.5
FORCE = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0       # 팔 5관절 forcerange
GFORCE = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0      # 그리퍼 forcerange (0=XML기본 1.5)
GRASP_DZ = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0    # 큐브중심 대비 grasp 타겟 z 보정
# 캘리브 기준 갭(=큐브폭 30mm). 두 안쪽면이 이 거리일 때의 그리퍼 자세에서 중점을 TCP로.
TARGET_GAP = float(sys.argv[6]) if len(sys.argv) > 6 else 0.030
# 캘리브 TCP x에 더할 보정(+면 큐브를 가동조 쪽으로 옮겨 고정손가락 끝이 하강 시 큐브를 안 침).
XOFF = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0

if FORCE > 0:
    for ai in range(5):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]
if GFORCE > 0:
    m.actuator_forcerange[5] = [-GFORCE, GFORCE]


def pad_faces_local(dd):
    """그리퍼 body 로컬에서 고정/가동 패드의 실제 메시면 안쪽면 x와 밴드 z중심을 반환.
    AABB(geom29=몸체 셸 전체) 대신 손가락끝 z-밴드의 실제 메시정점을 쓴다."""
    gx = dd.xpos[GBID]
    gR = dd.xmat[GBID].reshape(3, 3)
    P29 = (dd.geom_xpos[FIXED_G] + V_FIX @ dd.geom_xmat[FIXED_G].reshape(3, 3).T - gx) @ gR
    P31 = (dd.geom_xpos[MOVING_G] + V_MOV @ dd.geom_xmat[MOVING_G].reshape(3, 3).T - gx) @ gR
    b29 = P29[(P29[:, 2] > BAND_LO) & (P29[:, 2] < BAND_HI)]
    b31 = P31[(P31[:, 2] > BAND_LO) & (P31[:, 2] < BAND_HI)]
    if len(b29) == 0 or len(b31) == 0:
        return None
    f29 = b29[:, 0].max()    # 고정패드 안쪽면(가동조 쪽, +x)
    f31 = b31[:, 0].min()    # 가동패드 안쪽면(고정조 쪽, -x)
    zc = 0.5 * (b29[:, 2].mean() + b31[:, 2].mean())
    return f29, f31, zc


def calibrate_tcp():
    """빈손으로 OPEN→CLOSE 스윕. 두 안쪽면 갭이 TARGET_GAP 으로 줄어드는 순간의
    중점(그리퍼 body 로컬)을 TCP_LOCAL 로 반환."""
    mujoco.mj_resetData(m, d_cal)
    mujoco.mj_forward(m, d_cal)
    d_cal.ctrl[:5] = 0.0
    d_cal.ctrl[5] = GRIP_OPEN
    for _ in range(400):
        mujoco.mj_step(m, d_cal)
    # 천천히 닫으며 갭을 추적
    prev = None
    n = 1200
    last = None
    for s in range(n):
        t = (s + 1) / n
        d_cal.ctrl[5] = GRIP_OPEN + (GRIP_CLOSE - GRIP_OPEN) * t
        mujoco.mj_step(m, d_cal)
        pf = pad_faces_local(d_cal)
        if pf is None:
            continue
        f29, f31, zc = pf
        gap = f31 - f29
        midx = 0.5 * (f29 + f31)
        rec = (gap, midx, zc)
        if prev is not None and prev[0] >= TARGET_GAP >= gap:
            g0, x0, z0 = prev
            g1, x1, z1 = rec
            w = (g0 - TARGET_GAP) / (g0 - g1 + 1e-12)
            tx = x0 + (x1 - x0) * w
            tz = z0 + (z1 - z0) * w
            return np.array([tx, 0.0, tz]), gap
        prev = rec
        last = rec
    if last is not None:
        return np.array([last[1], 0.0, last[2]]), last[0]
    return np.array([0.0, 0.0, -0.064]), 0.0


TCP_LOCAL, calib_gap = calibrate_tcp()
TCP_LOCAL = TCP_LOCAL + np.array([XOFF, 0.0, 0.0])


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def ik_tcp(target, seed):
    q = np.array(seed, float)
    UP = np.array([0., 0., 1.])
    pos_err = np.ones(3)
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


def grip_q():
    return float(d.qpos[GRIPQADR])


def episode(cube_xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + CUBE_HALF]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0
    d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy()
    z0 = float(cube[2])
    q_pre, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5))
    q_grasp, e_g = ik_tcp(np.array([cube[0], cube[1], z0 + GRASP_DZ]), np.zeros(5))
    q_lift, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5))
    drive(q_pre, GRIP_OPEN, 150)
    drive(q_grasp, GRIP_OPEN, 150)
    if verbose:
        cb = d.body('cube').xpos
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={cb.round(3).tolist()} "
              f"TCP-cube={(tcp_pos(d)-cb).round(3).tolist()} 접촉={jaw_cube_contacts()}")
    drive(q_grasp, GRIP_CLOSE, 120)
    contacts_closed = jaw_cube_contacts()
    gq = grip_q()
    if verbose:
        print(f"    닫음후 접촉={contacts_closed} grip_q={gq:.3f} cube={d.body('cube').xpos.round(3).tolist()}")
    maxlift = 0.0
    cur = d.ctrl[:5].copy()
    for s in range(250):
        t = (s + 1) / 250
        d.ctrl[:5] = cur + (q_lift - cur) * t
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    return maxlift, e_g, contacts_closed, gq


POSITIONS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
             (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]


def run():
    print(f"[CALIB] TCP_LOCAL={TCP_LOCAL.round(4).tolist()} (calib_gap={calib_gap*1000:.1f}mm, "
          f"TARGET_GAP={TARGET_GAP*1000:.0f}mm)")
    print(f"GRIP_OPEN={GRIP_OPEN} GRIP_CLOSE={GRIP_CLOSE} FORCE={FORCE} "
          f"GFORCE={GFORCE or 'XML(1.5)'} GRASP_DZ={GRASP_DZ}")
    res = []
    lifts = []
    for k, xy in enumerate(POSITIONS):
        ml, eg, nc, gq = episode(xy, verbose=(k == 0))
        ok = ml >= 0.04
        res.append(ok)
        lifts.append(ml)
        print(f"  cube{xy}: lift={ml*1000:5.1f}mm ik={eg*1000:4.1f}mm "
              f"닫음접촉={nc} grip_q={gq:+.2f} {'성공' if ok else '실패'}")
    rate = sum(res) / len(res)
    print(f"성공률: {sum(res)}/{len(res)} = {100*rate:.0f}%  "
          f"중앙값lift={1000*float(np.median(lifts)):.1f}mm")
    return rate, lifts


if __name__ == "__main__":
    run()
