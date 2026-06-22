"""전략2 — 메시 vertex로 손가락 안쪽면 갭 중심 정밀 계산 후 그 점을 TCP로.

핵심 발견(실측):
- moving_jaw 는 회전 조. ctrl(=position) 만 바꾸고 mj_forward 해도 관절이 안 움직임 →
  반드시 mj_step 으로 안착시킨 '실제 닫힘 자세'의 메시 vertex 로 갭을 재야 함.
- gripper body 로컬에서 개폐축 = x. 고정손가락(geom29) 안쪽면 ≈ x=-0.008(상수).
  moving 조(geom31) 끝은 닫을수록 x 가 -방향으로 호를 그리며 내려옴.
- 닫힘 진행(q: 1.33 open → 음수)에 따라 두 안쪽면이 만나는 'pinch 점'의 x 가 이동.
  → AABB 가 아니라 실측 vertex 로 '실제 닫혔을 때' 갭 중심을 구해 TCP_LOCAL 로 삼는다.

전략:
1. 빈 손(큐브 없이) 그리퍼를 GRIP_CLOSE_PROBE 로 닫아 안착시킨 뒤, 그 자세의 geom29/31
   메시 vertex 를 gripper body 로컬로 변환. 손가락끝 높이대 z 에서 두 안쪽면 중점(x,y)과
   z 를 TCP_LOCAL 로 산출.
2. 이 TCP 로 IK(검증된 ik_tcp)를 풀어 8위치 grasp. 파라미터 반복 튜닝.

사용: python _grasp_strat_mesh_vert_gap.py [FORCE] [TCP_Z_OFF] [XOFF] [GRASP_DZ] [PROBE_Q]
  FORCE: 팔 forcerange(±). 0 이면 XML기본(1.5). 6 이면 메커니즘 격리.
  TCP_Z_OFF: 산출된 tip z 에 더하는 보정(m). 0 이면 실측 tip z.
  XOFF: TCP x 추가 보정(m).
  GRASP_DZ: 큐브중심 대비 grasp 타겟 z(m, -면 더 깊이).
  PROBE_Q: 갭 측정용 닫힘 진행 목표 gripper qpos.
"""
import mujoco, numpy as np, sys
np.seterr(all="ignore")

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper"); GQA = m.jnt_qposadr[GJ]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TABLE_TOP = 0.16

FORCE = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
TCP_Z_OFF = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
XOFF = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
GRASP_DZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
PROBE_Q = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
# GRIP_CLOSE = 닫힘 목표 ctrl(=목표 관절각). 위치서보라 -1.5 면 끝까지 닫혀 30mm 큐브를
# 호로 쳐낸다. 큐브를 면-면 압착하려면 30mm 갭 자세(q≈+0.2)보다 살짝 더 닫힌 값으로 멈춰
# 잔류 오차로 압착력을 만든다. 6번째 인자로 튜닝.
GRIP_CLOSE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
APPROACH_GRIP = float(sys.argv[7]) if len(sys.argv) > 7 else 0.45  # 하강 시 반개 각
GRIP_OPEN = 1.5

if FORCE > 0:
    for ai in range(6):  # 팔5 + 그리퍼1. 그리퍼도 같이 격리(닫힘 토크 병목 확인용).
        m.actuator_forcerange[ai] = [-FORCE, FORCE]


def mesh_local_posed(dd, geom_i):
    """현재 dd 자세 기준, geom 의 메시 vertex 를 gripper body 로컬로 변환."""
    did = m.geom_dataid[geom_i]; a = m.mesh_vertadr[did]; n = m.mesh_vertnum[did]
    v = m.mesh_vert[a:a + n].reshape(-1, 3).astype(np.float64)
    v = v[np.isfinite(v).all(1) & (np.abs(v) < 1.0).all(1)]
    gp = dd.geom_xpos[geom_i].astype(np.float64)
    gRm = dd.geom_xmat[geom_i].reshape(3, 3).astype(np.float64)
    gx = dd.xpos[GBID].astype(np.float64); gR = dd.xmat[GBID].reshape(3, 3).astype(np.float64)
    return (gR.T @ (((gRm @ v.T).T + gp) - gx).T).T


CUBE_W = 0.030  # 큐브 폭(30mm). 핀치 갭이 이 값일 때의 자세에서 TCP 정의.


def measure_tcp_local(band_z):
    """moving_jaw 회전 갭이 큐브폭(30mm)이 되는 그리퍼 자세를 찾고, 그 핀치 중심을 TCP 로.

    핵심: AABB/완전닫힘 tip 이 아니라, '큐브가 실제로 끼이는 자세'(갭=30mm)에서
    band_z 높이의 두 안쪽면 중점을 잰다. 개폐축 x. cz=band_z(손가락이 큐브를 감싸는 높이).

    band_z 부근(±7mm) 슬라이스에서 fixed 안쪽면(최대 x), moving 안쪽면(최소 x).
    gripper 관절 q 를 open→close 로 훑어 gap≈CUBE_W 인 q 를 이분 탐색.
    """
    dd = mujoco.MjData(m)

    def gap_center_at_q(q):
        dd.qpos[:] = 0; dd.qpos[GQA] = q
        mujoco.mj_forward(m, dd)
        mv = mesh_local_posed(dd, 31); f = mesh_local_posed(dd, 29)
        sel = lambda a: a[(a[:, 2] >= band_z - 0.007) & (a[:, 2] < band_z + 0.007)]
        mb = sel(mv); fb = sel(f)
        if len(mb) < 3 or len(fb) < 3:
            return None
        fx = fb[:, 0].max(); mx = mb[:, 0].min()
        cy = 0.5 * (np.median(mb[:, 1]) + np.median(fb[:, 1]))
        return (mx - fx), 0.5 * (mx + fx), cy, fx, mx

    # 이분 탐색: gap 은 q 증가에 단조 증가. gap=CUBE_W 인 q.
    lo, hi = -0.4, 0.7
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        r = gap_center_at_q(mid)
        if r is None:
            hi = mid; continue
        if r[0] > CUBE_W:
            hi = mid
        else:
            lo = mid
    qsol = 0.5 * (lo + hi)
    g, cx, cy, fx, mx = gap_center_at_q(qsol)
    return np.array([cx, cy, band_z]), (fx, mx, g, qsol)


# band_z: 큐브를 감싸는 손가락 높이. PROBE_Q 인자를 band_z 로 재사용(기본 -0.090).
BAND_Z = PROBE_Q if PROBE_Q < 0 else -0.090
TCP_BASE, probe = measure_tcp_local(BAND_Z)
TCP_LOCAL = TCP_BASE + np.array([XOFF, 0.0, TCP_Z_OFF])


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def ik_tcp(target, seed):
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
    # 사전접근(높이 70mm 위)은 완전 개방. 하강은 APPROACH_GRIP(반개)로 — 그래야 moving 조 끝이
    # 큐브 밴드 높이까지 내려와 양 손가락이 큐브 옆을 straddle 한다(완전개방이면 조가 위로 들려 못 감쌈).
    drive(q_pre, GRIP_OPEN, 150)
    drive(q_grasp, APPROACH_GRIP, 150)
    if verbose:
        cb = d.body('cube').xpos
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={cb.round(3).tolist()} 접촉={jaw_cube_contacts()} ik오차={e_g*1000:.1f}mm")
    drive(q_grasp, GRIP_CLOSE, 120)
    # 닫힘 후 압착 안정화 hold(잡은 채 정지) — 슬립 전 충분히 조이게.
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE; mujoco.mj_step(m, d)
    grip_q = float(d.qpos[GQA])
    if verbose:
        print(f"    닫음후  접촉={jaw_cube_contacts()} grip_q={grip_q:.3f} cube={d.body('cube').xpos.round(3).tolist()}")
    maxlift = 0.0; cur = d.ctrl[:5].copy()
    for s in range(450):  # 천천히 들어올림(관성 슬립 방지)
        t = (s + 1) / 450
        d.ctrl[:5] = cur + (q_lift - cur) * t; d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    return maxlift, e_g, jaw_cube_contacts(), grip_q


POSITIONS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
             (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]

print(f"FORCE={FORCE or 'XML(1.5)'} TCP_Z_OFF={TCP_Z_OFF} XOFF={XOFF} GRASP_DZ={GRASP_DZ} BAND_Z_arg={PROBE_Q} GRIP_CLOSE={GRIP_CLOSE} APPROACH_GRIP={APPROACH_GRIP}")
print(f"  측정 TCP_LOCAL={TCP_LOCAL.round(4).tolist()} BAND_Z={BAND_Z}  (핀치자세 fixed_innerX={probe[0]:+.4f} moving_innerX={probe[1]:+.4f} gap={probe[2]*1000:.1f}mm q={probe[3]:.3f})")
res = []
lifts = []
for k, xy in enumerate(POSITIONS):
    ml, eg, nc, gq = episode(xy, verbose=(k == 0))
    ok = ml >= 0.04
    res.append(ok); lifts.append(ml * 1000)
    print(f"  cube{xy}: lift={ml*1000:5.1f}mm ik={eg*1000:4.1f}mm 접촉={nc} grip_q={gq:+.3f} {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%  중앙값lift={np.median(lifts):.1f}mm")
