"""전략 6 — 수직 하강 접근 + 개폐축 정렬 추가 제약 + TCP x-오프셋.

핵심 진단(geom probe + v2 결과 종합):
- 그리퍼 개폐축 ≈ body-x. 고정패드(geom29) 몸체로컬중심 x≈-0.016(half 0.027),
  가동패드(geom31) 몸체로컬중심 x≈+0.018(half 0.010). 따라서 실제 갭 중앙은
  body-x=0 이 아니라 +0.008~+0.010 부근. v2 의 TCP_LOCAL=[0,0,z]는 큐브를
  고정패드 쪽으로 ~11mm 치우치게 했다(증상과 일치).
- 대책1(TCP x-오프셋): TCP_LOCAL=[TCP_X,0,TCP_Z]. TCP_X로 큐브를 갭 중앙에 안착.
- 대책2(수직 하강): pre→grasp 를 큐브 바로 위에서 TCP xy 고정, z만 하강시켜
  큐브를 옆으로 밀지 않게.
- 대책3(개폐축 정렬): IK에 그리퍼 body-x 축을 월드 +y로 정렬하는 제약 추가
  → 매 위치에서 개폐 방향 일관(wrist_roll 자유도 소비). 위치3+z정렬1+x정렬1=5/5.

사용: python _grasp_strat_approach_vertical.py [TCP_X] [TCP_Z] [FORCE] [GRASP_DZ] [GRIP_CLOSE]
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
GRIPQ = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TABLE_TOP = 0.16

# 파라미터
TCP_X = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
TCP_Z = float(sys.argv[2]) if len(sys.argv) > 2 else -0.085
FORCE = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
GRASP_DZ = float(sys.argv[4]) if len(sys.argv) > 4 else 0.020
GRIP_CLOSE = float(sys.argv[5]) if len(sys.argv) > 5 else -1.5
# 그리퍼 액추에이터(인덱스5) 힘. 0이면 XML기본(1.5). 메커니즘격리 시 팔과 함께 키운다.
GRIP_FORCE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
GRIP_OPEN = 1.5

# 개폐축(body-x)을 정렬할 월드 목표축. +y 로 고정.
OPEN_AXIS_WORLD = np.array([0.0, 1.0, 0.0])

POSITIONS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
             (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]


def make_tcp_local():
    return np.array([TCP_X, 0.0, TCP_Z])


def tcp_pos(dd, tcp_local):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ tcp_local


def ik_tcp(target, seed, tcp_local):
    """TCP→target(위치3) + body z축→월드+z(정렬1) + body x축→월드 OPEN_AXIS(정렬1).

    정렬은 각각 1성분만 쓰는 게 아니라 cross 로 2벡터지만, z정렬+x정렬을 함께 주면
    회전이 완전 결정된다(과제약이 아니라 5DOF에 맞게 damped LS로 흡수). err6는
    pos3 + (z정렬 1축 가중) 으로 구성해 안정화.
    """
    q = np.array(seed, float)
    UP = np.array([0., 0., 1.])
    pos_err = np.ones(3)
    for _ in range(800):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = GRIP_OPEN
        mujoco.mj_forward(m, d_ik)
        R = d_ik.xmat[GBID].reshape(3, 3)
        tcp = d_ik.xpos[GBID] + R @ tcp_local
        z_local = R[:, 2]
        x_local = R[:, 0]
        pos_err = target - tcp
        # z축을 월드+z로 (손가락 아래), x축을 OPEN_AXIS_WORLD 로.
        rot_err_z = np.cross(z_local, UP)
        rot_err_x = np.cross(x_local, OPEN_AXIS_WORLD)
        # 두 회전제약 합성. cross 합은 회전속도 형태로 잘 합쳐짐.
        rot_err = rot_err_z + rot_err_x
        err6 = np.concatenate([pos_err, 0.6 * rot_err])
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
    nfix = nmov = 0
    for c in range(d.ncon):
        g1, g2 = d.contact[c].geom1, d.contact[c].geom2
        cube_hit = (g1 in CUBE_GEOM) or (g2 in CUBE_GEOM)
        if not cube_hit:
            continue
        other = g1 if g2 in CUBE_GEOM else g2
        if other in JAWG:
            if m.geom_bodyid[other] == JBID:
                nmov += 1
            else:
                nfix += 1
    return nfix, nmov


def episode(cube_xy, tcp_local, verbose=False):
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
    cx, cy = float(cube[0]), float(cube[1])

    # 수직 하강 접근: pre/grasp/lift 모두 동일 xy(=큐브 중심), z만 변경.
    q_pre, e_pre = ik_tcp(np.array([cx, cy, z0 + 0.07]), np.zeros(5), tcp_local)
    q_grasp, e_g = ik_tcp(np.array([cx, cy, z0 + GRASP_DZ]), q_pre, tcp_local)
    q_lift, _ = ik_tcp(np.array([cx, cy, z0 + 0.10]), q_grasp, tcp_local)

    drive(q_pre, GRIP_OPEN, 150)
    # 순수 수직 하강: pre→grasp 사이 보간이지만 xy 동일하므로 사실상 z만 내려감.
    drive(q_grasp, GRIP_OPEN, 180)

    if verbose:
        R = d.xmat[GBID].reshape(3, 3)
        fixed_c = d.geom_xpos[29] + R @ m.geom_aabb[29, :3]
        moving_c = d.geom_xpos[31] + R @ m.geom_aabb[31, :3]
        cb = d.body('cube').xpos
        nf, nm = jaw_cube_contacts()
        print(f"    접근후 TCP={tcp_pos(d, tcp_local).round(3).tolist()} cube={cb.round(3).tolist()} 접촉(고정{nf}/가동{nm})")
        print(f"      개폐축 body-x(월드)={R[:,0].round(2).tolist()} body+z(월드)={R[:,2].round(2).tolist()}")
        print(f"      cube-고정패드={(cb-fixed_c).round(3).tolist()}  cube-가동패드={(cb-moving_c).round(3).tolist()}")

    # 닫기: 그리퍼는 무부하에서도 +1.5→-1.5 풀스윙에 ~400스텝 필요. 충분히 준다.
    drive(q_grasp, GRIP_CLOSE, 450)
    # 닫힌 상태로 잠깐 정착(그립 안정화)
    for _ in range(80):
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
    grip_q = float(d.qpos[GRIPQ])
    nf, nm = jaw_cube_contacts()
    if verbose:
        print(f"    닫음후 접촉(고정{nf}/가동{nm}) grip_q={grip_q:.3f} cube={d.body('cube').xpos.round(3).tolist()}")

    # 들어올리기: 천천히(인덱스 부하로 그립 깨지지 않게). 400스텝.
    maxlift = 0.0
    cur = d.ctrl[:5].copy()
    for s in range(400):
        t = (s + 1) / 400
        d.ctrl[:5] = cur + (q_lift - cur) * t
        d.ctrl[5] = GRIP_CLOSE
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    final_lift = float(d.body("cube").xpos[2]) - z0
    return dict(maxlift=maxlift, final_lift=final_lift, e_g=e_g,
                grip_q=grip_q, nfix=nf, nmov=nm, e_pre=e_pre)


def run(force, tcp_local, grip_force=0.0, verbose_first=False):
    # 토크 설정: 팔 5관절
    for ai in range(5):
        m.actuator_forcerange[ai] = [-force, force]
    # 그리퍼 액추에이터(인덱스5) 힘. grip_force>0 이면 덮어쓰기.
    if grip_force > 0:
        m.actuator_forcerange[5] = [-grip_force, grip_force]
    res = []
    detail = []
    for k, xy in enumerate(POSITIONS):
        r = episode(xy, tcp_local, verbose=(verbose_first and k == 0))
        ok = r["maxlift"] >= 0.04
        res.append(ok)
        detail.append(r)
    return res, detail


if __name__ == "__main__":
    tcp_local = make_tcp_local()
    print(f"=== 전략6 수직하강+개폐축정렬  TCP_LOCAL={tcp_local.round(4).tolist()} "
          f"GRASP_DZ={GRASP_DZ} GRIP_CLOSE={GRIP_CLOSE} GRIP_FORCE={GRIP_FORCE or 'XML기본'} ===")
    # 메커니즘격리(±6Nm): 팔과 그리퍼 모두 6Nm. 실토크(±1.5Nm): 둘 다 XML기본 1.5.
    for force in (6.0, 1.5):
        gf = force if GRIP_FORCE == 0.0 else GRIP_FORCE
        # 실토크 측정에서는 그리퍼도 1.5 그대로(=XML기본). gf=force=1.5 와 동일.
        res, detail = run(force, tcp_local, grip_force=gf, verbose_first=(force == 6.0))
        print(f"\n[FORCE=±{force}Nm (그리퍼힘=±{gf}Nm)]")
        for xy, ok, r in zip(POSITIONS, res, detail):
            print(f"  cube{xy}: max_lift={r['maxlift']*1000:5.1f}mm final={r['final_lift']*1000:5.1f}mm "
                  f"grip_q={r['grip_q']:.2f} 접촉(고{r['nfix']}/가{r['nmov']}) "
                  f"ik={r['e_g']*1000:.1f}mm {'성공' if ok else '실패'}")
        print(f"  성공률: {sum(res)}/{len(res)} = {100*sum(res)/len(res):.0f}%")
