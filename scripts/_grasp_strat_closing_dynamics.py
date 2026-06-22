"""전략 5 — closing 동역학 튜닝(잼 해소).

검증된 IK/기하(_grasp_test_v2.py)를 재사용. 닫힘이 grip_q≈1.03 에서 잼하는 걸
다음 노브로 해소 시도:
  - GRIP_FORCE : 그리퍼 액추에이터(인덱스 5) forcerange (집는 토크)
  - CLOSE_STEPS: 닫힘 구동 step 수
  - SETTLE     : 닫은 뒤 lift 전 settle step 수
  - GRIP_OPEN  : 접근시 벌림 폭 (큐브가 갭에 확실히 들어오게)
  - GRIP_CLOSE : 닫힘 ctrl 목표값

사용:
  python _grasp_strat_closing_dynamics.py diag        # 진단 1회(왜 잼하나)
  python _grasp_strat_closing_dynamics.py sweep        # 노브 sweep
  python _grasp_strat_closing_dynamics.py eval <GO> <GC> <TCPZ> <GF> <CS> <ST> <ARMF>  # 단일조합 8위치
"""
import mujoco, numpy as np, sys, itertools

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m); d_ik = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
ARM = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
DOF = [m.jnt_dofadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
QAD = [m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ARM]
CJ = nid(mujoco.mjtObj.mjOBJ_JOINT, "cube_joint"); CADR = m.jnt_qposadr[CJ]
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GRIPQ = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
JAWG = [i for i in range(m.ngeom) if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]
MOVG = [i for i in range(m.ngeom) if m.geom_bodyid[i] == JBID and m.geom_group[i] == 3]
FIXG = [i for i in range(m.ngeom) if m.geom_bodyid[i] == GBID and m.geom_group[i] == 3]
CUBE_GEOM = [i for i in range(m.ngeom) if m.geom_bodyid[i] == nid(mujoco.mjtObj.mjOBJ_BODY, "cube")]
TABLE_TOP = 0.16

POS = [(0.13, 0.0), (0.13, 0.02), (0.11, -0.02), (0.15, 0.01),
       (0.12, 0.015), (0.14, -0.015), (0.12, -0.01), (0.15, -0.02)]


def tcp_pos(dd, tcp_z, tcp_x=0.0):
    return dd.xpos[GBID] + dd.xmat[GBID].reshape(3, 3) @ np.array([tcp_x, 0., tcp_z])


def ik_tcp(target, seed, grip_open, tcp_z, tcp_x=0.0):
    q = np.array(seed, float); UP = np.array([0., 0., 1.]); pos_err = np.ones(3)
    TCP_LOCAL = np.array([tcp_x, 0., tcp_z])
    for _ in range(600):
        for i, a in enumerate(QAD):
            d_ik.qpos[a] = q[i]
        d_ik.ctrl[5] = grip_open
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


def jaw_cube_contacts():
    n = 0
    for c in range(d.ncon):
        g1, g2 = d.contact[c].geom1, d.contact[c].geom2
        if (g1 in JAWG and g2 in CUBE_GEOM) or (g2 in JAWG and g1 in CUBE_GEOM):
            n += 1
    return n


def contact_breakdown():
    """가동패드-큐브 / 고정패드-큐브 접촉 수."""
    nm = nf = 0
    for c in range(d.ncon):
        g1, g2 = d.contact[c].geom1, d.contact[c].geom2
        pair = {g1, g2}
        if pair & set(CUBE_GEOM):
            if pair & set(MOVG):
                nm += 1
            if pair & set(FIXG):
                nf += 1
    return nm, nf


def drive(q_arm, grip, n):
    cur = d.ctrl[:5].copy()
    for s in range(n):
        t = (s + 1) / n
        d.ctrl[:5] = cur + (q_arm - cur) * t; d.ctrl[5] = grip
        mujoco.mj_step(m, d)


def set_forces(arm_f, grip_f):
    for ai in range(5):
        m.actuator_forcerange[ai] = [-arm_f, arm_f]
    m.actuator_forcerange[5] = [-grip_f, grip_f]


def pad_x(dd, gi):
    """패드 geom 월드중심 x (개폐축 ≈ 월드 x)."""
    c = dd.geom_xpos[gi] + dd.geom_xmat[gi].reshape(3, 3) @ m.geom_aabb[gi, :3]
    return float(c[0])


def episode(cube_xy, grip_open, grip_close, tcp_z, corral_f, close_steps, settle,
            arm_f, grasp_dz=0.0, tcp_x=0.0, hold_f=None, hold_steps=200,
            lift_steps=250, hold_dq=0.15, verbose=False):
    """2단계 닫힘:
      phase1 (corral): 저토크(corral_f)로 천천히 닫아 자유 큐브를 고정패드에 코너링(쳐냄 방지).
      phase2 (clamp) : 그리퍼 토크를 hold_f 로 올려 확실히 압착, settle 후 lift.
    """
    if hold_f is None:
        hold_f = corral_f
    set_forces(arm_f, corral_f)
    mujoco.mj_resetData(m, d)
    d.qpos[CADR:CADR + 3] = [cube_xy[0], cube_xy[1], TABLE_TOP + 0.015]
    d.qpos[CADR + 3:CADR + 7] = [1, 0, 0, 0]
    d.ctrl[:5] = 0; d.ctrl[5] = grip_open
    mujoco.mj_forward(m, d)
    for _ in range(100):
        mujoco.mj_step(m, d)
    cube = d.body("cube").xpos.copy(); z0 = float(cube[2])
    q_pre, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.07]), np.zeros(5), grip_open, tcp_z, tcp_x)
    q_grasp, e_g = ik_tcp(np.array([cube[0], cube[1], z0 + grasp_dz]), np.zeros(5), grip_open, tcp_z, tcp_x)
    q_lift, _ = ik_tcp(np.array([cube[0], cube[1], z0 + 0.10]), np.zeros(5), grip_open, tcp_z, tcp_x)
    drive(q_pre, grip_open, 150)
    drive(q_grasp, grip_open, 150)
    cube_pre = d.body("cube").xpos.copy()
    if verbose:
        print(f"    접근후 cube={cube_pre.round(3).tolist()} TCP={tcp_pos(d,tcp_z,tcp_x).round(3).tolist()} "
              f"고정패드x={pad_x(d,29):.3f} 가동패드x={pad_x(d,31):.3f}")
    # phase1: 저토크 천천히 닫기 (코너링) — 큐브가 고정패드에 코너링되며 가동조가 압착하는 각에서 멈춤
    drive(q_grasp, grip_close, close_steps)
    nm1, nf1 = contact_breakdown()
    hold_q = float(d.qpos[GRIPQ])  # 코너링이 멈춘 핀치 각(큐브가 막아 더 못 닫힘)
    # phase2: 토크 상향, 그러나 더 닫으라 명령하지 않고 '핀치 각 + 약간 더'를 목표로 유지(과회전 방지)
    m.actuator_forcerange[5] = [-hold_f, hold_f]
    hold_ctrl = hold_q - hold_dq  # 핀치보다 살짝만 더 조이게(큐브가 막으므로 토크로 압착)
    for _ in range(hold_steps):
        d.ctrl[:5] = q_grasp; d.ctrl[5] = hold_ctrl
        mujoco.mj_step(m, d)
    for _ in range(settle):
        d.ctrl[:5] = q_grasp; d.ctrl[5] = hold_ctrl
        mujoco.mj_step(m, d)
    gq_closed = float(d.qpos[GRIPQ])
    nm, nf = contact_breakdown()
    cube_closed = d.body("cube").xpos.copy()
    if verbose:
        print(f"    코너링후 mov={nm1} fix={nf1} / 압착후 grip_q={gq_closed:.3f} mov={nm} fix={nf} "
              f"cube={cube_closed.round(3).tolist()} cube이동={(cube_closed-cube_pre).round(3).tolist()}")
    # lift (압착토크/핀치각 유지) — lift_steps 클수록 천천히(관성으로 그립 깨짐 방지)
    maxlift = 0.0; cur = d.ctrl[:5].copy()
    for s in range(lift_steps):
        t = (s + 1) / lift_steps
        d.ctrl[:5] = cur + (q_lift - cur) * t; d.ctrl[5] = hold_ctrl
        mujoco.mj_step(m, d)
        maxlift = max(maxlift, float(d.body("cube").xpos[2]) - z0)
    final_lift = float(d.body("cube").xpos[2]) - z0
    return dict(maxlift=maxlift, final_lift=final_lift, ik=e_g, gq=gq_closed,
                nm=nm, nf=nf, ok=final_lift >= 0.04)


def run_set(grip_open, grip_close, tcp_z, corral_f, close_steps, settle, arm_f,
            grasp_dz=0.0, tcp_x=0.0, hold_f=None, hold_steps=200,
            lift_steps=250, hold_dq=0.15, label="", verbose0=False):
    res = []
    for k, xy in enumerate(POS):
        r = episode(xy, grip_open, grip_close, tcp_z, corral_f, close_steps, settle,
                    arm_f, grasp_dz, tcp_x, hold_f=hold_f, hold_steps=hold_steps,
                    lift_steps=lift_steps, hold_dq=hold_dq, verbose=(verbose0 and k == 0))
        res.append(r)
    n_ok = sum(r["ok"] for r in res)
    med_lift = float(np.median([r["final_lift"] for r in res])) * 1000
    med_gq = float(np.median([r["gq"] for r in res]))
    return n_ok, res, med_lift, med_gq


# ---------------- DIAG ----------------
def diag():
    print("=== 진단A: 좁은 GRIP_OPEN 으로 접근(가동조 호 최소화). tcp_x sweep ===")
    print("  gap_x: q=0.23→42mm, q=-0.09→30mm. 큐브30mm → OPEN≈0.0~0.3 로 접근")
    for go in (0.4, 0.2, 0.0):
        for tx in (0.0, 0.015, 0.025):
            r = episode(POS[0], go, -2.0, -0.085, 8.0, 250, 150, 6.0, tcp_x=tx, verbose=False)
            print(f"  OPEN={go} tcp_x={tx}: grip_q={r['gq']:.2f} mov={r['nm']} fix={r['nf']} lift={r['final_lift']*1000:6.1f}mm ok={r['ok']}")
    print("\n  상세(OPEN=0.2 tcp_x=0.015):")
    episode(POS[0], 0.2, -2.0, -0.085, 8.0, 250, 150, 6.0, tcp_x=0.015, verbose=True)


# ---------------- SWEEP ----------------
def sweep():
    print("=== 전략5 sweep (±6Nm 메커니즘 격리) ===")
    print("핵심: 가동조가 큐브를 고정패드에 압착(mov접촉≥1)하게 만드는 게 목표.\n")

    # 1단계: tcp_x x grasp_dz 광역 (큐브를 고정패드에 backing + 적정 깊이)
    print("[1] tcp_x x grasp_dz 광역 (OPEN=1.5 close=300 settle=200 grip_f=10 arm=6 GC=-2.5)")
    best = None
    for tx in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05):
        for dz in (0.0, -0.008, -0.016):
            n_ok, res, ml, gq = run_set(1.5, -2.5, -0.085, 10.0, 300, 200, 6.0, grasp_dz=dz, tcp_x=tx)
            nm_tot = sum(r["nm"] for r in res)
            print(f"  tcp_x={tx:+.2f} grasp_dz={dz:+.3f}: {n_ok}/8 med_lift={ml:6.1f}mm mov접촉합={nm_tot}")
            sc = (n_ok, nm_tot, ml)
            if best is None or sc > best[0]:
                best = (sc, dict(tx=tx, dz=dz))
    b1 = best[1]
    print(f"\n  → 1단계 최선: tcp_x={b1['tx']} grasp_dz={b1['dz']}")

    # 2단계: GRIP_OPEN x GRIP_CLOSE (접근 폭, 닫힘 목표)
    print(f"\n[2] GRIP_OPEN x GRIP_CLOSE (tcp_x={b1['tx']} grasp_dz={b1['dz']})")
    best2 = None
    for go in (1.0, 1.5, 2.0):
        for gc in (-2.0, -2.5, -3.0):
            n_ok, res, ml, gq = run_set(go, gc, -0.085, 10.0, 300, 200, 6.0, grasp_dz=b1['dz'], tcp_x=b1['tx'])
            nm_tot = sum(r["nm"] for r in res)
            print(f"  OPEN={go} CLOSE={gc}: {n_ok}/8 med_lift={ml:6.1f}mm mov접촉합={nm_tot}")
            if best2 is None or (n_ok, nm_tot, ml) > best2[0]:
                best2 = ((n_ok, nm_tot, ml), dict(go=go, gc=gc))
    b2 = best2[1]
    print(f"\n  → 2단계 최선: OPEN={b2['go']} CLOSE={b2['gc']}")

    # 3단계: grip_f x close_steps x settle
    print(f"\n[3] grip_f x close_steps x settle (OPEN={b2['go']} CLOSE={b2['gc']} tcp_x={b1['tx']} grasp_dz={b1['dz']})")
    best3 = None
    for gf, cs, st in itertools.product([6.0, 10.0, 16.0], [200, 400], [150, 350]):
        n_ok, res, ml, gq = run_set(b2['go'], b2['gc'], -0.085, gf, cs, st, 6.0,
                                    grasp_dz=b1['dz'], tcp_x=b1['tx'])
        nm_tot = sum(r["nm"] for r in res)
        print(f"  grip_f={gf} close={cs} settle={st}: {n_ok}/8 med_lift={ml:6.1f}mm mov접촉합={nm_tot}")
        if best3 is None or (n_ok, nm_tot, ml) > best3[0]:
            best3 = ((n_ok, nm_tot, ml), dict(gf=gf, cs=cs, st=st))
    b3 = best3[1]
    print(f"\n  → 3단계 최선: grip_f={b3['gf']} close={b3['cs']} settle={b3['st']}")

    P = dict(go=b2['go'], gc=b2['gc'], tz=-0.085, gf=b3['gf'], cs=b3['cs'], st=b3['st'],
             dz=b1['dz'], tx=b1['tx'])
    final_report(P)


def final_report(P=None):
    # 검증된 최선 closing-dynamics 설정(저토크 2단계 corral + 핀치각 유지)
    if P is None:
        # 검증된 최선: 단일 저토크 phase(hold_f=corral_f=1.0), 핀치보다 0.1만 더 조임, 표준 lift
        P = dict(go=1.5, gc=-2.5, tz=-0.085, tx=0.01, dz=-0.008,
                 cf=1.0, cs=1200, st=300, hf=1.0, hs=300, ls=250, hdq=0.1)
    print(f"\n=== 최선조합 최종측정 (저토크 2단계 corral) ===")
    print(f"  OPEN={P['go']} CLOSE={P['gc']} TCP_Z={P['tz']} tcp_x={P['tx']} grasp_dz={P['dz']} "
          f"corral_f={P['cf']} close_steps={P['cs']} hold_f={P['hf']} hold_steps={P['hs']} settle={P['st']}")
    out = {}
    for arm_f, tag in ((6.0, "±6Nm 격리"), (1.5, "±1.5Nm 실토크")):
        n_ok, res, ml, gq = run_set(P['go'], P['gc'], P['tz'], P['cf'], P['cs'], P['st'], arm_f,
                                    grasp_dz=P['dz'], tcp_x=P['tx'], hold_f=P['hf'], hold_steps=P['hs'],
                                    lift_steps=P['ls'], hold_dq=P['hdq'], verbose0=(arm_f == 6.0))
        nm_tot = sum(r["nm"] for r in res)
        print(f"\n  [{tag}] {n_ok}/8 = {100*n_ok/8:.0f}%  med_lift={ml:.1f}mm mov접촉합={nm_tot}")
        for xy, r in zip(POS, res):
            print(f"    {xy}: lift={r['final_lift']*1000:6.1f}mm gq={r['gq']:.2f} mov={r['nm']} fix={r['nf']} {'OK' if r['ok'] else '--'}")
        out[arm_f] = n_ok
    return out


def eval_one():
    go, gc, tz, gf, cs, st, af = (float(x) for x in sys.argv[2:9])
    n_ok, res, med_lift, med_gq = run_set(go, gc, tz, gf, int(cs), int(st), af, verbose0=True)
    print(f"{n_ok}/8 med_lift={med_lift:.1f}mm med_gq={med_gq:.2f}")
    for xy, r in zip(POS, res):
        print(f"  {xy}: lift={r['final_lift']*1000:5.1f}mm gq={r['gq']:.2f} mov={r['nm']} fix={r['nf']} {'OK' if r['ok'] else '--'}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "final"
    if mode == "diag":
        diag()
    elif mode == "eval":
        eval_one()
    elif mode == "sweep":
        sweep()
    else:
        final_report()
