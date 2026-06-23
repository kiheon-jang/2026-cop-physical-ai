"""갈래① — closed-loop sim grasp expert (visual servoing + graded close + re-grasp).

전제(확정 사실):
- 스톡 그리퍼=단일 회전조. 닫을 때 moving 조 안쪽면이 호를 그려 자유 큐브를 쳐냄.
- open-loop IK expert(_grasp_strat_mesh_vert_gap.py, mesh 손가락 씬)는 0/8: 접근/IK는 OK(0.5mm),
  닫는 순간/드는 순간 큐브 사출. 토크/개구폭/접촉모델 전부 반증.
- 실물은 텔레오퍼레이션(사람 closed-loop)으로 3~5cm 물체를 바닥에서 잡음 → open vs closed-loop 차이.

이 스크립트가 검증한 가설/실측(diag 스크립트들로 확인):
1) mesh 손가락 씬은 손가락'끝선' 접촉이라 닫아도 면압이 안 생기고, 더 닫을수록 호가 큐브를 쳐냄
   (drift 가 닫힘 진행에 따라 +x→-x→+x 로 진동, 들면 즉시 슬립). → 평평 패드 씬이 필수.
   scene_grasp_pads.xml(so101_grasp_calib.xml): 양 조에 4x12x18mm 평패드(마찰2.0). 면 접촉 patch 형성.
2) 닫힘은 '사람처럼 갭이 큐브폭에 맞는 grip_q 까지만' 점진적으로(over many steps) 닫고 멈춘다.
   한 번에 깊이 닫으면(-0.6) 호가 큐브를 좌우로 쳐냄. grip_q≈+0.10~0.15 에서 패드 8접촉 firm.
3) 들기: 작업대 위 x≈0.13 에서는 손목수직 IK 가 z≈0.211(=+36mm)밖에 못 올림(팔 도달한계).
   큐브를 들며 베이스쪽(x≈0.10)으로 당기는 위→안쪽 곡선 경로면 +40mm 도달(IK err 0.5mm).
   → closed-loop 로 매 step 큐브 현 xy 를 읽어 (x 를 LIFT_X 로 당기며) TCP를 큐브추종.
4) re-grasp: 닫은 뒤 패드 양쪽 firm 접촉이 안 잡히면 재개방·재접근·재시도(최대 RETRY).

수정 금지: scene/calib/기존 _grasp_*.py. 큐브 크기/위치·forcerange 는 코드로만.

사용: python _grasp_closedloop.py [CUBE_MM] [FORCE] [CLOSE_Q] [LIFT_X] [RETRY] [verbose]
  CUBE_MM : 큐브 한 변(mm). 30 또는 50.
  FORCE   : 팔/그리퍼 forcerange(±Nm). 0=XML기본(1.5). 메커니즘 격리는 6.
  CLOSE_Q : firm grip 목표 gripper qpos(점진 닫힘 종료점). 30mm 기본 0.13.
  LIFT_X  : 들 때 큐브를 당겨갈 x(베이스쪽). 기본 0.10.
  RETRY   : 재시도 최대 횟수.
  verbose : 1이면 step 로그.
"""
import mujoco, numpy as np, sys
np.seterr(all="ignore")

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp_pads.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
CUBE_BID = nid(mujoco.mjtObj.mjOBJ_BODY, "cube")
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
PADS = [nid(mujoco.mjtObj.mjOBJ_GEOM, "fixed_pad"), nid(mujoco.mjtObj.mjOBJ_GEOM, "moving_pad")]
FIXED_PAD, MOVING_PAD = PADS
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == CUBE_BID][0]
TCP_LOCAL = np.array([0.0071, -0.0002, -0.090])  # 검증된 패드 갭 중점
TABLE_TOP = 0.16
GRIP_OPEN = 1.5
APPROACH_GRIP = 0.45

CUBE_MM = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
FORCE = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
CLOSE_Q = float(sys.argv[3]) if len(sys.argv) > 3 else 0.13
LIFT_X = float(sys.argv[4]) if len(sys.argv) > 4 else 0.09
RETRY = int(sys.argv[5]) if len(sys.argv) > 5 else 3
VERBOSE = len(sys.argv) > 6 and sys.argv[6] == "1"

HALF = CUBE_MM / 2000.0
m.geom_size[CUBE_GEOM] = [HALF, HALF, HALF]
m.body_mass[CUBE_BID] = 0.05 * (HALF / 0.015) ** 3
mujoco.mj_setConst(m, d)
if FORCE > 0:
    for ai in range(6):
        m.actuator_forcerange[ai] = [-FORCE, FORCE]


def tcp_pos(dd):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ TCP_LOCAL


def ik_tcp(target, seed):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pos_err = np.ones(3)
    for _ in range(700):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ TCP_LOCAL
        pos_err = target - tcp
        rot_err = np.cross(R[:, 2], UP)
        err6 = np.concatenate([pos_err, 0.7 * rot_err])
        if np.linalg.norm(pos_err) < 5e-4 and np.linalg.norm(rot_err) < 0.02:
            break
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        mujoco.mj_jac(m, d_ik, jacp, jacr, tcp, GBID)
        J = np.vstack([jacp[:, DOF], jacr[:, DOF]])
        dq = J.T @ np.linalg.solve(J @ J.T + 0.04 * np.eye(6), err6)
        q = q + np.clip(dq, -0.2, 0.2)
    return q, np.linalg.norm(pos_err)


def step_to(q_arm, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        t = (s + 1) / n
        d.ctrl[:5] = cur + (q_arm - cur) * t; d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def pad_contacts():
    """패드별 큐브 접촉 수와 firm 판정(양 패드 동시 접촉)."""
    nf = nm = 0
    for c in range(d.ncon):
        g1, g2 = d.contact[c].geom1, d.contact[c].geom2
        if CUBE_GEOM not in (g1, g2):
            continue
        other = g1 if g2 == CUBE_GEOM else g2
        if other == FIXED_PAD:
            nf += 1
        elif other == MOVING_PAD:
            nm += 1
    return nf, nm


def graded_close(z_grasp, verbose=False):
    """점진 닫힘: APPROACH_GRIP→CLOSE_Q 를 여러 step 에 나눠 닫으며 매 step 큐브 추종(재중심).
    팔 xy 는 큐브 현위치로 부드럽게 추종해 호로 밀린 큐브를 다시 패드 사이로. CLOSE_Q 도달 후 hold.
    """
    seed = d.ctrl[:5].copy()
    n_micro = 50
    g0 = float(d.qpos[GQA])
    for k in range(n_micro):
        t = (k + 1) / n_micro
        grip = g0 + (CLOSE_Q - g0) * t
        cube = d.body("cube").xpos.copy()
        target = np.array([cube[0], cube[1], z_grasp])  # 큐브 현 xy 추종
        q_arm, _ = ik_tcp(target, seed); seed = q_arm
        cur = d.ctrl[:5].copy()
        for s in range(5):
            d.ctrl[:5] = cur + (q_arm - cur) * (s + 1) / 5
            d.ctrl[5] = grip
            mujoco.mj_step(m, d)
    for _ in range(80):
        d.ctrl[5] = CLOSE_Q; mujoco.mj_step(m, d)
    nf, nm = pad_contacts()
    if verbose:
        print(f"      [close] fixed_pad={nf} moving_pad={nm} grip_q={float(d.qpos[GQA]):+.3f} "
              f"cube={d.body('cube').xpos.round(3).tolist()}")
    return nf > 0 and nm > 0


def closed_loop_lift(z0, verbose=False):
    """closed-loop 들기: 큐브를 위+베이스쪽(LIFT_X)으로 당기는 곡선 경로. 매 step 큐브추종.
    팔 도달한계(x=0.13 에서 z≈+36mm) 때문에 x 를 당겨야 +40mm 도달.
    """
    n = 550
    seed = d.ctrl[:5].copy()
    maxlift = 0.0
    cube0_xy = d.body("cube").xpos[:2].copy()
    for s in range(n):
        t = min(1.0, (s + 1) / 420)
        cube = d.body("cube").xpos.copy()
        # 목표: x 는 cube0→LIFT_X 로 당김, y 는 큐브 현 y 유지, z 는 z0→z0+0.045 상승
        tx = cube0_xy[0] + (LIFT_X - cube0_xy[0]) * t
        tz = z0 + 0.065 * t
        target = np.array([tx, cube[1], tz])
        q_arm, _ = ik_tcp(target, seed); seed = q_arm
        cur = d.ctrl[:5].copy()
        d.ctrl[:5] = cur + (q_arm - cur) * 0.5
        d.ctrl[5] = CLOSE_Q
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    if verbose:
        nf, nm = pad_contacts()
        print(f"      [lift] maxlift={maxlift*1000:.1f}mm fixed_pad={nf} moving_pad={nm} "
              f"cube={d.body('cube').xpos.round(3).tolist()}")
    return maxlift


def reopen(z0):
    cube = d.body("cube").xpos.copy()
    q_up, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.06]), d.ctrl[:5].copy())
    step_to(q_up, GRIP_OPEN, 100)


def attempt(z0, verbose=False):
    cube = d.body("cube").xpos.copy()
    q_pre, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), d.ctrl[:5].copy())
    step_to(q_pre, GRIP_OPEN, 120)
    cube = d.body("cube").xpos.copy()
    q_grasp, e_g = ik_tcp(np.array([cube[0], cube[1], z0]), q_pre)
    step_to(q_grasp, APPROACH_GRIP, 130)
    if verbose:
        nf, nm = pad_contacts()
        print(f"    접근후 TCP={tcp_pos(d).round(3).tolist()} cube={d.body('cube').xpos.round(3).tolist()} "
              f"pad(f{nf},m{nm}) ik={e_g*1000:.1f}mm")
    firm = graded_close(z0, verbose)
    return firm


def episode(cube_xy, verbose=False):
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + HALF]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = GRIP_OPEN
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    z0 = float(d.body("cube").xpos[2])

    tries = 0; firm = False
    for r in range(RETRY + 1):
        tries = r + 1
        firm = attempt(z0, verbose=(verbose and r == 0))
        if firm:
            break
        if verbose:
            print(f"    [재시도 {r}] firm grasp 실패 → 재개방")
        reopen(z0)

    maxlift = closed_loop_lift(z0, verbose=verbose)
    return maxlift, pad_contacts(), tries


POSITIONS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
             (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]

print(f"CL grasp: cube={CUBE_MM:.0f}mm FORCE={FORCE or 'XML1.5'} CLOSE_Q={CLOSE_Q} "
      f"LIFT_X={LIFT_X} RETRY={RETRY}  scene=pads")
res = []; lifts = []
for k, xy in enumerate(POSITIONS):
    ml, (nf, nm), tries = episode(xy, verbose=(k == 0))
    ok = ml >= 0.04
    res.append(ok); lifts.append(ml * 1000)
    print(f"  cube{xy}: lift={ml*1000:5.1f}mm pad(f{nf},m{nm}) 시도={tries} {'성공' if ok else '실패'}")
print(f"성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%  중앙값lift={np.median(lifts):.1f}mm")
