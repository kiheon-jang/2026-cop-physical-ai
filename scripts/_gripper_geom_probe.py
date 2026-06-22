"""그리퍼 기하 실측 — 실제 손가락 패드 위치/개폐축/접근축을 찾아 TCP 정의 근거 확보.

zero 팔자세 + 그리퍼 개폐 상태에서 콜리전 지오메트리 월드 AABB 중심을 본다.
- 고정 패드: 그리퍼 몸체 콜리전 geom
- 가동 패드: moving_jaw 콜리전 geom
TCP = 두 패드 내측면 중점(손가락 끝). 개폐축 = 두 패드를 잇는 벡터.
"""
import mujoco, numpy as np

m = mujoco.MjModel.from_xml_path("SO-ARM100/Simulation/SO101/scene_grasp.xml")
d = mujoco.MjData(m)
nid = lambda t, n: mujoco.mj_name2id(m, t, n)
GBID = nid(mujoco.mjtObj.mjOBJ_BODY, "gripper")
JBID = nid(mujoco.mjtObj.mjOBJ_BODY, "moving_jaw_so101_v1")
COL = [i for i in range(m.ngeom)
       if m.geom_bodyid[i] in (GBID, JBID) and m.geom_group[i] == 3]


def geom_world_center(dd, i):
    c_local = m.geom_aabb[i, :3]
    return dd.geom_xpos[i] + dd.geom_xmat[i].reshape(3, 3) @ c_local


def show(grip):
    d.ctrl[:5] = 0.0; d.ctrl[5] = grip
    mujoco.mj_forward(m, d)
    print(f"\n=== 그리퍼 ctrl={grip} (개={'열림' if grip>0 else '닫힘'}) ===")
    gx = d.xpos[GBID]; gR = d.xmat[GBID].reshape(3, 3)
    print(f"gripper body  pos={gx.round(4).tolist()}")
    print(f"  body x축(월드)={gR[:,0].round(3).tolist()}  y축={gR[:,1].round(3).tolist()}  z축={gR[:,2].round(3).tolist()}")
    centers = {}
    for i in COL:
        bn = m.body(m.geom_bodyid[i]).name
        c = geom_world_center(d, i)
        sz = m.geom_aabb[i, 3:]
        centers[i] = c
        # 월드 + 그리퍼 몸체 로컬좌표로도 표시
        c_in_body = gR.T @ (c - gx)
        print(f"  geom{i:>3} body={bn:<22} 월드중심={c.round(4).tolist()} 몸체로컬={c_in_body.round(4).tolist()} half={sz.round(4).tolist()}")
    return centers


c_open = show(1.5)
c_closed = show(-1.5)

# 고정 패드 후보 = 그리퍼 몸체 geom, 가동 패드 = moving_jaw geom
fixed = [i for i in COL if m.geom_bodyid[i] == GBID]
moving = [i for i in COL if m.geom_bodyid[i] == JBID]
print("\n고정측 콜리전 geom:", fixed, " 가동측:", moving)
if fixed and moving:
    # 가동 패드와 가장 가까운 고정 패드를 짝지어 그 중점을 TCP 후보로
    gx = d.xpos[GBID]; gR = d.xmat[GBID].reshape(3, 3)
    d.ctrl[:5] = 0; d.ctrl[5] = 1.5; mujoco.mj_forward(m, d)
    fpos = {i: geom_world_center(d, i) for i in fixed}
    mpos = {i: geom_world_center(d, i) for i in moving}
    for mi, mc in mpos.items():
        fi = min(fpos, key=lambda k: np.linalg.norm(fpos[k] - mc))
        mid = 0.5 * (mc + fpos[fi])
        mid_body = gR.T @ (mid - gx)
        opening_axis = (mc - fpos[fi]); opening_axis /= (np.linalg.norm(opening_axis) + 1e-9)
        print(f"\nTCP 후보 (movingGeom{mi} ↔ fixedGeom{fi}):")
        print(f"  월드={mid.round(4).tolist()}  그리퍼몸체로컬={mid_body.round(4).tolist()}")
        print(f"  개폐축(월드, 열림기준)={opening_axis.round(3).tolist()}  패드간격={np.linalg.norm(mc-fpos[fi])*1000:.1f}mm")
        print(f"  → 이 로컬좌표로 <site name='tcp' pos='...'> 를 gripper 바디에 추가하면 됨")
