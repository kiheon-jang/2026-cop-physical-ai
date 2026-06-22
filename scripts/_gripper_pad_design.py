"""손가락 패드 콜리전 박스 설계용 실측 — 고정/가동 손가락의 그립 면을 각 body 로컬에서 추출.

목적: 풀메시 콜리전(글랜싱 접촉) 대신 평평한 패드 박스를 각 손가락 안쪽면에 붙이기 위해,
fixed finger(geom29, gripper body)와 moving jaw(geom31, moving_jaw body)의 그립 영역
AABB 를 각자 body 로컬 프레임에서 측정해 박스 pos/size 를 출력.
"""
import mujoco, numpy as np

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
d.qpos[:] = 0
mujoco.mj_forward(m, d)


def verts_in_body(geom_i, bid):
    did = m.geom_dataid[geom_i]; a = m.mesh_vertadr[did]; n = m.mesh_vertnum[did]
    v = m.mesh_vert[a:a + n].reshape(-1, 3).astype(np.float64)
    v = v[np.isfinite(v).all(1) & (np.abs(v) < 1.0).all(1)]
    gp = d.geom_xpos[geom_i]; gR = d.geom_xmat[geom_i].reshape(3, 3)
    bx = d.xpos[bid]; bR = d.xmat[bid].reshape(3, 3)
    world = (gR @ v.T).T + gp
    return (bR.T @ (world - bx).T).T


def report(name, geom_i, bid):
    vb = verts_in_body(geom_i, bid)
    lo = vb.min(0); hi = vb.max(0)
    print(f"\n[{name}] geom{geom_i} in body '{m.body(bid).name}' 로컬 AABB:")
    print(f"   x[{lo[0]:+.4f},{hi[0]:+.4f}] y[{lo[1]:+.4f},{hi[1]:+.4f}] z[{lo[2]:+.4f},{hi[2]:+.4f}]  (mm폭: {((hi-lo)*1000).round(1).tolist()})")
    return vb, lo, hi


# 그리퍼 body 프레임에서 두 손가락의 위치관계(개폐축=x, 손가락=-z 방향)를 먼저 확인
print("== 그리퍼 body 프레임 기준 (개폐축 x, 손가락 -z, 그립밴드 z≈-0.09) ==")
fb, flo, fhi = report("고정손가락(wrist_roll_follower)", 29, GBID)   # gripper body
# moving jaw 는 자기 body 프레임에서
mj_own, mlo, mhi = report("가동조(moving_jaw) [own frame]", 31, JBID)

# 그립밴드(z≈-0.09 부근, gripper 프레임)에서 고정손가락 안쪽면(+x 최대) 추출
band = fb[(fb[:, 2] > -0.105) & (fb[:, 2] < -0.060)]
if len(band):
    print(f"\n고정손가락 그립밴드(z∈[-0.105,-0.060]) gripper로컬: x최대(안쪽면)={band[:,0].max():+.4f}  y[{band[:,1].min():+.4f},{band[:,1].max():+.4f}]")
    fy_lo, fy_hi = band[:, 1].min(), band[:, 1].max()
    fx_inner = band[:, 0].max()
    print(f"  → 고정패드 제안(gripper body): pos≈[{fx_inner-0.004:+.4f}, {0.5*(fy_lo+fy_hi):+.4f}, -0.085], size≈[0.004, {0.5*(fy_hi-fy_lo):.4f}, 0.012]")

# 가동조: 자기 프레임에서 그립면(고정손가락을 향하는 면) 추출.
# 가동조를 닫힘자세(q≈0.195)에 두고 gripper 프레임 x 최소면을 본 뒤 own 프레임으로 역산.
d2 = mujoco.MjData(m)
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
d2.qpos[:] = 0; d2.qpos[GQA] = 0.195
mujoco.mj_forward(m, d2)
did = m.geom_dataid[31]; a = m.mesh_vertadr[did]; nn = m.mesh_vertnum[did]
vv = m.mesh_vert[a:a + nn].reshape(-1, 3).astype(np.float64)
vv = vv[np.isfinite(vv).all(1) & (np.abs(vv) < 1.0).all(1)]
gR31 = d2.geom_xmat[31].reshape(3, 3); gp31 = d2.geom_xpos[31]
world = (gR31 @ vv.T).T + gp31
gx = d2.xpos[GBID]; gRb = d2.xmat[GBID].reshape(3, 3)
in_grip = (gRb.T @ (world - gx).T).T
mband = in_grip[(in_grip[:, 2] > -0.105) & (in_grip[:, 2] < -0.060)]
if len(mband):
    print(f"\n가동조 그립밴드(닫힘 q=0.195, gripper로컬): x최소(안쪽면)={mband[:,0].min():+.4f}  y[{mband[:,1].min():+.4f},{mband[:,1].max():+.4f}]")
# own 프레임으로: 가동조 그립면을 moving_jaw 로컬로
bxj = d2.xpos[JBID]; bRj = d2.xmat[JBID].reshape(3, 3)
in_jaw = (bRj.T @ (world - bxj).T).T
jband = in_jaw[(in_grip[:, 2] > -0.105) & (in_grip[:, 2] < -0.060)]
if len(jband):
    lo = jband.min(0); hi = jband.max(0)
    print(f"가동조 그립밴드 moving_jaw로컬 AABB: x[{lo[0]:+.4f},{hi[0]:+.4f}] y[{lo[1]:+.4f},{hi[1]:+.4f}] z[{lo[2]:+.4f},{hi[2]:+.4f}]")
    print(f"  → 가동패드 제안(moving_jaw body): 이 AABB의 고정손가락 향하는 면에 thin box")
