"""스톡 SO-101 그리퍼(공식 MJCF)의 실제 최대 개구폭 측정 — 50mm 큐브가 기하적으로 잡히는가."""
import mujoco, numpy as np

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")  # 스톡 팔(so101_new_calib)+작업대
d = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
GQA = m.jnt_qposadr[nid(mujoco.mjtObj.mjOBJ_JOINT, "gripper")]


def verts_world(geom_i, dd):
    did = m.geom_dataid[geom_i]; a = m.mesh_vertadr[did]; n = m.mesh_vertnum[did]
    v = m.mesh_vert[a:a + n].reshape(-1, 3).astype(np.float64)
    v = v[np.isfinite(v).all(1) & (np.abs(v) < 1.0).all(1)]
    return (dd.geom_xmat[geom_i].reshape(3, 3) @ v.T).T + dd.geom_xpos[geom_i]


# 고정 손가락 geom 29(follower), 가동 geom 31(moving_jaw)
FIXED, MOVING = 29, 31
gx = lambda: d.xpos[GBID]; gR = lambda: d.xmat[GBID].reshape(3, 3)


def gap_at(qg):
    """gripper qpos=qg 에서 손가락 끝(그립밴드) 안쪽면 사이 개구폭(개폐축=gripper x)."""
    d.qpos[:] = 0; d.qpos[GQA] = qg
    mujoco.mj_forward(m, d)
    R = gR(); o = gx()
    def local(gi):
        w = verts_world(gi, d)
        return (R.T @ (w - o).T).T
    fb = local(FIXED); mb = local(MOVING)
    # 그립밴드(손가락 끝, gripper z ∈ [-0.105,-0.060])
    band = lambda a: a[(a[:, 2] > -0.105) & (a[:, 2] < -0.060)]
    fbb, mbb = band(fb), band(mb)
    if len(fbb) < 3 or len(mbb) < 3:
        return None
    return mbb[:, 0].min() - fbb[:, 0].max()   # 가동 안쪽면 - 고정 안쪽면


# 개구폭은 qpos 단조. 관절 범위 훑어 최대 개구 찾기
qs = np.linspace(-0.5, 1.5, 60)
gaps = [(q, gap_at(q)) for q in qs]
gaps = [(q, g) for q, g in gaps if g is not None]
gmax = max(g for _, g in gaps); gmin = min(g for _, g in gaps)
qopen = [q for q, g in gaps if g == gmax][0]
print(f"스톡 SO-101 그리퍼 (공식 MJCF) 손가락끝 개구폭:")
print(f"  최대 개구 = {gmax*1000:.1f}mm  (gripper qpos={qopen:.2f})")
print(f"  최소(닫힘) = {gmin*1000:.1f}mm")
print()
print(f"50mm 큐브: 개구 대비 {50/(gmax*1000)*100:.0f}% 점유 (여유 편당 {(gmax*1000-50)/2:.1f}mm)")
print(f"30mm 큐브: 개구 대비 {30/(gmax*1000)*100:.0f}% 점유 (여유 편당 {(gmax*1000-30)/2:.1f}mm)")
print()
print("일반적 안정 그립 기준: 물체폭 ≤ 개구의 ~70%")
print(f"  → 이 그리퍼 안정 그립 권장 최대 물체폭 ≈ {gmax*1000*0.7:.0f}mm")
